"""
Pexels API + FFmpeg による動画生成モジュール

Kling AI の代替として、無料の素材動画＋テキストオーバーレイで動画を作成する。
Pexels API キーは無料登録で取得可能: https://www.pexels.com/api/
"""
import os
import subprocess
import requests
from typing import List, Dict


PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
PEXELS_BASE_URL = "https://api.pexels.com/videos"

# 日本語対応フォント（環境変数で上書き可能）
FONT_PATH = os.environ.get(
    "FONT_PATH",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
)


def search_video(query: str, duration_min: int = 3, duration_max: int = 20) -> str:
    """
    Pexels で縦向き動画を検索し、ダウンロードURLを返す

    Args:
        query: 検索キーワード（英語推奨）
        duration_min: 最短秒数
        duration_max: 最長秒数

    Returns:
        動画ダウンロードURL
    """
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "orientation": "portrait",
        "size": "medium",
        "per_page": 10,
        "min_duration": duration_min,
        "max_duration": duration_max,
    }

    res = requests.get(f"{PEXELS_BASE_URL}/search", headers=headers, params=params, timeout=30)
    res.raise_for_status()
    videos = res.json().get("videos", [])

    # 見つからない場合は duration 条件を外して再検索
    if not videos:
        params.pop("min_duration", None)
        params.pop("max_duration", None)
        res = requests.get(f"{PEXELS_BASE_URL}/search", headers=headers, params=params, timeout=30)
        res.raise_for_status()
        videos = res.json().get("videos", [])

    if not videos:
        raise RuntimeError(f"Pexels: 動画が見つかりません: query={query}")

    # HD > SD の順で URL を選択
    video = videos[0]
    for vf in sorted(video["video_files"], key=lambda x: x.get("height", 0), reverse=True):
        if vf.get("quality") in ("hd", "sd") and vf.get("link"):
            return vf["link"]

    return video["video_files"][0]["link"]


def download_and_trim(url: str, output_path: str, duration: int) -> str:
    """
    動画をダウンロードして指定秒数にトリム・縦型にクロップする

    Args:
        url: 動画URL
        output_path: 保存先パス
        duration: 秒数

    Returns:
        output_path
    """
    tmp_path = output_path + ".raw.mp4"

    res = requests.get(url, stream=True, timeout=60)
    res.raise_for_status()
    with open(tmp_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

    # 縦型 (9:16) にリサイズ＋クロップ＋トリム
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", tmp_path,
            "-t", str(duration),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            output_path,
        ],
        check=True,
        capture_output=True,
    )
    os.remove(tmp_path)
    return output_path


def add_text_overlay(input_path: str, output_path: str, text: str, font_size: int = 44) -> str:
    """
    FFmpeg の drawtext フィルターでテキストオーバーレイを追加する

    テキストは画面下部に半透明の黒背景付きで表示する。

    Args:
        input_path: 入力動画パス
        output_path: 出力動画パス
        text: オーバーレイするテキスト（日本語可）
        font_size: フォントサイズ

    Returns:
        output_path
    """
    # drawtext 用に特殊文字をエスケープ
    safe_text = text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")

    font_option = f":fontfile={FONT_PATH}" if os.path.exists(FONT_PATH) else ""

    drawtext = (
        f"drawtext=text='{safe_text}'"
        f"{font_option}"
        f":fontsize={font_size}"
        f":fontcolor=white"
        f":x=(w-text_w)/2"
        f":y=h*0.72"
        f":box=1:boxcolor=black@0.65:boxborderw=12"
        f":line_spacing=6"
    )

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", drawtext,
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "copy",
            output_path,
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def generate_all_scenes(scenes: List[Dict], tmpdir: str) -> List[str]:
    """
    全シーンの動画を生成してローカルパスリストを返す

    Pexels で素材を検索し、ナレーションテキストをオーバーレイする。

    Args:
        scenes: スクリプトのシーンリスト
        tmpdir: 一時ディレクトリパス

    Returns:
        各シーンの動画パスリスト
    """
    scene_paths = []

    for i, scene in enumerate(scenes):
        print(f"[Pexels] シーン {i+1}/{len(scenes)} 生成中...")

        duration = min(scene.get("duration", 5), 15)
        query = scene.get("visual_description", scene.get("narration", "news"))[:80]

        raw_path = os.path.join(tmpdir, f"scene_{i:02d}_raw.mp4")
        final_path = os.path.join(tmpdir, f"scene_{i:02d}.mp4")

        # 素材検索 → ダウンロード → トリム
        url = search_video(query, duration_min=duration, duration_max=duration + 10)
        download_and_trim(url, raw_path, duration)

        # ナレーションテキストをオーバーレイ
        narration = scene.get("narration", "").strip()
        if narration:
            add_text_overlay(raw_path, final_path, narration)
            os.remove(raw_path)
        else:
            os.rename(raw_path, final_path)

        scene_paths.append(final_path)
        print(f"[Pexels] シーン {i+1} 完了")

    return scene_paths
