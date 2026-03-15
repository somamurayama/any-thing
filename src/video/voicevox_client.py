"""
VOICEVOX TTS モジュール
ナレーションテキストを VOICEVOX Engine API で音声合成する
"""
import os
import requests


VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://localhost:50021")
# スピーカーID（デフォルト: 3 = ずんだもん ノーマル）
# 他の選択肢: 1=四国めたん, 8=春日部つむぎ, 13=青山龍星
VOICEVOX_SPEAKER = int(os.environ.get("VOICEVOX_SPEAKER", "3"))


def synthesize(text: str, output_path: str) -> str:
    """
    テキストを音声合成して WAV ファイルに保存する

    Args:
        text: ナレーションテキスト
        output_path: 保存先パス（.wav）

    Returns:
        output_path
    """
    # Step 1: 音声クエリ生成
    res = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={"text": text, "speaker": VOICEVOX_SPEAKER},
        timeout=30,
    )
    res.raise_for_status()
    query = res.json()

    # Step 2: 音声合成
    res = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": VOICEVOX_SPEAKER},
        json=query,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    res.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(res.content)

    return output_path
