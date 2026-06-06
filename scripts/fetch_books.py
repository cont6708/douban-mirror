#!/usr/bin/env python3
"""
Fetch all books from a Douban user's collection.

Usage:
    python fetch_books.py <douban_id> [--output books_data.txt]

Features:
    - Collects: books read (读过), currently reading (在读), want-to-read (想读)
    - Handles book.douban.com 403 anti-scraping via browser-like headers
    - Polite delays between requests (0.3-0.5s)
    - Outputs structured markdown with ratings, dates, and comments

Requirements:
    Python 3.7+, no external dependencies
"""

import re
import urllib.request
import time
import sys
import os
import argparse


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.douban.com/",
}


def fetch(url, referer=None):
    """Fetch a URL with browser headers. Returns decoded HTML string or None."""
    headers = HEADERS.copy()
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}", file=sys.stderr)
        return None


def parse_book_page(html):
    """Parse a book collection page HTML, return list of book dicts."""
    books = []
    items = re.split(r'<li class="subject-item">', html)
    for item in items[1:]:
        book = {}

        # Title and URL
        title_m = re.search(r'<a href="([^"]+)"[^>]*title="([^"]*)"', item)
        if not title_m:
            continue
        book['url'] = title_m.group(1)
        book['title'] = title_m.group(2).strip()

        # Author / pub info
        pub_m = re.search(r'<div class="pub">\s*(.*?)\s*</div>', item, re.DOTALL)
        if pub_m:
            book['pub_info'] = pub_m.group(1).strip()

        # Star rating
        rating_m = re.search(r'<span class="rating(\d)-t"></span>', item)
        book['rating'] = int(rating_m.group(1)) if rating_m else None

        # Date
        date_m = re.search(r'<span class="date">([^<]+)</span>', item)
        book['date'] = date_m.group(1).strip() if date_m else None

        # Comment
        comment_m = re.search(r'<p class="comment[^"]*"[^>]*>\s*(.*?)\s*</p>', item, re.DOTALL)
        if comment_m:
            comment = re.sub(r'<[^>]+>', '', comment_m.group(1)).strip()
            if comment and comment not in ('读过', '想读', '在读'):
                book['comment'] = comment
            else:
                book['comment'] = None
        else:
            book['comment'] = None

        books.append(book)
    return books


def collect_books(douban_id, category="collect"):
    """
    Collect all books for a douban user.

    Args:
        douban_id: The user's Douban numeric ID
        category: 'collect' (读过), 'do' (在读), or 'wish' (想读)

    Returns:
        List of book dicts
    """
    base_url = f"https://book.douban.com/people/{douban_id}/{category}"
    all_books = []
    start = 0
    empty_streak = 0

    while empty_streak < 3:  # Stop after 3 consecutive empty pages
        url = f"{base_url}?sort=time&start={start}&mode=grid&tags_sort=count"
        print(f"  Page start={start}...", file=sys.stderr, end=" ")
        html = fetch(url, referer=f"https://book.douban.com/people/{douban_id}/")

        if html is None:
            empty_streak += 1
            print("FAILED", file=sys.stderr)
            start += 15
            time.sleep(1)
            continue

        books = parse_book_page(html)
        if not books:
            empty_streak += 1
            print("empty", file=sys.stderr)
        else:
            empty_streak = 0
            all_books.extend(books)
            print(f"{len(books)} books", file=sys.stderr)

        start += 15
        time.sleep(0.4)

    return all_books


def format_output(books, output_file):
    """Write books to a formatted markdown file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Books ({len(books)})\n\n")

        # Statistics
        rated = [b for b in books if b['rating'] is not None]
        commented = [b for b in books if b.get('comment')]
        f.write("## Statistics\n")
        f.write(f"- Total: {len(books)}\n")
        f.write(f"- Rated: {len(rated)} ({len(rated)/max(len(books),1)*100:.1f}%)\n")
        f.write(f"- With comments: {len(commented)} ({len(commented)/max(len(books),1)*100:.1f}%)\n")

        if rated:
            avg = sum(b['rating'] for b in rated) / len(rated)
            f.write(f"- Average rating: {avg:.2f}\n")
            dist = {}
            for b in rated:
                dist[b['rating']] = dist.get(b['rating'], 0) + 1
            f.write(f"- Rating distribution: {dict(sorted(dist.items()))}\n")

        f.write("\n## Full List\n\n")
        for i, b in enumerate(books):
            stars = "★" * b['rating'] if b['rating'] else "—"
            date_str = b.get('date', '?')
            pub = b.get('pub_info', '')
            comment = b.get('comment', '')

            f.write(f"**{i+1}. {b['title']}**\n")
            f.write(f"  {stars} | {date_str}\n")
            if pub:
                f.write(f"  {pub}\n")
            if comment:
                f.write(f"  > {comment}\n")
            f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Fetch Douban user's book collection")
    parser.add_argument("douban_id", help="Douban user numeric ID")
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    parser.add_argument("--category", "-c", default="collect",
                        choices=["collect", "do", "wish"],
                        help="Book category: collect=读过, do=在读, wish=想读")
    args = parser.parse_args()

    category_names = {"collect": "读过", "do": "在读", "wish": "想读"}
    cat_name = category_names[args.category]

    print(f"Fetching {cat_name} books for douban ID: {args.douban_id}", file=sys.stderr)

    books = collect_books(args.douban_id, args.category)

    output = args.output or f"douban_{args.douban_id}_books_{args.category}.txt"
    format_output(books, output)
    print(f"\nSaved {len(books)} books to {output}", file=sys.stderr)


if __name__ == "__main__":
    main()
