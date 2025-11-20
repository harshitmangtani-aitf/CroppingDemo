import os
import cv2
import numpy as np
from PIL import Image
from flask import Flask, render_template, request, jsonify, session
import io
import base64
import math

# Optional YOLO (auto-download if model name used)
try:
    from ultralytics import YOLO
    MODEL = YOLO("yolov8m")  # change to "yolov8n" or "yolov8s" if you want faster but less accurate detection
except Exception:
    MODEL = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Simple translation dictionary
TRANSLATIONS = {
    'en': {
        'title': 'Motorcycle Image Cropping Demo',
        'upload_text': 'Upload a motorcycle image to automatically crop and process it',
        'click_upload': 'Click to upload or drag and drop',
        'supported_formats': 'Supported formats: JPG, PNG, GIF',
        'bike_length': 'Estimated motorcycle length (mm)',
        'padding': 'Padding (px) around tight crop (used for other UI options)',
        'fill_method': 'Fill method for top (Output 3)',
        'hard_color': 'Hard color hex (used for solid_color)',
        'process_image': 'Process Image',
        'processing': 'Processing...',
        'original_image': 'Original Image',
        'output1': 'Natural tight crop',
        'output2': 'Size-aware scaled output (bottom-centered on original-size canvas)',
        'output3': 'Original width, floor trimmed & top-filled',
        'download_result': 'Download Result',
        'no_image_uploaded': 'No image uploaded',
        'no_image_selected': 'No image selected',
        'invalid_format': 'Invalid image format',
        'processing_failed': 'Failed to process image',
        'success_message': 'Image processed successfully',
        'network_error': 'Network error occurred'
    },
    'ja': {
        'title': 'バイク画像切り抜きデモ',
        'upload_text': 'バイクの画像をアップロードして自動的にクロップ・処理します',
        'click_upload': 'クリックしてアップロードまたはドラッグ&ドロップ',
        'supported_formats': '対応形式：JPG、PNG、GIF',
        'bike_length': '推定バイク長（mm）',
        'padding': 'タイトクロップ周りのパディング（px）（その他のUIオプションで使用）',
        'fill_method': '上部の塗りつぶし方法（出力3）',
        'hard_color': 'ハードカラー16進数（solid_colorで使用）',
        'process_image': '画像を処理',
        'processing': '処理中...',
        'original_image': '元の画像',
        'output1': '自然なタイトクロップ',
        'output2': 'サイズ対応スケール出力（元サイズキャンバス下部中央配置）',
        'output3': '元幅、床トリム・上部塗りつぶし',
        'download_result': '結果をダウンロード',
        'no_image_uploaded': '画像がアップロードされていません',
        'no_image_selected': '画像が選択されていません',
        'invalid_format': '無効な画像形式です',
        'processing_failed': '画像の処理に失敗しました',
        'success_message': '画像の処理が完了しました',
        'network_error': 'ネットワークエラーが発生しました'
    }
}

def get_text(key, lang='en'):
    """Simple translation function"""
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

# ---------------- parameters for optimization ----------------
MAX_PROC_SIDE = 1280        # max side for downscale during detection/mask
GRABCUT_ITERS = 3           # lower iterations for speed (quality tradeoff small)
MORPH_KERNEL = (3, 3)
DILATE_KERNEL = (3, 3)
BLUR_KERNEL_LARGE = (31, 31)
BLUR_KERNEL_MED = (21, 21)

# --- FIXED REFERENCE LENGTH ---
BASE_LENGTH_MM = 1620  # fixed; removed from UI

# ---------------- detection / mask helpers ----------------
def resize_for_processing(img_rgb, max_side=MAX_PROC_SIDE):
    H, W = img_rgb.shape[:2]
    max_dim = max(H, W)
    if max_dim <= max_side:
        return img_rgb.copy(), 1.0
    scale = max_side / float(max_dim)
    new_w = int(round(W * scale))
    new_h = int(round(H * scale))
    small = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    return small, scale

