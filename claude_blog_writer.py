#!/usr/bin/env python3
"""
Generate blog content from a URL + prompt using the Anthropic Claude API.

Usage examples:
  export ANTHROPIC_API_KEY="your_key_here"

  python3 claude_blog_writer.py \
    --url "https://example.com" \
    --prompt "Write an SEO blog for Indian SMB owners. Include H2s and CTA." \
    --format md \
    --out blog_post

  python3 claude_blog_writer.py \
    --url "https://example.com" \
    --prompt "Write a concise summary for LinkedIn." \
    --format pdf \
    --out linkedin_summary
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-6"


def validate_source_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Invalid URL. Use a full URL like https://example.com/page")
    if "your-blog-source-url.com" in parsed.netloc:
        raise ValueError(
            "Replace placeholder URL with your real blog/source URL."
        )


def build_http_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_verify_bundle() -> str | bool:
    """
    Return CA bundle path from certifi when available.
    This helps on macOS where Python cert store can be missing/outdated.
    """
    try:
        import certifi

        return certifi.where()
    except Exception:
        return True


def fetch_url_html(
    session: requests.Session, url: str, verify: str | bool, timeout: int = 30
) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    response = session.get(url, headers=headers, timeout=timeout, verify=verify)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def html_to_text(html: str) -> tuple[str, str]:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    title = unescape(title_match.group(1)).strip() if title_match else "Untitled"

    cleaned = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    cleaned = re.sub(r"(?is)<style.*?>.*?</style>", " ", cleaned)
    cleaned = re.sub(r"(?is)<!--.*?-->", " ", cleaned)
    cleaned = re.sub(r"(?is)<noscript.*?>.*?</noscript>", " ", cleaned)
    cleaned = re.sub(r"(?is)<[^>]+>", "\n", cleaned)
    cleaned = unescape(cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    lines = [line.strip() for line in cleaned.splitlines()]
    lines = [line for line in lines if line]

    # Keep meaningful body text while avoiding huge payloads.
    text = "\n".join(lines)
    text = text[:32000]
    return title, text


def call_claude(
    session: requests.Session,
    api_key: str,
    model: str,
    prompt: str,
    source_url: str,
    page_title: str,
    page_text: str,
    verify: str | bool,
    max_tokens: int,
    temperature: float,
) -> str:
    user_content = (
        f"Source URL: {source_url}\n"
        f"Page title: {page_title}\n\n"
        "Extracted page content:\n"
        "-----\n"
        f"{page_text}\n"
        "-----\n\n"
        f"User request:\n{prompt}\n\n"
        "Write original content. Do not copy long chunks from the source."
    )

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": user_content}],
    }

    headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": API_VERSION,
    }

    response = session.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=120,
        verify=verify,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Claude API HTTP {response.status_code}: {response.text}"
        )

    data = response.json()
    chunks = data.get("content", [])
    texts: list[str] = []
    for chunk in chunks:
        if chunk.get("type") == "text":
            texts.append(chunk.get("text", ""))

    answer = "\n".join(t.strip() for t in texts if t.strip()).strip()
    if not answer:
        raise RuntimeError("Claude API returned no text output.")
    return answer


def save_text_output(out_base: Path, content: str, fmt: str) -> Path:
    suffix = ".md" if fmt == "md" else ".txt"
    out_file = out_base.with_suffix(suffix)
    out_file.write_text(content, encoding="utf-8")
    return out_file


def save_pdf_output(out_base: Path, content: str) -> Optional[Path]:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
    except Exception:
        return None

    out_file = out_base.with_suffix(".pdf")
    c = canvas.Canvas(str(out_file), pagesize=A4)
    width, height = A4
    left = 2 * cm
    right = width - 2 * cm
    y = height - 2 * cm
    line_height = 14

    c.setFont("Helvetica", 10)
    for raw_line in content.splitlines() or [""]:
        line = raw_line.rstrip()
        if not line:
            y -= line_height
            if y < 2 * cm:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 2 * cm
            continue

        while line:
            chunk = line
            while c.stringWidth(chunk, "Helvetica", 10) > (right - left) and len(chunk) > 1:
                chunk = chunk[:-1]

            c.drawString(left, y, chunk)
            y -= line_height
            line = line[len(chunk) :]

            if y < 2 * cm:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 2 * cm

    c.save()
    return out_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate blog content from URL + prompt using Claude API."
    )
    parser.add_argument("--url", required=True, help="Source URL to read.")
    parser.add_argument(
        "--prompt",
        help="Your content instruction prompt.",
    )
    parser.add_argument(
        "--prompt-file",
        help="Path to a text file containing your prompt (recommended for multiline prompts).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--format",
        choices=["txt", "md", "pdf"],
        default="md",
        help="Output format.",
    )
    parser.add_argument(
        "--out",
        default=f"claude_blog_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        help="Output filename base (no extension).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1800,
        help="Max tokens for Claude output.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.4,
        help="Sampling temperature.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.prompt and not args.prompt_file:
        print("Error: Provide --prompt or --prompt-file", file=sys.stderr)
        return 1
    if args.prompt and args.prompt_file:
        print("Error: Use either --prompt or --prompt-file, not both.", file=sys.stderr)
        return 1

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("Error: Set ANTHROPIC_API_KEY in environment.", file=sys.stderr)
        return 1

    prompt = args.prompt
    if args.prompt_file:
        prompt_path = Path(args.prompt_file).expanduser().resolve()
        if not prompt_path.exists():
            print(f"Error: Prompt file not found: {prompt_path}", file=sys.stderr)
            return 1
        prompt = prompt_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not prompt:
        print("Error: Prompt content is empty.", file=sys.stderr)
        return 1

    try:
        session = build_http_session()
        verify_bundle = get_verify_bundle()
        validate_source_url(args.url)
        html = fetch_url_html(session, args.url, verify=verify_bundle)
        page_title, page_text = html_to_text(html)
        result = call_claude(
            session=session,
            api_key=api_key,
            model=args.model,
            prompt=prompt,
            source_url=args.url,
            page_title=page_title,
            page_text=page_text,
            verify=verify_bundle,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
    except requests.exceptions.SSLError as e:
        print(
            "Error: SSL certificate verification failed.\n"
            "Fix options:\n"
            "1) pip install certifi\n"
            "2) For python.org Python on macOS, run: "
            "'/Applications/Python 3.12/Install Certificates.command'\n"
            f"Details: {e}",
            file=sys.stderr,
        )
        return 1
    except requests.exceptions.RequestException as e:
        print(f"Error: Network request failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    out_base = Path(args.out).expanduser().resolve()

    if args.format in {"txt", "md"}:
        out_file = save_text_output(out_base, result, args.format)
        print(f"Saved: {out_file}")
        return 0

    # PDF mode
    pdf_file = save_pdf_output(out_base, result)
    if pdf_file is not None:
        print(f"Saved: {pdf_file}")
        return 0

    # Fallback to markdown when reportlab is not installed.
    fallback = save_text_output(out_base, result, "md")
    print("PDF export requested but reportlab is not installed.")
    print("Run: pip install reportlab")
    print(f"Saved fallback markdown: {fallback}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
