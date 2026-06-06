#!/usr/bin/env python3
"""
Fetch all statuses (动态/广播) from a Douban user's timeline.

Usage:
    export DB_CL2='dbcl2="your_cookie_value"'
    python fetch_statuses.py <douban_id> [--output statuses_data.txt]

Features:
    - Collects all public statuses (watched/read/want-to-read actions with star ratings)
    - Handles Douban's JavaScript pagination (?p=N scheme)
    - Extracts star ratings from HTML entities (&#9733;)
    - Polite delays between requests (0.5-1.0s)

Requirements:
    Python 3.7+, no external dependencies
    Douban login cookie (dbcl2) — required for accessing statuses

Getting the cookie:
    1. Log in to douban.com in your browser
    2. Use a cookie editor extension (e.g., Cookie-Editor for Chrome)
    3. Export cookies and find the "dbcl2" key
    4. Set as environment variable: export DB_CL2='dbcl2="VALUE"'
"""

import re
import urllib.request
import time
import sys
import os
import argparse


def get_headers():
    cookie = os.environ.get("DB_CL2", "")
    if not cookie:
        print("ERROR: DB_CL2 environment variable not set.", file=sys.stderr)
        print("  export DB_CL2='dbcl2=\"your_cookie_value\"'", file=sys.stderr)
        sys.exit(1)

    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": cookie,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.douban.com/",
    }


def fetch(url, headers):
    """Fetch a URL and return decoded HTML string."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return None


def parse_statuses(html):
    """Extract status entries from a status page HTML."""
    entries = []

    # Find all status blocks
    # Each status contains: action type (看过/想看/想读), item title, star rating, date, comment
    items = re.split(r'class="status-item"', html)
    if len(items) <= 1:
        # Try alternative parsing
        items = re.split(r'class="feed-item"', html)

    for item in items[1:]:
        entry = {}

        # Action type
        if '看过' in item:
            entry['action'] = 'watched'
        elif '想看' in item:
            entry['action'] = 'want-watch'
        elif '想读' in item:
            entry['action'] = 'want-read'
        elif '在读' in item:
            entry['action'] = 'reading'
        elif '听过' in item:
            entry['action'] = 'listened'
        else:
            entry['action'] = 'unknown'

        # Star rating (HTML entities)
        stars = item.count('&#9733;')
        entry['rating'] = stars if 1 <= stars <= 5 else None

        # Item title from media link
        title_m = re.search(r'title="([^"]+)"\s+class="media"', item)
        if title_m:
            entry['title'] = title_m.group(1).strip()
        else:
            title_m = re.search(r'<a[^>]+title="([^"]+)"', item)
            entry['title'] = title_m.group(1).strip() if title_m else None

        # Date
        date_m = re.search(r'title="(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"', item)
        if date_m:
            entry['timestamp'] = date_m.group(1)
        else:
            date_m = re.search(r'(\d{4}-\d{2}-\d{2})', item)
            entry['timestamp'] = date_m.group(1) if date_m else None

        # Comment text
        comment_m = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', item, re.DOTALL)
        if comment_m:
            comment = re.sub(r'<[^>]+>', ' ', comment_m.group(1)).strip()
            comment = re.sub(r'\s+', ' ', comment)
            if len(comment) > 5:
                entry['comment'] = comment

        if entry.get('title'):
            entries.append(entry)

    return entries


def collect_all_statuses(douban_id, max_pages=500):
    """
    Collect all statuses for a douban user.

    Args:
        douban_id: The user's Douban numeric ID
        max_pages: Safety limit

    Returns:
        List of status entry dicts
    """
    headers = get_headers()
    base_url = f"https://www.douban.com/people/{douban_id}/statuses"
    all_entries = []
    seen_ids = set()
    empty_streak = 0

    for page in range(1, max_pages + 1):
        url = f"{base_url}?p={page}"
        print(f"  Page {page}...", file=sys.stderr, end=" ")
        html = fetch(url, headers)

        if html is None:
            empty_streak += 1
            print("FAILED", file=sys.stderr)
            if empty_streak >= 3:
                break
            time.sleep(1)
            continue

        entries = parse_statuses(html)
        if not entries:
            empty_streak += 1
            print("empty", file=sys.stderr)
            if empty_streak >= 3:
                break
        else:
            empty_streak = 0
            # Deduplicate by title
            new_entries = []
            for e in entries:
                key = (e.get('title', ''), e.get('timestamp', ''))
                if key not in seen_ids:
                    seen_ids.add(key)
                    new_entries.append(e)
            all_entries.extend(new_entries)
            print(f"{len(entries)} entries ({len(new_entries)} new)", file=sys.stderr)

        # Longer delay to avoid rate limiting
        time.sleep(0.8)

    return all_entries


def format_output(entries, output_file):
    """Write statuses to a formatted markdown file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Statuses ({len(entries)})\n\n")

        # Statistics
        actions = {}
        rated = [e for e in entries if e.get('rating')]
        for e in entries:
            actions[e['action']] = actions.get(e['action'], 0) + 1

        f.write("## Statistics\n")
        f.write(f"- Total entries: {len(entries)}\n")
        f.write(f"- With ratings: {len(rated)}\n")
        f.write(f"- Actions: {actions}\n")

        if rated:
            avg = sum(e['rating'] for e in rated) / len(rated)
            f.write(f"- Average rating: {avg:.2f}\n")

        f.write("\n## Timeline\n\n")
        for i, e in enumerate(entries):
            stars = "★" * e['rating'] if e.get('rating') else "—"
            ts = e.get('timestamp', '?')
            action_map = {
                'watched': '看过', 'want-watch': '想看',
                'want-read': '想读', 'reading': '在读',
                'listened': '听过', 'unknown': '标记'
            }
            action = action_map.get(e['action'], e['action'])
            comment = e.get('comment', '')

            f.write(f"**{i+1}. {e.get('title', 'Unknown')}**\n")
            f.write(f"  {action} | {stars} | {ts}\n")
            if comment:
                f.write(f"  > {comment}\n")
            f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Fetch Douban user's statuses")
    parser.add_argument("douban_id", help="Douban user numeric ID")
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    parser.add_argument("--max-pages", "-m", type=int, default=500,
                        help="Maximum pages to fetch (safety limit)")
    args = parser.parse_args()

    print(f"Fetching statuses for douban ID: {args.douban_id}", file=sys.stderr)

    entries = collect_all_statuses(args.douban_id, args.max_pages)

    output = args.output or f"douban_{args.douban_id}_statuses.txt"
    format_output(entries, output)
    print(f"\nSaved {len(entries)} statuses to {output}", file=sys.stderr)


if __name__ == "__main__":
    main()
