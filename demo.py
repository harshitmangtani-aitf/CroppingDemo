#!/usr/bin/env python3
"""
Demo version of the Motorcycle Image Cropping Demo with minimal dependencies
バイク画像切り抜きデモのデモ版（最小限の依存関係）
"""

import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, jsonify
from flask_babel import Babel, gettext

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-secret-key'
app.config['LANGUAGES'] = {
    'en': 'English',
    'ja': '日本語'
}

babel = Babel()
babel.init_app(app)

@babel.localeselector
def get_locale():
    return request.args.get('lang', 'en')

def simple_crop_demo(img, padding=5):
    """
    Simple demo cropping function that just adds a border
    実際のYOLO/OpenCVの代わりのシンプルなデモクロップ機能
    """
    try:
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get image dimensions
        width, height = img.size
        
        # Simple center crop with padding
        crop_size = min(width, height) - (padding * 4)
        if crop_size <= 0:
            return img
        
        left = (width - crop_size) // 2
        top = (height - crop_size) // 2
        right = left + crop_size
        bottom = top + crop_size
        
        # Crop the image
        cropped = img.crop((left, top, right, bottom))
        
        # Add a simple border to show processing
        draw = ImageDraw.Draw(cropped)
        draw.rectangle([0, 0, crop_size-1, crop_size-1], outline='red', width=3)
        
        return cropped
        
    except Exception as e:
        print(f"Error in demo processing: {e}")
        return img

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        if 'image' not in request.files:
            return jsonify({'error': gettext('No image uploaded')})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': gettext('No image selected')})
        
        # Read image with PIL
        try:
            img = Image.open(file.stream)
        except Exception:
            return jsonify({'error': gettext('Invalid image format')})
        
        # Get parameters
        padding = int(request.form.get('padding', 5))
        
        # Process image (demo version)
        result = simple_crop_demo(img, padding)
        
        if result is None:
            return jsonify({'error': gettext('Failed to process image')})
        
        # Convert to base64 for response
        buffer = io.BytesIO()
        result.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_str}',
            'message': gettext('Image processed successfully') + ' (Demo Mode / デモモード)'
        })
        
    except Exception as e:
        return jsonify({'error': gettext('Processing failed: %(error)s', error=str(e))})

if __name__ == '__main__':
    print("Demo Mode - Motorcycle Image Cropping Demo")
    print("デモモード - バイク画像切り抜きデモ")
    print("=" * 50)
    print("This is a demo version with simplified processing.")
    print("これは簡略化された処理のデモ版です。")
    print("\nOpen your browser to: http://localhost:5000")
    print("ブラウザで開く: http://localhost:5000")
    print("\nPress Ctrl+C to stop / 停止するにはCtrl+Cを押してください")
    
    app.run(debug=True, host='0.0.0.0', port=5000)