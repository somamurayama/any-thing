"""
X (Twitter) 動画投稿モジュール
"""
import os
import requests
from requests_oauthlib import OAuth1


def _get_auth():
    return OAuth1(
        os.environ["TWITTER_API_KEY"],
        os.environ["TWITTER_API_SECRET"],
        os.environ["TWITTER_ACCESS_TOKEN"],
        os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )


def upload_to_twitter(video_path: str, text: str) -> str:
    """
    X (Twitter) に動画を投稿する

    Returns:
        投稿URL
    """
    auth = _get_auth()
    file_size = os.path.getsize(video_path)

    # 1. アップロード初期化
    init_res = requests.post(
        "https://upload.twitter.com/1.1/media/upload.json",
        auth=auth,
        data={
            "command": "INIT",
            "total_bytes": file_size,
            "media_type": "video/mp4",
            "media_category": "tweet_video",
        },
        timeout=30,
    )
    init_res.raise_for_status()
    media_id = init_res.json()["media_id_string"]

    # 2. チャンクアップロード（5MBずつ）
    chunk_size = 5 * 1024 * 1024
    with open(video_path, "rb") as f:
        segment = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            requests.post(
                "https://upload.twitter.com/1.1/media/upload.json",
                auth=auth,
                data={"command": "APPEND", "media_id": media_id, "segment_index": segment},
                files={"media": chunk},
                timeout=60,
            ).raise_for_status()
            segment += 1

    # 3. ファイナライズ
    requests.post(
        "https://upload.twitter.com/1.1/media/upload.json",
        auth=auth,
        data={"command": "FINALIZE", "media_id": media_id},
        timeout=30,
    ).raise_for_status()

    # 4. ツイート投稿
    tweet_res = requests.post(
        "https://api.twitter.com/2/tweets",
        auth=auth,
        json={"text": text[:280], "media": {"media_ids": [media_id]}},
        timeout=30,
    )
    tweet_res.raise_for_status()
    tweet_id = tweet_res.json()["data"]["id"]
    return f"https://twitter.com/i/status/{tweet_id}"
