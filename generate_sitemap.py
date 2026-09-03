#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.top-fight.cz/"
PUBLICATION_NAME = "Top-Fight.cz"
LANGUAGE = "cs"
OUTPUT = Path(__file__).with_name("news-sitemap.xml")
MAX_PAGES = 6
MAX_ARTICLES = 1000
WINDOW_HOURS = 48
TZ = timezone(timedelta(hours=2))  # Europe/Prague summer time; article dates are local site time.

UA = (
    "Mozilla/5.0 (compatible; TopFightNewsSitemap/1.0; "
    "+https://www.top-fight.cz/)"
)
DATE_RE = re.compile(r"\b(\d{2})[./](\d{2})[./](\d{4})\s+(\d{2}):(\d{2})\b")


def get(url: str) -> str:
    r = requests.get(url, timeout=25, headers={"User-Agent": UA})
    r.raise_for_status()
    return r.text


def parse_listing(url: str) -> list[dict]:
    soup = BeautifulSoup(get(url), "html.parser")
    results: list[dict] = []

    for h2 in soup.find_all("h2"):
        a = h2.find("a", href=True)
        if not a:
            continue
        href = urljoin(BASE_URL, a["href"])
        p = urlparse(href)
        if p.netloc not in {"top-fight.cz", "www.top-fight.cz"}:
            continue
        if href.rstrip("/") == BASE_URL.rstrip("/"):
            continue

        # Search a limited amount of nearby text for the listing timestamp.
        bits = []
        node = h2
        for _ in range(8):
            node = node.next_element
            if node is None:
                break
            if getattr(node, "name", None) == "h2" and node is not h2:
                break
            if isinstance(node, str):
                s = " ".join(node.split())
                if s:
                    bits.append(s)
            joined = " ".join(bits)
            m = DATE_RE.search(joined)
            if m:
                d, mo, y, hh, mm = map(int, m.groups())
                dt = datetime(y, mo, d, hh, mm, tzinfo=TZ)
                results.append({
                    "url": href,
                    "title": " ".join(a.get_text(" ", strip=True).split()),
                    "published": dt,
                })
                break
    return results


def collect_articles() -> list[dict]:
    cutoff = datetime.now(TZ) - timedelta(hours=WINDOW_HOURS)
    seen: set[str] = set()
    items: list[dict] = []

    for page in range(1, MAX_PAGES + 1):
        url = BASE_URL if page == 1 else urljoin(BASE_URL, f"page/{page}/")
        try:
            batch = parse_listing(url)
        except Exception as e:
            print(f"WARN: cannot read {url}: {e}", file=sys.stderr)
            continue

        if not batch:
            continue

        for item in batch:
            canonical = item["url"].split("#", 1)[0]
            if canonical in seen:
                continue
            seen.add(canonical)
            if item["published"] >= cutoff:
                item["url"] = canonical
                items.append(item)

        oldest = min(x["published"] for x in batch)
        if oldest < cutoff and page > 1:
            break
        time.sleep(0.25)

    items.sort(key=lambda x: x["published"], reverse=True)
    return items[:MAX_ARTICLES]


def build_xml(items: list[dict]) -> bytes:
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    ET.register_namespace("news", "http://www.google.com/schemas/sitemap-news/0.9")
    urlset = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")

    for item in items:
        url_el = ET.SubElement(urlset, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
        ET.SubElement(url_el, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text = item["url"]
        news = ET.SubElement(url_el, "{http://www.google.com/schemas/sitemap-news/0.9}news")
        pub = ET.SubElement(news, "{http://www.google.com/schemas/sitemap-news/0.9}publication")
        ET.SubElement(pub, "{http://www.google.com/schemas/sitemap-news/0.9}name").text = PUBLICATION_NAME
        ET.SubElement(pub, "{http://www.google.com/schemas/sitemap-news/0.9}language").text = LANGUAGE
        ET.SubElement(news, "{http://www.google.com/schemas/sitemap-news/0.9}publication_date").text = item["published"].isoformat(timespec="minutes")
        ET.SubElement(news, "{http://www.google.com/schemas/sitemap-news/0.9}title").text = item["title"]

    xml = ET.tostring(urlset, encoding="utf-8", xml_declaration=True)
    return xml + b"\n"


def main() -> int:
    items = collect_articles()
    OUTPUT.write_bytes(build_xml(items))
    print(f"Wrote {OUTPUT} with {len(items)} recent articles.")
    for x in items:
        print(x["published"].isoformat(), x["url"], x["title"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