def detect_bbox(img_bgr):
    H, W = img_bgr.shape[:2]
    # YOLO preferred
    if MODEL is not None:
        try:
            res = MODEL(img_bgr)
            boxes = res[0].boxes
            if len(boxes):
                best = None; best_conf = -1.0
                for b in boxes:
                    conf = float(b.conf[0])
                    try:
                        cls = int(b.cls[0])
                    except Exception:
                        cls = None
                    if cls == 3 and conf > best_conf:
                        best = b; best_conf = conf
                if best is None:
                    best = boxes[np.argmax(boxes.conf)]
                x1, y1, x2, y2 = map(int, best.xyxy[0])
                return (max(0, x1), max(0, y1), min(W - 1, x2), min(H - 1, y2))
        except Exception:
            pass
    
    # fallback: choose contour by bbox area (robust)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    edges = cv2.Canny(blur, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    best_bb = None; best_area = 0
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w < 30 or h < 30:
            continue
        area = w * h
        if area > best_area:
            best_area = area; best_bb = (x, y, w, h)
    if best_bb is None:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
    else:
        x, y, w, h = best_bb
    pad = int(0.05 * max(w, h))
    x1 = max(0, x - pad); y1 = max(0, y - pad)
    x2 = min(W - 1, x + w + pad); y2 = min(H - 1, y + h + pad)
    if (x2 - x1) < 40 or (y2 - y1) < 40:
        return None
    return (x1, y1, x2, y2)

def grabcut_full_image(img_bgr, rect):
    H, W = img_bgr.shape[:2]
    mask = np.zeros((H, W), np.uint8)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    x, y, w, h = rect
    # clamp rect
    x = max(0, min(int(x), W - 2)); y = max(0, min(int(y), H - 2))
    w = max(2, min(int(w), W - x - 1)); h = max(2, min(int(h), H - y - 1))
    try:
        cv2.grabCut(img_bgr, mask, (x, y, w, h), bgd, fgd, GRABCUT_ITERS, cv2.GC_INIT_WITH_RECT)
        mask2 = np.where((mask == 2) | (mask == 0), 0, 255).astype('uint8')
    except Exception:
        mask2 = np.zeros((H, W), dtype=np.uint8)
        mask2[y:y + h, x:x + w] = 255
    # cleanup (lighter kernels)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, MORPH_KERNEL)
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel, iterations=1)
    mask2 = cv2.dilate(mask2, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, DILATE_KERNEL), iterations=1)
    return mask2

