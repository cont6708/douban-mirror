# Scripts

Helper scripts for batch-collecting Douban user data.

## fetch_books.py

Fetches all books from a user's Douban collection (读过, 在读, 想读).

```bash
python fetch_books.py <douban_id> [--category {collect|do|wish}] [--output file.txt]
```

Handles the `book.douban.com` 403 anti-scraping barrier via browser User-Agent headers.

## fetch_statuses.py

Fetches all statuses (动态) from a user's Douban timeline. **Requires login cookie.**

```bash
export DB_CL2='dbcl2="your_cookie_value"'
python fetch_statuses.py <douban_id> [--output file.txt]
```

Statuses are the richest data source — they contain star ratings for movies that aren't visible on collection pages.

## Privacy

These scripts:
- Run entirely locally
- Do NOT send data to any external service
- Do NOT store cookies or personal data
- Use polite delays (0.3-1.0s) between requests to avoid overloading Douban servers
