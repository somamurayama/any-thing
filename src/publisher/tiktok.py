"""
TikTok 投稿モジュール
"""
import os
import requests


TIKTOK_BASE_URL = "https://open.tiktokapis.com/v2"


def upload_to_tiktok(
    video_path: str,
    title: str,
    description: str,
) -> str:
    """
    TikTok に動画をアップロードする

    Returns:
        投稿ID
    """
    access_token = os.environ["TIKTOK_ACCESS_TOKEN"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. アップロードURL取得
    init_res = requests.post(
        f"{TIKTOK_BASE_URL}/post/publish/video/init/",
        headers=headers,
        json={
            "post_info": {
                "title": description[:150],
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": os.path.getsize(video_path),
                "chunk_size": os.path.getsize(video_path),
                "total_chunk_count": 1,
            },
        },
        timeout=30,
    )
    init_res.raise_for_status()
    upload_url = init_res.json()["data"]["upload_url"]
    publish_id = init_res.json()["data"]["publish_id"]

    # 2. 動画アップロード
    with open(video_path, "rb") as f:
        video_data = f.read()

    upload_res = requests.put(
        upload_url,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{len(video_data)-1}/{len(video_data)}",
        },
        data=video_data,
        timeout=120,
    )
    upload_res.raise_for_status()

    return publish_id
