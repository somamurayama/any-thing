"""
エントリーポイント
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline()