# ---------------- core pipeline (single-grabcut, scaled processing) ----------------
def compute_single_mask_and_crops(original_rgb, ui_padding):
    """Run detection+grabcut once at downscaled resolution (padding=5), map results back.
    Returns:
    mask_orig (HxW uint8 mask in original coords),
    crop_coords_5 (xmin,ymin,xmax,ymax) in original coords (padding=5)
    pil_crop_ui (RGB PIL) -> crop using UI padding (expanded from padding=5)
    bike_px_w_ui (int) width (px) of UI crop (used for scaling)
    pil_crop_5 (RGB PIL) -> crop using padding=5 (used for top-trim mask & maybe preview)
    """
    H_orig, W_orig = original_rgb.shape[:2]
    # downscale for faster detection/mask
    proc_img, scale = resize_for_processing(original_rgb, MAX_PROC_SIDE)
    proc_bgr = cv2.cvtColor(proc_img, cv2.COLOR_RGB2BGR)
    bbox_proc = detect_bbox(proc_bgr)
    if bbox_proc is None:
        # nothing detected -> return defaults
        mask_full_orig = np.zeros((H_orig, W_orig), dtype=np.uint8)
        return mask_full_orig, (0, 0, W_orig - 1, H_orig - 1), Image.fromarray(original_rgb), None, Image.fromarray(original_rgb)
    x1p, y1p, x2p, y2p = bbox_proc
    rect_proc = (x1p, y1p, x2p - x1p, y2p - y1p)
    mask_proc = grabcut_full_image(proc_bgr, rect_proc)  # mask at proc resolution
    # map mask_proc back to original resolution (nearest)
    mask_orig = cv2.resize(mask_proc, (W_orig, H_orig), interpolation=cv2.INTER_NEAREST)
    ys, xs = np.where(mask_orig == 255)
    if ys.size == 0 or xs.size == 0:
        # fallback: use bbox scaled to original
        x1o = int(round(x1p / scale)); y1o = int(round(y1p / scale))
        x2o = int(round(x2p / scale)); y2o = int(round(y2p / scale))
        crop_coords_5 = (x1o, y1o, x2o, y2o)
    else:
        ymin_o, ymax_o = int(ys.min()), int(ys.max())
        xmin_o, xmax_o = int(xs.min()), int(xs.max())
        # padding=5 fixed for mask-based crop
        crop_coords_5 = (max(0, xmin_o - 5), max(0, ymin_o - 5), min(W_orig - 1, xmax_o + 5), min(H_orig - 1, ymax_o + 5))
    # Build pil_crop_5
    xmin5, ymin5, xmax5, ymax5 = crop_coords_5
    crop5 = original_rgb[ymin5:ymax5 + 1, xmin5:xmax5 + 1]
    pil_crop_5 = Image.fromarray(crop5)
    # Derive UI crop by expanding crop_coords_5 to requested ui_padding (without rerunning GrabCut)
    ui_pad = max(0, int(round(ui_padding)))
    if ui_pad <= 5:
        pil_crop_ui = pil_crop_5
        bike_px_w_ui = (xmax5 - xmin5 + 1)
    else:
        extra = ui_pad - 5
        xmin_ui = max(0, xmin5 - extra); ymin_ui = max(0, ymin5 - extra)
        xmax_ui = min(W_orig - 1, xmax5 + extra); ymax_ui = min(H_orig - 1, ymax5 + extra)
        crop_ui = original_rgb[ymin_ui:ymax_ui + 1, xmin_ui:xmax_ui + 1]
        pil_crop_ui = Image.fromarray(crop_ui)
        bike_px_w_ui = (xmax_ui - xmin_ui + 1)
    return mask_orig, crop_coords_5, pil_crop_ui, bike_px_w_ui, pil_crop_5

# ---------------- scaling onto original-size canvas (bottom-centered) ----------------
def scale_center_on_canvas(pil_rgb, bike_pixel_width, bike_length_mm, base_length_mm=BASE_LENGTH_MM, canvas_size=None, ref_frac=0.6):
    if pil_rgb is None:
        return None
    if canvas_size is None:
        canvas_w, canvas_h = 512, 512
    else:
        canvas_w, canvas_h = int(canvas_size[0]), int(canvas_size[1])
    if canvas_w <= 0 or canvas_h <= 0:
        canvas_w, canvas_h = 512, 512
    
    w, h = pil_rgb.size
    if bike_pixel_width is None or bike_pixel_width == 0:
        scale = min(canvas_w / max(1, w), canvas_h / max(1, h), 1.0)
        new_w = max(1, int(round(w * scale))); new_h = max(1, int(round(h * scale)))
        resized = pil_rgb.resize((new_w, new_h), resample=Image.LANCZOS)
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
        left = (canvas_w - new_w) // 2
        top = canvas_h - new_h
        if top < 0:
            top = 0
        canvas.paste(resized.convert("RGBA"), (left, top), resized.convert("RGBA"))
        return canvas
    
    try:
        scale_real = float(bike_length_mm) / float(base_length_mm) if (bike_length_mm and base_length_mm) else 1.0
    except Exception:
        scale_real = 1.0
    
    desired_bike_px = int(canvas_w * ref_frac * scale_real)
    desired_bike_px = max(1, desired_bike_px)
    ratio = desired_bike_px / float(bike_pixel_width)
    new_w = max(1, int(round(w * ratio))); new_h = max(1, int(round(h * ratio)))
    
    # Ensure it fits within canvas
    if new_w > canvas_w or new_h > canvas_h:
        scale_fit = min(canvas_w / new_w, canvas_h / new_h)
        new_w = max(1, int(round(new_w * scale_fit))); new_h = max(1, int(round(new_h * scale_fit)))
    
    resized = pil_rgb.resize((new_w, new_h), resample=Image.LANCZOS)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    left = (canvas_w - new_w) // 2
    top = canvas_h - new_h
    if top < 0:
        top = 0
    canvas.paste(resized.convert("RGBA"), (left, top), resized.convert("RGBA"))
    return canvas

