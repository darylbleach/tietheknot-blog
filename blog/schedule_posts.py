#!/usr/bin/env python3
"""
TieTheKnot — Schedule all unposted blog posts, one per week.
Posts them as DRAFT with a publishAt date. If the CMS supports
scheduled publishing, they'll go live automatically on that date.

Usage:
  python3 schedule_posts.py

Set START_DATE to the date you want the first scheduled post to go live.
Posts will be spaced one week apart from that date.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

# ── CONFIG ──────────────────────────────────────────────────────────────────
API_KEY  = os.environ.get('BLOG_CMS_API_KEY', '')
BASE_URL = 'https://tietheknot.uk/api/cms/blog/posts'

# First post goes live next Monday at 09:00 UTC, then every Monday after
today = datetime.now(timezone.utc)
days_until_monday = (7 - today.weekday()) % 7 or 7  # always next Monday, not today
START_DATE = (today + timedelta(days=days_until_monday)).replace(hour=9, minute=0, second=0, microsecond=0)

# Posts to schedule in order (skip post-01, already live)
POSTS = [
    "post-02-what-to-put-on-wedding-website.md",
    "post-03-do-i-need-a-wedding-website.md",
    "post-04-how-to-create-wedding-website-uk.md",
    "post-05-wedding-website-vs-paper-invites-uk.md",
    "post-06-how-much-does-a-wedding-website-cost-uk.md",
]
# ────────────────────────────────────────────────────────────────────────────

BLOG_DIR = os.path.dirname(os.path.abspath(__file__))

if not API_KEY:
    print("❌  BLOG_CMS_API_KEY not set. Run: source ~/Downloads/TieTheKnot-Instagram-Kit\\ 2/.env")
    sys.exit(1)

def extract_meta(text, key):
    match = re.search(rf'^\*\*{re.escape(key)}:\*\*\s*(.+)$', text, re.MULTILINE)
    return match.group(1).strip() if match else None

def strip_metadata_block(text):
    text = re.sub(r'^\*\*[^*]+:\*\*.*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*---\s*\n', '', text, count=1)
    return text.strip()

def post_to_cms(payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE_URL, data=data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

for i, filename in enumerate(POSTS):
    publish_date = START_DATE + timedelta(weeks=i)
    path = os.path.join(BLOG_DIR, filename)

    if not os.path.exists(path):
        print(f"⚠️  File not found: {filename}")
        continue

    with open(path) as f:
        raw = f.read()

    title     = extract_meta(raw, "Meta title") or ""
    slug      = extract_meta(raw, "Slug") or ""
    meta_desc = extract_meta(raw, "Meta description") or ""
    cover     = extract_meta(raw, "Featured image") or ""
    content   = strip_metadata_block(raw)

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()
                  and not p.strip().startswith("#") and not p.strip().startswith("!")]
    excerpt = paragraphs[0][:300] if paragraphs else ""

    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    display_title = h1_match.group(1) if h1_match else title

    publish_iso = publish_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    payload = {
        "title":           display_title,
        "slug":            slug,
        "content":         content,
        "excerpt":         excerpt,
        "coverImage":      cover,
        "metaTitle":       title,
        "metaDescription": meta_desc,
        "authorName":      "Tie The Knot Team",
        "status":          "SCHEDULED",
        "publishAt":       publish_iso,
    }

    print(f"\n📅  {filename}")
    print(f"    Slug:       {slug}")
    print(f"    Goes live:  {publish_date.strftime('%d %b %Y, %H:%M UTC')}")

    status, resp = post_to_cms(payload)

    if status == 201:
        print(f"    ✅  Scheduled")
    elif status == 409:
        print(f"    ⏭️  Slug already exists, skipping")
    else:
        print(f"    ❌  {status} — {resp}")
        # If SCHEDULED status isn't supported, try DRAFT with publishAt
        if status == 400:
            print(f"    🔄  Retrying as DRAFT...")
            payload["status"] = "DRAFT"
            status2, resp2 = post_to_cms(payload)
            if status2 == 201:
                print(f"    ✅  Saved as DRAFT (publishAt: {publish_iso})")
            else:
                print(f"    ❌  {status2} — {resp2}")

print("\nDone. Check your CMS to confirm scheduled dates are set correctly.")
