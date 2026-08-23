#!/usr/bin/env python3
"""Fail publishing when a Knowledge Center article has broken or incomplete media."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote, parse_qs
import sys

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "knowledge-center"
SITE_HOST = "function-media-intelligence.netlify.app"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}

class MediaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images, self.og_images = [], []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img" and a.get("src"):
            self.images.append((a["src"], a.get("alt", ""), a.get("width"), a.get("height")))
        if tag == "meta" and a.get("property") == "og:image" and a.get("content"):
            self.og_images.append(a["content"])

def local_path(article, ref):
    """Resolve same-site media references to their source file in the repo.

    Netlify Image CDN URLs such as /.netlify/images?url=/assets/hero.png&...
    are virtual endpoints. Validate the underlying `url` source asset instead of
    incorrectly looking for a physical `.netlify/images` file in the repository.
    """
    parsed = urlparse(ref)

    if parsed.scheme and parsed.netloc != SITE_HOST:
        return None

    if parsed.path == "/.netlify/images":
        source = parse_qs(parsed.query).get("url", [None])[0]
        if not source:
            return None
        source = unquote(source)
        return local_path(article, source)

    clean_path = unquote(parsed.path)
    if clean_path.startswith("/"):
        return ROOT / clean_path.lstrip("/")
    return article.parent / clean_path

def valid_signature(path):
    data = path.read_bytes()[:16]
    ext = path.suffix.lower()
    if ext == ".png": return data.startswith(b"\x89PNG\r\n\x1a\n")
    if ext in {".jpg", ".jpeg"}: return data.startswith(b"\xff\xd8\xff")
    if ext == ".gif": return data.startswith((b"GIF87a", b"GIF89a"))
    if ext == ".webp": return data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    if ext == ".svg":
        return b"<svg" in path.read_bytes()[:2048].lower()
    return False

errors = []
for article in sorted(ARTICLES.glob("*/index.html")):
    parser = MediaParser()
    parser.feed(article.read_text(encoding="utf-8"))
    label = article.parent.name
    if not parser.images:
        errors.append(f"{label}: article has no embedded editorial image")
    if not parser.og_images:
        errors.append(f"{label}: missing og:image social preview")
    for ref, alt, width, height in parser.images:
        if not alt.strip():
            errors.append(f"{label}: image missing meaningful alt text: {ref}")
        path = local_path(article, ref)
        if path is None:
            continue
        if path.suffix.lower() not in IMAGE_EXTS:
            errors.append(f"{label}: unsupported image type: {ref}")
        elif not path.is_file():
            errors.append(f"{label}: missing image file: {ref}")
        elif path.stat().st_size == 0:
            errors.append(f"{label}: zero-byte image: {ref}")
        elif not valid_signature(path):
            errors.append(f"{label}: corrupt or mislabeled image: {ref}")
    for ref in parser.og_images:
        path = local_path(article, ref)
        if path is not None and (not path.is_file() or not valid_signature(path)):
            errors.append(f"{label}: broken og:image: {ref}")

if errors:
    print("ARTICLE MEDIA AUDIT FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("ARTICLE MEDIA AUDIT PASSED")