# ---------------- top-fill utilities (lighter blur kernels) ----------------
def heuristic_blur_fill(top_src_rgb, width, height):
    if top_src_rgb is None or top_src_rgb.size == 0:
        return np.ones((height, width, 3), dtype=np.uint8) * 200
    scaled = cv2.resize(top_src_rgb, (width, max(1, int(height * 0.9))), interpolation=cv2.INTER_LINEAR)
    if scaled.shape[0] < height:
        extra = height - scaled.shape[0]
        pad_block = np.tile(scaled[-1:, :, :], (extra, 1, 1))
        scaled = np.vstack([pad_block, scaled])[-height:, :, :]
    filled = cv2.GaussianBlur(scaled, BLUR_KERNEL_LARGE, 0)
    return filled[:height, :, :]

def mirror_fill(top_src_rgb, width, height):
    if top_src_rgb is None or top_src_rgb.size == 0:
        return np.ones((height, width, 3), dtype=np.uint8) * 200
    scaled = cv2.resize(top_src_rgb, (width, top_src_rgb.shape[0]), interpolation=cv2.INTER_LINEAR)
    times = int(np.ceil(height / scaled.shape[0])) + 1
    tiled = np.vstack([scaled[::-1] if i % 2 else scaled for i in range(times)])
    result = tiled[:height, :width, :]
    result = cv2.GaussianBlur(result, BLUR_KERNEL_MED, 0)
    return result

