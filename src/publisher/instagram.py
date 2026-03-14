"""
Instagram Reels 投稿モジュール（Meta Graph API）
"""
import os
import requests


GRAPH_BASE = "https://graph.facebook.com/v19.0"


def upload_to_instagram(
    video_url: str,
    caption: str,
) -> str:
    """
    Instagram Reels に動画を投稿する
    ※ video_url はパブリックにアクセス可能なURLである必要がある

    Returns:
        投稿のURL
    """
    access_token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    ig_user_id = os.environ["INSTAGRAM_USER_ID"]

    # 1. メディアコンテナ作成
    container_res = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media",
        params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption[:2200],
            "access_token": access_token,
        },
        timeout=30,
    )
    container_res.raise_for_status()
    container_id = container_res.json()["id"]

    # 2. アップロード完了待ち
    import time
    for _ in range(30):
        time.sleep(10)
        status_res = requests.get(
            f"{GRAPH_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": access_token},
            timeout=30,
        )
        if status_res.json().get("status_code") == "FINISHED":
            break

    # 3. 公開
    publish_res = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media_publish",
        params={"creation_id": container_id, "access_token": access_token},
        timeout=30,
    )
    publish_res.raise_for_status()
    media_id = publish_res.json()["id"]

    return f"https://www.instagram.com/p/{media_id}/"
