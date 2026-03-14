"""
Kling AI 動画生成モジュール
各シーンのプロンプトから動画を生成し、結合する
"""
import os
import time
import requests
from typing import List, Dict


KLING_API_KEY = os.environ.get("KLING_API_KEY", "")
KLING_BASE_URL = "https://api.klingai.com/v1"


def generate_scene_video(visual_prompt: str, duration: int = 5) -> str:
    """
    1シーン分の動画を生成する

    Args:
        visual_prompt: Kling AI への英語プロンプト
        duration: 動画の長さ（秒）5 or 10

    Returns:
        生成された動画のURL
    """
    headers = {
        "Authorization": f"Bearer {KLING_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "kling-v2-master",
        "prompt": visual_prompt,
        "negative_prompt": "blurry, low quality, watermark, text overlay",
        "cfg_scale": 0.5,
        "mode": "std",
        "aspect_ratio": "9:16",
        "duration": str(duration),
    }

    # 動画生成リクエスト
    res = requests.post(
        f"{KLING_BASE_URL}/videos/text2video",
        headers=headers,
        json=payload,
        timeout=30,
    )
    res.raise_for_status()
    data = res.json()
    task_id = data["data"]["task_id"]

    # 完了をポーリング（最大5分）
    return _wait_for_video(task_id, headers)


def _wait_for_video(task_id: str, headers: dict, max_wait: int = 300) -> str:
    """動画生成完了を待ってURLを返す"""
    elapsed = 0
    interval = 10

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval

        res = requests.get(
            f"{KLING_BASE_URL}/videos/text2video/{task_id}",
            headers=headers,
            timeout=30,
        )
        res.raise_for_status()
        data = res.json()
        status = data["data"]["task_status"]

        if status == "succeed":
            return data["data"]["task_result"]["videos"][0]["url"]
        elif status == "failed":
            raise RuntimeError(f"Kling AI 動画生成失敗: {data}")

    raise TimeoutError(f"Kling AI タイムアウト: task_id={task_id}")


def generate_all_scenes(scenes: List[Dict]) -> List[str]:
    """
    全シーンの動画を生成してURLリストを返す

    Args:
        scenes: スクリプトのシーンリスト

    Returns:
        各シーンの動画URLリスト
    """
    video_urls = []
    for i, scene in enumerate(scenes):
        print(f"[Kling] シーン {i+1}/{len(scenes)} 生成中...")
        url = generate_scene_video(
            visual_prompt=scene["visual_description"],
            duration=min(scene.get("duration", 5), 10),
        )
        video_urls.append(url)
        print(f"[Kling] シーン {i+1} 完了: {url}")

    return video_urls


def download_video(url: str, output_path: str) -> str:
    """動画をダウンロードしてローカルパスを返す"""
    res = requests.get(url, stream=True, timeout=60)
    res.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)
    return output_path
