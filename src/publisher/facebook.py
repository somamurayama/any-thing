"""
Facebook Reels 投稿モジュール（Meta Graph API）
"""
import os
import requests


GRAPH_BASE = "https://graph.facebook.com/v19.0"


def upload_to_facebook(video_path: str, description: str) -> str:
    """
    Facebook ページに動画（Reels）を投稿する

    Returns:
        投稿URL
    """
    access_token = os.environ["FACEBOOK_ACCESS_TOKEN"]
    page_id = os.environ["FACEBOOK_PAGE_ID"]

    file_size = os.path.getsize(video_path)

    # 1. アップロードセッション開始
    start_res = requests.post(
        f"{GRAPH_BASE}/{page_id}/video_reels",
        params={"access_token": access_token},
        json={
            "upload_phase": "start",
            "file_size": file_size,
        },
        timeout=30,
    )
    start_res.raise_for_status()
    video_id = start_res.json()["video_id"]
    upload_url = start_res.json()["upload_url"]

    # 2. 動画アップロード
    with open(video_path, "rb") as f:
        upload_res = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {access_token}",
                "offset": "0",
                "file_size": str(file_size),
            },
            files={"video_file_chunk": f},
            timeout=120,
        )
    upload_res.raise_for_status()

    # 3. 公開
    finish_res = requests.post(
        f"{GRAPH_BASE}/{page_id}/video_reels",
        params={"access_token": access_token},
        json={
            "video_id": video_id,
            "upload_phase": "finish",
            "video_state": "PUBLISHED",
            "description": description[:2200],
        },
        timeout=30,
    )
    finish_res.raise_for_status()

    return f"https://www.facebook.com/{page_id}/videos/{video_id}"
