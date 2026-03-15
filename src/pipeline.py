"""
メインパイプライン
ニュース収集 → スクリプト生成 → 動画生成 → SNS一括投稿
"""
import os
import json
import tempfile
from datetime import datetime
from typing import List

from research.news_fetcher import fetch_news, rank_articles
from summarizer.script_generator import generate_script, generate_thumbnail_prompt
from video.pexels_client import generate_all_scenes
from publisher.youtube import upload_to_youtube
from publisher.tiktok import upload_to_tiktok
from publisher.instagram import upload_to_instagram
from publisher.twitter import upload_to_twitter
from publisher.facebook import upload_to_facebook


# 有効にするSNSを環境変数で制御
ENABLED_PLATFORMS = {
    "youtube": bool(os.environ.get("YOUTUBE_ACCESS_TOKEN")),
    "tiktok": bool(os.environ.get("TIKTOK_ACCESS_TOKEN")),
    "instagram": bool(os.environ.get("INSTAGRAM_ACCESS_TOKEN")),
    "twitter": bool(os.environ.get("TWITTER_API_KEY")),
    "facebook": bool(os.environ.get("FACEBOOK_ACCESS_TOKEN")),
}


def run_pipeline():
    print(f"=== パイプライン開始: {datetime.now().isoformat()} ===")

    # 1. ニュース収集
    print("[1/4] ニュース収集中...")
    articles = fetch_news(max_hours=24, max_per_feed=5)
    top_articles = rank_articles(articles, top_n=10)
    print(f"  取得: {len(articles)}件 → 上位{len(top_articles)}件を使用")

    # 2. スクリプト生成
    print("[2/4] スクリプト生成中（Claude API）...")
    script = generate_script(top_articles)
    print(f"  タイトル: {script['title']}")
    print(f"  シーン数: {len(script['scenes'])}")

    # スクリプトをログ保存
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = f"{log_dir}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_script.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    # 3. 動画生成（Pexels + FFmpeg）
    print("[3/4] 動画生成中（Pexels + FFmpeg）...")

    with tempfile.TemporaryDirectory() as tmpdir:
        scene_paths = generate_all_scenes(script["scenes"], tmpdir)

        # FFmpegでシーンを結合
        final_video_path = os.path.join(tmpdir, "final.mp4")
        _concat_videos(scene_paths, final_video_path)

        # 4. SNS投稿
        print("[4/4] SNS投稿中...")
        results = _publish_to_all(
            video_path=final_video_path,
            script=script,
        )

    print("\n=== 投稿結果 ===")
    for platform, url in results.items():
        print(f"  {platform}: {url}")

    return results


def _concat_videos(scene_paths: List[str], output_path: str):
    """FFmpegで動画を結合する"""
    import subprocess

    list_file = output_path + ".txt"
    with open(list_file, "w") as f:
        for path in scene_paths:
            f.write(f"file '{path}'\n")

    subprocess.run(
        ["ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_path],
        check=True,
        capture_output=True,
    )
    os.remove(list_file)


def _publish_to_all(video_path: str, script: dict) -> dict:
    """全有効SNSに投稿する"""
    results = {}
    caption = _build_caption(script)

    if ENABLED_PLATFORMS["youtube"]:
        try:
            url = upload_to_youtube(
                video_path=video_path,
                title=script["title"],
                description=caption,
                tags=[tag.lstrip("#") for tag in script["hashtags"]],
            )
            results["youtube"] = url
            print(f"  YouTube: {url}")
        except Exception as e:
            print(f"  YouTube 失敗: {e}")

    if ENABLED_PLATFORMS["tiktok"]:
        try:
            publish_id = upload_to_tiktok(
                video_path=video_path,
                title=script["title"],
                description=caption,
            )
            results["tiktok"] = publish_id
            print(f"  TikTok: {publish_id}")
        except Exception as e:
            print(f"  TikTok 失敗: {e}")

    if ENABLED_PLATFORMS["instagram"]:
        # Instagramは公開URLが必要なためYouTube URLを流用（または別途ホスト）
        video_public_url = results.get("youtube", "")
        if video_public_url:
            try:
                url = upload_to_instagram(video_url=video_public_url, caption=caption)
                results["instagram"] = url
                print(f"  Instagram: {url}")
            except Exception as e:
                print(f"  Instagram 失敗: {e}")

    if ENABLED_PLATFORMS["twitter"]:
        try:
            url = upload_to_twitter(video_path=video_path, text=caption[:280])
            results["twitter"] = url
            print(f"  Twitter/X: {url}")
        except Exception as e:
            print(f"  Twitter/X 失敗: {e}")

    if ENABLED_PLATFORMS["facebook"]:
        try:
            url = upload_to_facebook(video_path=video_path, description=caption)
            results["facebook"] = url
            print(f"  Facebook: {url}")
        except Exception as e:
            print(f"  Facebook 失敗: {e}")

    return results


def _build_caption(script: dict) -> str:
    """SNS投稿用キャプションを組み立てる"""
    hashtags = " ".join(script["hashtags"])
    return f"{script['title']}\n\n{script['description']}\n\n{hashtags}"


if __name__ == "__main__":
    run_pipeline()
