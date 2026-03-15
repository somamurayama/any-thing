"""
スクリプト生成モジュール
Claude API を使ってニュースをショート動画用スクリプトに変換する
"""
import os
import anthropic
from typing import List, Dict


def _get_client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def generate_script(articles: List[Dict]) -> Dict:
    """
    ニュース記事群からショート動画スクリプトを生成する

    Args:
        articles: ニュース記事のリスト

    Returns:
        {
            "title": 動画タイトル,
            "narration": ナレーション全文,
            "scenes": [{"scene": シーン説明, "narration": セリフ, "duration": 秒数}],
            "hashtags": ハッシュタグリスト,
            "description": SNS投稿説明文,
        }
    """
    news_text = "\n\n".join([
        f"【{a['source']}】{a['title']}\n{a['summary']}"
        for a in articles
    ])

    prompt = f"""以下の今日のニュースをもとに、SNSショート動画（60秒以内）用のスクリプトを日本語で作成してください。

# 今日のニュース
{news_text}

# 出力形式（JSON）
{{
  "title": "動画タイトル（30文字以内、インパクトあり）",
  "narration": "ナレーション全文（自然な話し言葉、60秒以内に読める量）",
  "scenes": [
    {{
      "scene_number": 1,
      "visual_description": "映像の説明（英語で、Kling AIへの動画生成プロンプトとして使う）",
      "narration": "このシーンのナレーション",
      "duration": 秒数
    }}
  ],
  "hashtags": ["ハッシュタグ1", "ハッシュタグ2", ...],
  "description": "SNS投稿用の説明文（200文字以内）"
}}

# 条件
- シーン数は5〜8個
- 合計尺は45〜60秒
- 視聴者が最後まで見たくなる構成（冒頭3秒で掴む）
- visual_description は Kling AI に渡す英語プロンプト（映像的・具体的に）
- ハッシュタグは10〜15個（日本語・英語混在OK）
"""

    message = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    content = message.content[0].text

    # JSON部分を抽出
    start = content.find("{")
    end = content.rfind("}") + 1
    json_str = content[start:end]

    return json.loads(json_str)


def generate_thumbnail_prompt(script: Dict) -> str:
    """
    サムネイル生成用プロンプトを生成する
    """
    prompt = f"""以下のショート動画スクリプトに最適なサムネイル画像を生成するための
Kling AI / Stable Diffusion 用プロンプトを英語で1文で作成してください。

タイトル: {script['title']}
内容: {script['description']}

条件:
- 縦型（9:16）
- 目を引くビジュアル
- テキストオーバーレイ想定（シンプルな背景）
- フォトリアルまたはシネマティックスタイル

プロンプトのみ返してください。
"""
    message = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
