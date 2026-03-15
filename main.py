"""
エントリーポイント

使い方:
  python main.py            # 生成から投稿まで一括（ローカル実行用）
  python main.py generate   # 動画生成のみ（output/ に保存）
  python main.py publish    # output/ の動画をSNS投稿
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pipeline import run_pipeline, generate_video, publish_video

OUTPUT_DIR = "output"

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    if command == "generate":
        generate_video(OUTPUT_DIR)
    elif command == "publish":
        publish_video(OUTPUT_DIR)
    else:
        run_pipeline()
