#!/usr/bin/env python3
"""
TieTheKnot — Publish any draft posts whose publishAt date has passed.
Run by the GitHub Action every Monday at 09:00 UTC.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_KEY  = os.environ.get('BLOG_CMS_API_KEY', '')
BASE_URL = 'https://tietheknot.uk/api/cms/blog/posts'

if not API_KEY:
    print("❌  BLOG_CMS_API_KEY not set.")
    sys.exit(1)

def api(method, url, data=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# Fetch all draft posts
status, posts = api('GET', f"{BASE_URL}?status=DRAFT")
if status != 200:
    print(f"❌  Failed to fetch drafts: {status} — {posts}")
    sys.exit(1)

if isinstance(posts, dict):
    posts = posts.get('posts') or posts.get('data') or posts.get('items') or []

now = datetime.now(timezone.utc)
published = 0

for post in posts:
    publish_at = post.get('publishAt')
    if not publish_at:
        continue

    publish_dt = datetime.fromisoformat(publish_at.replace('Z', '+00:00'))
    if publish_dt > now:
        print(f"⏳  Skipping '{post.get('slug')}' — goes live {publish_dt.strftime('%d %b %Y')}")
        continue

    print(f"🚀  Publishing '{post.get('slug')}' (was due {publish_dt.strftime('%d %b %Y')})")
    s, r = api('PATCH', f"{BASE_URL}/{post['id']}", {"status": "PUBLISHED"})
    if s in (200, 201):
        print(f"    ✅  Published")
        published += 1
    else:
        print(f"    ❌  {s} — {r}")

print(f"\n{published} post(s) published.")
