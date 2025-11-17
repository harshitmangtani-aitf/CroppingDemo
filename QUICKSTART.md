# Quick Start Guide / クイックスタートガイド

## 🚀 Quick Start

### 1. Check Dependencies / 依存関係チェック
```bash
python test_app.py
```

### 2. Run Full Version (Recommended) / フル版を実行（推奨）
```bash
python simple_app.py
```

### 3. Run Demo Version / デモ版を実行
```bash
python demo.py
# Or on Windows: double-click start_demo.bat
```

### 4. Open Browser / ブラウザで開く
```
http://localhost:5000
```

## 📦 Install Dependencies / 依存関係をインストール

If missing packages / パッケージが不足している場合:

```bash
pip install -r requirements.txt
```

## Features / 機能

### Full Mode (simple_app.py) / フルモード
- ✅ **3 Output Types** / 3つの出力タイプ:
  - Natural tight crop / 自然なタイトクロップ
  - Size-aware scaled output / サイズ対応スケール出力  
  - Floor trimmed & top-filled / 床トリム・上部塗りつぶし
- ✅ **All Original Parameters** / 元のパラメータすべて:
  - Motorcycle length (mm) / バイク長（mm）
  - Base/reference length / ベース/参照長
  - Target canvas size / ターゲットキャンバスサイズ
  - Padding control / パディング制御
  - Fill methods (heuristic_blur, mirror, solid_color) / 塗りつぶし方法
  - Hard color picker / ハードカラーピッカー
- ✅ AI-powered motorcycle detection / AI搭載バイク検出
- ✅ YOLO v8 integration / YOLO v8統合
- ✅ Single GrabCut optimization / 単一GrabCut最適化
- ✅ Japanese/English UI / 日本語・英語UI

### Demo Mode (demo.py) / デモモード  
- ✅ Basic image upload / 基本的な画像アップロード
- ✅ Simple cropping / シンプルなクロップ
- ✅ Japanese/English UI / 日本語・英語UI
- ✅ Minimal dependencies / 最小限の依存関係

## Language Switching / 言語切り替え

Click the language buttons in the top-right corner:
- **English** - English interface
- **日本語** - Japanese interface

右上の言語ボタンをクリック:
- **English** - 英語インターフェース  
- **日本語** - 日本語インターフェース

## Troubleshooting / トラブルシューティング

### Common Issues / よくある問題

1. **Port already in use / ポートが使用中**
   ```
   Error: Address already in use
   ```
   Solution: Change port in demo.py or kill existing process

2. **Missing PIL / PILがない**
   ```bash
   pip install Pillow
   ```

3. **Permission errors / 権限エラー**
   - Run as administrator on Windows
   - Use `sudo` on Mac/Linux if needed

### Support / サポート

For issues, check the console output for error messages.
問題がある場合は、コンソール出力でエラーメッセージを確認してください。