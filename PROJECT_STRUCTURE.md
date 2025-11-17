# Project Structure / プロジェクト構造

## 📁 **Core Files / コアファイル**

### **Main Application / メインアプリケーション**
- `simple_app.py` - **Main Flask app with full motorcycle processing**
  - Complete 3-output processing pipeline
  - Japanese/English bilingual interface
  - All original Gradio script parameters
  - YOLO v8 motorcycle detection

### **Templates / テンプレート**
- `templates/simple_index.html` - **Main UI template**
  - Left panel: Controls + original image
  - Right panel: 3 output results
  - Click-to-enlarge image modal
  - Responsive design

### **Styling / スタイル**
- `static/style.css` - **Custom CSS**
  - Left-right split layout
  - Japanese font support
  - Hover effects and animations
  - Mobile responsive

## 🎯 **Utility Files / ユーティリティファイル**

### **Alternative Versions / 代替版**
- `demo.py` - **Lightweight demo version**
  - Minimal dependencies (Flask + PIL only)
  - Simple cropping functionality
  - Same bilingual interface

### **Setup & Testing / セットアップ・テスト**
- `test_app.py` - **Dependency checker**
- `start_demo.bat` - **Windows demo launcher**
- `requirements.txt` - **Python dependencies**

### **Documentation / ドキュメント**
- `README.md` - **Main project documentation**
- `QUICKSTART.md` - **Quick start guide**
- `PROJECT_STRUCTURE.md` - **This file**

## 🔧 **Configuration / 設定**

### **Git & IDE**
- `.gitignore` - **Git ignore rules**
  - Python cache files
  - YOLO model files (auto-downloaded)
  - IDE settings
  - OS temporary files

### **Model Files / モデルファイル**
- `yolov8m.pt` - **YOLO v8 model (auto-downloaded)**

## 🚀 **Usage / 使用方法**

### **Full Version / フル版**
```bash
python simple_app.py
```
- Complete motorcycle processing
- All 3 outputs (crop, scaled, floor-trimmed)
- All original parameters

### **Demo Version / デモ版**
```bash
python demo.py
```
- Lightweight processing
- Single output
- Minimal dependencies

### **Dependency Check / 依存関係チェック**
```bash
python test_app.py
```

## 📊 **Features / 機能**

### **Processing Outputs / 処理出力**
1. **Natural tight crop** / 自然なタイトクロップ
2. **Size-aware scaled output** / サイズ対応スケール出力
3. **Floor trimmed & top-filled** / 床トリム・上部塗りつぶし

### **Parameters / パラメータ**
- Motorcycle length (mm) / バイク長
- Base/reference length (mm) / ベース長
- Target canvas size (px) / キャンバスサイズ
- Padding (px) / パディング
- Fill method / 塗りつぶし方法
- Hard color / ハードカラー

### **UI Features / UI機能**
- Drag & drop upload / ドラッグ&ドロップ
- Click-to-enlarge images / クリックで拡大
- Language switching (EN/JA) / 言語切り替え
- Real-time parameter preview / リアルタイムプレビュー
- Download processed results / 結果ダウンロード

## 🌐 **Internationalization / 国際化**

- **English** - Default interface
- **Japanese (日本語)** - Complete translation
- Simple dictionary-based approach
- No external translation dependencies