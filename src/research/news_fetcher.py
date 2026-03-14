"""
ニュース収集モジュール
RSS フィードから日本語ニュースを取得する
"""
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict


# 主要日本語ニュースRSSフィード
RSS_FEEDS = {
    "NHK": "https://www.nhk.or.jp/rss/news/cat0.xml",
    "NHK_社会": "https://www.nhk.or.jp/rss/news/cat1.xml",
    "NHK_科学文化": "https://www.nhk.or.jp/rss/news/cat3.xml",
    "NHK_政治": "https://www.nhk.or.jp/rss/news/cat4.xml",
    "NHK_経済": "https://www.nhk.or.jp/rss/news/cat5.xml",
    "NHK_国際": "https://www.nhk.or.jp/rss/news/cat6.xml",
    "朝日新聞": "https://www.asahi.com/rss/asahi/newsheadlines.rdf",
    "Yahoo_国内": "https://news.yahoo.co.jp/rss/topics/domestic.xml",
    "Yahoo_国際": "https://news.yahoo.co.jp/rss/topics/world.xml",
    "Yahoo_経済": "https://news.yahoo.co.jp/rss/topics/business.xml",
    "Yahoo_エンタメ": "https://news.yahoo.co.jp/rss/topics/entertainment.xml",
    "Yahoo_スポーツ": "https://news.yahoo.co.jp/rss/topics/sports.xml",
    "Yahoo_テクノロジー": "https://news.yahoo.co.jp/rss/topics/it.xml",
}


def fetch_news(max_hours: int = 24, max_per_feed: int = 5) -> List[Dict]:
    """
    各RSSフィードからニュースを取得する

    Args:
        max_hours: 何時間以内のニュースを取得するか
        max_per_feed: フィードあたりの最大記事数

    Returns:
        ニュース記事のリスト
    """
    articles = []
    cutoff = datetime.now() - timedelta(hours=max_hours)

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if count >= max_per_feed:
                    break

                # 公開日時の取得
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])

                # 古い記事はスキップ
                if published and published < cutoff:
                    continue

                article = {
                    "source": source,
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", "")),
                    "url": entry.get("link", ""),
                    "published": published.isoformat() if published else None,
                }
                articles.append(article)
                count += 1

        except Exception as e:
            print(f"[WARNING] {source} の取得に失敗: {e}")

    return articles


def rank_articles(articles: List[Dict], top_n: int = 10) -> List[Dict]:
    """
    記事を重要度でランキングし上位N件を返す
    （シンプルに新しい順 + タイトルの長さで重み付け）
    """
    def score(article):
        title_len = len(article.get("title", ""))
        has_date = 1 if article.get("published") else 0
        return title_len + has_date * 100

    ranked = sorted(articles, key=score, reverse=True)
    return ranked[:top_n]
