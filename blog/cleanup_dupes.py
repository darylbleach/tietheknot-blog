#!/usr/bin/env python3
"""
TieTheKnot — Delete the 4 duplicate posts created by the GitHub Action.
Run from Terminal: python3 cleanup_dupes.py
"""

import json
import urllib.request
import urllib.error

import os
API_KEY  = os.environ.get('BLOG_CMS_API_KEY', '')
if not API_KEY:
    print("❌ BLOG_CMS_API_KEY not set. Run: source ~/Downloads/TieTheKnot-Instagram-Kit\\ 2/.env")
    exit(1)
BASE_URL = 'https://tietheknot.uk/api/cms/blog/posts'

DUPES_TO_DELETE = [
    ('cmrmfv7g10005lg09n9cz6hr0', 'how-much-does-a-wedding-website-cost-uk'),
    ('cmrmfv73c0004lg094qfuhu74', 'wedding-website-vs-paper-invites-uk'),
    ('cmrmfv6b90003lg09e1qf9z39', 'how-to-create-a-wedding-website-uk-2'),
    ('cmrmfv5gf0002lg09o42vgg39', 'do-i-need-a-wedding-website-uk-2'),
    ('cmrmfv4k60001lg099t69yhm7', 'what-to-put-on-your-wedding-website-uk-2'),
    ('cmrmfv3bj0000lg09tri1clze', 'best-wedding-website-builder-uk-2'),
    ('cmrffjhqw0004jr09b9jd93w9', 'how-to-create-a-wedding-website-uk'),
    ('cmrffjgwe0003jr09duaqx72w', 'do-i-need-a-wedding-website-uk'),
    ('cmrffjg1q0002jr09ibo5omks', 'what-to-put-on-your-wedding-website-uk'),
    ('cmrffjf2k0001jr09m39f2d7q', 'best-wedding-website-builder-uk'),
]

def delete_post(post_id):
    req = urllib.request.Request(
        f"{BASE_URL}/{post_id}",
        headers={'Authorization': f'Bearer {API_KEY}'},
        method='DELETE',
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code

for post_id, slug in DUPES_TO_DELETE:
    status = delete_post(post_id)
    if status in (200, 204):
        print(f"✅ Deleted {slug} ({post_id})")
    else:
        print(f"❌ Failed ({status}): {slug} ({post_id})")

print("\nDone.")
