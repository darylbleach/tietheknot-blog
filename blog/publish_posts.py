#!/usr/bin/env python3
"""
TieTheKnot — Publish blog posts to the CMS
Run: python3 publish_posts.py

API key is read from the BLOG_CMS_API_KEY environment variable.
For local use, it falls back to the hardcoded key below.
"""

import json
import urllib.request
import urllib.error
import os
import re

# ── CONFIG ─────────────────────────────────────────────────────────────────
API_KEY  = os.environ.get('BLOG_CMS_API_KEY', '')
if not API_KEY:
    print("❌ BLOG_CMS_API_KEY not set. Run: source ~/Downloads/TieTheKnot-Instagram-Kit\\ 2/.env")
    exit(1)
BASE_URL = "https://tietheknot.uk/api/cms/blog/posts"
BLOG_DIR = os.path.dirname(os.path.abspath(__file__))
# ───────────────────────────────────────────────────────────────────────────


def extract_meta(text, key):
    """Pull a value from a **Key:** line in the metadata block."""
    match = re.search(rf'^\*\*{re.escape(key)}:\*\*\s*(.+)$', text, re.MULTILINE)
    return match.group(1).strip() if match else None


def strip_metadata_block(text):
    """Remove the **Field:** metadata lines and the following --- separator."""
    text = re.sub(r'^\*\*[^*]+:\*\*.*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*---\s*\n', '', text, count=1)
    return text.strip()


def post(payload):
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        BASE_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    files = sorted(f for f in os.listdir(BLOG_DIR) if f.startswith("post-") and f.endswith(".md"))

    if not files:
        print("❌  No post-*.md files found in", BLOG_DIR)
        return

    for filename in files:
        path = os.path.join(BLOG_DIR, filename)
        with open(path) as f:
            raw = f.read()

        title     = extract_meta(raw, "Meta title") or ""
        slug      = extract_meta(raw, "Slug") or ""
        meta_desc = extract_meta(raw, "Meta description") or ""
        cover     = extract_meta(raw, "Featured image") or ""

        content = strip_metadata_block(raw)

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

        print(f"\nPublishing: {filename}")
        print(f"  Title:  {display_title}")
        print(f"  Slug:   {slug}")

        status, resp = post(payload)

        if status == 201:
            print(f"  ✅  Published → {resp.get('url', '')}")
        elif status == 409:
            print("  ⏭️  Already published (slug exists), skipping.")
        elif status == 503:
            print("  ❌  503 — BLOG_CMS_API_KEY not set. Check env var and retry.")
            break
        elif status == 401:
            print("  ❌  401 — API key rejected.")
            break
        else:
            print(f"  ❌  {status} — {resp}")


if __name__ == "__main__":
    main()
