#!/usr/bin/env python3
"""
Test script for the complete Motorcycle Image Cropping Demo
完全なバイク画像切り抜きデモのテストスクリプト
"""

import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        ('flask', 'Flask'),
        ('cv2', 'opencv-python-headless'),
        ('PIL', 'Pillow'),
        ('numpy', 'numpy')
    ]
    
    missing = []
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            missing.append(package_name)
            print(f"✗ {package_name}")
    
    # Check optional YOLO
    try:
        from ultralytics import YOLO
        print("✓ ultralytics (YOLO detection available)")
    except ImportError:
        print("⚠ ultralytics (YOLO detection not available - will use fallback)")
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True

def main():
    """Main test function"""
    print("Motorcycle Image Cropping Demo - Dependency Check")
    print("バイク画像切り抜きデモ - 依存関係チェック")
    print("=" * 50)
    
    if check_dependencies():
        print("\n✓ All required dependencies are installed!")
        print("✓ 必要な依存関係がすべてインストールされています！")
        print("\nYou can now run:")
        print("実行できます:")
        print("  python simple_app.py  (Full version / フル版)")
        print("  python demo.py        (Demo version / デモ版)")
    else:
        print("\n✗ Some dependencies are missing")
        print("✗ いくつかの依存関係が不足しています")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)