def trim_floor_and_fill_top(original_rgb, crop_mask, crop_coords, fill_method='heuristic_blur', hard_color=(255,255,255), padding=5):
    """Uses mask (crop_mask) and crop_coords (from padding=5 run) to trim floor
    and fill the same amount of pixels at the top.
    Adds bottom padding=5 to mask bottom for stability."""
    H, W = original_rgb.shape[:2]
    xmin, ymin, xmax, ymax = crop_coords
    # safety
    if crop_mask is None:
        return Image.fromarray(original_rgb)
    # find bottom of mask inside crop-local coords
    ys, xs = np.where(crop_mask == 255)
    if ys.size == 0:
        return Image.fromarray(original_rgb)
    # mask bottom in crop-local coords
    local_ymax = int(ys.max())
    # ---------- APPLY PADDING = 5 HERE ----------
    local_ymax_padded = local_ymax + padding
    # clamp to crop height
    local_ymax_padded = min(local_ymax_padded, crop_mask.shape[0] - 1)
    # --------------------------------------------
    # convert to global coordinate
    mask_bottom_global = ymin + local_ymax_padded
    # compute how much to trim from the bottom
    trim_pixels = max(0, H - 1 - mask_bottom_global)
    if trim_pixels == 0:
        return Image.fromarray(original_rgb)
    # remove bottom rows
    trimmed = original_rgb[0:H - trim_pixels, :, :].copy()  # (H-trim, W, 3)
    # generate fill area (height = trim_pixels)
    if fill_method == 'solid_color':
        fill = np.ones((trim_pixels, W, 3), dtype=np.uint8) * np.array(hard_color, dtype=np.uint8)
    elif fill_method == 'mirror':
        top_h = min(max(10, trim_pixels // 4), H // 4)
        top_src = original_rgb[0:top_h, :, :]
        fill = mirror_fill(top_src, W, trim_pixels)
    else:  # heuristic_blur (default)
        top_h = min(max(10, trim_pixels // 4), H // 6)
        top_src = original_rgb[0:top_h, :, :]
        fill = heuristic_blur_fill(top_src, W, trim_pixels)
    # stack fill on top of trimmed
    out = np.vstack([fill, trimmed])
    # final height correction
    if out.shape[0] != H:
        if out.shape[0] > H:
            out = out[out.shape[0] - H:, :, :]
        else:
            pad_top = H - out.shape[0]
            pad_block = np.ones((pad_top, W, 3), dtype=np.uint8) * 255
            out = np.vstack([pad_block, out])
    return Image.fromarray(out.astype(np.uint8))

# ---------------- main processing handler ----------------
def process_motorcycle_image(uploaded_img, bike_length_mm=2200.0, padding=5, fill_method="heuristic_blur", hard_color_hex="#FFFFFF"):
    """Returns:
    - Natural tight crop (PIL RGB) using UI padding (derived from single mask run)
    - Size-aware scaled output (PIL RGB) - bottom-centered on original-size canvas
    - Original-size image with floor trimmed & top filled (mask produced with padding=5)
    """
    if uploaded_img is None:
        return None, None, None
    try:
        hard_color = tuple(int(hard_color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        hard_color = (255, 255, 255)
    
    original_rgb = uploaded_img.copy()
    H_orig, W_orig = original_rgb.shape[:2]
    
    # Single detection+grabcut (mask/crop_coords use padding=5 internally).
    # We pass ui_padding=padding so Output 1 respects user padding.
    mask_orig, crop_coords_5, pil_crop_ui, bike_px_w_ui, pil_crop_5 = compute_single_mask_and_crops(original_rgb, ui_padding=padding)
    
    # Output 1: tight crop using dynamic user padding
    out1 = pil_crop_ui
    
    # Prepare values from padding=5 crop
    xmin5, ymin5, xmax5, ymax5 = crop_coords_5
    w_crop5, h_crop5 = pil_crop_5.size
    bike_px_w_5 = (xmax5 - xmin5 + 1) if (xmax5 > xmin5) else None
    
    # Canvas size = original image size
    canvas_w, canvas_h = W_orig, H_orig
    ref_frac = 0.6
    
    # If we don't have a valid bike pixel width, fall back to previous canvas behavior
    if bike_px_w_5 is None or bike_px_w_5 == 0:
        out2 = scale_center_on_canvas(pil_crop_5, bike_px_w_5, bike_length_mm, base_length_mm=BASE_LENGTH_MM, canvas_size=(canvas_w, canvas_h), ref_frac=ref_frac)
    else:
        # 1) compute desired bike px (same formula as scale_center_on_canvas)
        try:
            scale_real = float(bike_length_mm) / float(BASE_LENGTH_MM) if (bike_length_mm and BASE_LENGTH_MM) else 1.0
        except Exception:
            scale_real = 1.0
        desired_bike_px = int(canvas_w * ref_frac * scale_real)
        desired_bike_px = max(1, desired_bike_px)
        
        # 2) ratio to resize crop5 -> new_w,new_h
        ratio = desired_bike_px / float(bike_px_w_5)
        new_w = max(1, int(round(w_crop5 * ratio)))
        new_h = max(1, int(round(h_crop5 * ratio)))
        
        # 3) ensure resized fits canvas (same clamp as before). If clamped, update ratio.
        if new_w > canvas_w or new_h > canvas_h:
            scale_fit = min(canvas_w / new_w, canvas_h / new_h)
            new_w = max(1, int(round(new_w * scale_fit)))
            new_h = max(1, int(round(new_h * scale_fit)))
            ratio = ratio * scale_fit
        
        # 4) compute paste position used by Output 2 (bottom-centered)
        left = (canvas_w - new_w) // 2
        top = canvas_h - new_h
        if top < 0:
            top = 0
        
        # 5) SCALE ENTIRE ORIGINAL by same ratio so bike has same pixel size
        scaled_W = max(1, int(round(W_orig * ratio)))
        scaled_H = max(1, int(round(H_orig * ratio)))
        # cv2 expects (width, height)
        scaled_orig = cv2.resize(original_rgb, (scaled_W, scaled_H), interpolation=cv2.INTER_LINEAR)
        
        # 6) compute window in scaled_orig so bike ends up at (left, top) in final canvas:
        # bike's top-left in scaled original:
        bike_x_scaled = int(round(xmin5 * ratio))
        bike_y_scaled = int(round(ymin5 * ratio))
        # we want bike_x_scaled -> left, bike_y_scaled -> top  => crop origin:
        crop_x = bike_x_scaled - left
        crop_y = bike_y_scaled - top
        
        # 7) extract canvas_w x canvas_h window from scaled_orig, with white padding if out-of-bounds
        out_arr = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255  # white background
        src_x0 = max(0, crop_x)
        src_y0 = max(0, crop_y)
        src_x1 = min(scaled_W, crop_x + canvas_w)
        src_y1 = min(scaled_H, crop_y + canvas_h)
        dst_x0 = src_x0 - crop_x
        dst_y0 = src_y0 - crop_y
        dst_x1 = dst_x0 + (src_x1 - src_x0)
        dst_y1 = dst_y0 + (src_y1 - src_y0)
        
        if src_x1 > src_x0 and src_y1 > src_y0:
            out_arr[dst_y0:dst_y1, dst_x0:dst_x1] = scaled_orig[src_y0:src_y1, src_x0:src_x1]
        
        out2 = Image.fromarray(out_arr)
    
    # Output 3: trim floor & fill top (uses default padding=5 inside function)
    if mask_orig is None or mask_orig.size == 0:
        crop_mask5 = None
    else:
        crop_mask5 = mask_orig[ymin5:ymax5 + 1, xmin5:xmax5 + 1]
    out3 = trim_floor_and_fill_top(original_rgb, crop_mask5, crop_coords_5, fill_method=fill_method, hard_color=hard_color)
    return out1, out2, out3

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    return render_template('simple_index.html', lang=lang, get_text=get_text)

@app.route('/process', methods=['POST'])
def process():
    lang = request.args.get('lang', 'en')
    
    try:
        if 'image' not in request.files:
            return jsonify({'error': get_text('no_image_uploaded', lang)})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': get_text('no_image_selected', lang)})
        
        # Read image
        img_bytes = file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': get_text('invalid_format', lang)})
        
        # Convert BGR to RGB
        original_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Get parameters
        bike_length_mm = float(request.form.get('bike_length', 2200))
        padding = int(request.form.get('padding', 5))
        fill_method = request.form.get('fill_method', 'heuristic_blur')
        hard_color_hex = request.form.get('hard_color', '#FFFFFF')
        
        # Process image - get all 3 outputs
        out1, out2, out3 = process_motorcycle_image(
            original_rgb, bike_length_mm, padding, fill_method, hard_color_hex
        )
        
        if out1 is None:
            return jsonify({'error': get_text('processing_failed', lang)})
        
        # Convert all outputs to base64
        def pil_to_base64(pil_img):
            if pil_img is None:
                return None
            buffer = io.BytesIO()
            # Convert RGBA to RGB if needed
            if pil_img.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', pil_img.size, (255, 255, 255))
                background.paste(pil_img, mask=pil_img.split()[-1])  # Use alpha channel as mask
                pil_img = background
            pil_img.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
        
        output1_b64 = pil_to_base64(out1)
        output2_b64 = pil_to_base64(out2)
        output3_b64 = pil_to_base64(out3)
        
        return jsonify({
            'success': True,
            'output1': f'data:image/png;base64,{output1_b64}' if output1_b64 else None,
            'output2': f'data:image/png;base64,{output2_b64}' if output2_b64 else None,
            'output3': f'data:image/png;base64,{output3_b64}' if output3_b64 else None,
            'message': get_text('success_message', lang)
        })
        
    except Exception as e:
        return jsonify({'error': f"{get_text('processing_failed', lang)}: {str(e)}"})

if __name__ == '__main__':
    print("Motorcycle Image Cropping Demo / バイク画像切り抜きデモ")
    print("=" * 50)
    print("Starting server... / サーバーを開始中...")
    print("Open your browser to: http://localhost:5000")
    print("ブラウザで開く: http://localhost:5000")
    print("\nPress Ctrl+C to stop / 停止するにはCtrl+Cを押してください")
    app.run(debug=True, host='0.0.0.0', port=5000)