#!/usr/bin/env python3
"""
TieTheKnot — Publish a single blog post to the CMS.
Usage: python3 publish_single_post.py blog/post-01-best-wedding-website-builder-uk.md
"""

import json
import os
import sys
import urllib.request
import urllib.error
import re

API_KEY  = os.environ.get('BLOG_CMS_API_KEY', '')
if not API_KEY:
    print("❌ BLOG_CMS_API_KEY not set. Run: source ~/Downloads/TieTheKnot-Instagram-Kit\\ 2/.env")
    sys.exit(1)
BASE_URL = 'https://tietheknot.uk/api/cms/blog/posts'

def extract_meta(text, key):
    match = re.search(rf'^\*\*{re.escape(key)}:\*\*\s*(.+)$', text, re.MULTILINE)
    return match.group(1).strip() if match else None

def strip_metadata_block(text):
    text = re.sub(r'^\*\*[^*]+:\*\*.*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*---\s*\n', '', text, count=1)
    return text.strip()

def publish(filepath):
    with open(filepath) as f:
        raw = f.read()

    title     = extract_meta(raw, "Meta title") or ""
    slug      = extract_meta(raw, "Slug") or ""
    meta_desc = extract_meta(raw, "Meta description") or ""
    cover     = extract_meta(raw, "Featured image") or ""
    content   = strip_metadata_block(raw)

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip() and not p.strip().startswith("#") and not p.strip().startswith("!")]
    excerpt = paragraphs[0][:300] if paragraphs else ""

    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    display_title = h1_match.group(1) if h1_match else title

    payload = {
        "title":           display_title,
        "slug":            slug,
        "content":         content,
        "excerpt":         excerpt,
        "coverImage":      cover,
        "metaTitle":       title,
        "metaDescription": meta_desc,
        "authorName":      "Tie The Knot Team",
        "status":          "PUBLISHED",
    }

    print(f"Publishing: {display_title}")
    print(f"Slug: {slug}")

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE_URL, data=data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read())
            print(f"✅ Published → {resp.get('url', resp.get('id', 'ok'))}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ {e.code} — {body}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 publish_single_post.py <path-to-post.md>")
        sys.exit(1)
    publish(sys.argv[1])
