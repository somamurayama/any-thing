"""
YouTube Shorts 投稿モジュール
"""
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list,
) -> str:
    """
    YouTube Shorts に動画をアップロードする

    Returns:
        投稿された動画のURL
    """
    creds = Credentials(
        token=os.environ["YOUTUBE_ACCESS_TOKEN"],
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "25",  # News & Politics
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    response = request.execute()
    video_id = response["id"]
    return f"https://www.youtube.com/shorts/{video_id}"
