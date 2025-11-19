# Motorcycle Image Cropping Demo / バイク画像切り抜きデモ

A simple web application for processing motorcycle images with automatic cropping and scaling, featuring Japanese internationalization support.

バイクの画像を自動的にクロップ・スケーリングするシンプルなWebアプリケーションです。日本語の国際化対応付き。

## Features / 機能

- **Automatic motorcycle detection** / 自動バイク検出
- **Smart cropping with padding** / パディング付きスマートクロップ
- **Size-aware scaling** / サイズ対応スケーリング
- **Japanese/English interface** / 日本語・英語インターフェース
- **Drag & drop upload** / ドラッグ&ドロップアップロード
- **Real-time preview** / リアルタイムプレビュー

## Installation / インストール

1. Install Python dependencies / Python依存関係をインストール:
```bash
pip install -r requirements.txt
```

2. Compile translations / 翻訳をコンパイル:
```bash
pybabel compile -d translations
```

3. Run the application / アプリケーションを実行:
```bash
python simple_app.py
```

4. Open your browser to / ブラウザで開く: `http://localhost:5000`

## Usage / 使用方法

1. **Upload Image** / 画像をアップロード: Click the upload area or drag & drop a motorcycle image
2. **Adjust Settings** / 設定を調整: Set motorcycle length and padding
3. **Process** / 処理: Click "Process Image" button
4. **Download** / ダウンロード: Save the processed result

## Language Support / 言語サポート

- **English**: Default interface language
- **Japanese (日本語)**: Full translation support

Switch languages using the buttons in the top-right corner.

右上のボタンで言語を切り替えできます。

## Technical Details / 技術詳細

- **Backend**: Flask with OpenCV and PIL
- **Frontend**: Bootstrap 5 with vanilla JavaScript
- **I18n**: Flask-Babel for internationalization
- **AI**: Optional YOLO v8 for motorcycle detection

## Requirements / 要件

- Python 3.8+
- OpenCV
- PIL/Pillow
- Flask
- Flask-Babel
- NumPy
- Ultralytics (optional, for YOLO detection)

## License / ライセンス

MIT License
