#!/usr/bin/env python3
"""
Basic web UI for AI Content Writer.

Run:
  export ANTHROPIC_API_KEY="your_key"
  python3 ui_app.py
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from flask import Flask, abort, render_template, request, send_from_directory

from claude_blog_writer import (
    DEFAULT_MODEL,
    build_http_session,
    call_claude,
    fetch_url_html,
    get_verify_bundle,
    html_to_text,
    save_pdf_output,
    validate_source_url,
)


app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent

# Vercel serverless filesystem is read-only except /tmp.
if os.getenv("VERCEL"):
    OUTPUT_DIR = Path("/tmp/generated_outputs")
else:
    OUTPUT_DIR = BASE_DIR / "generated_outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_docx_output(out_base: Path, content: str) -> Optional[Path]:
    try:
        from docx import Document
    except Exception:
        return None

    out_file = out_base.with_suffix(".docx")
    document = Document()
    for line in content.splitlines():
        if line.strip():
            document.add_paragraph(line)
        else:
            document.add_paragraph("")
    document.save(out_file)
    return out_file


@app.get("/download/<path:filename>")
def download_file(filename: str):
    safe_name = Path(filename).name
    if safe_name != filename:
        abort(404)
    target = OUTPUT_DIR / safe_name
    if not target.exists() or not target.is_file():
        abort(404)
    return send_from_directory(OUTPUT_DIR, safe_name, as_attachment=True)


@app.route("/", methods=["GET", "POST"])
def index():
    data = {
        "url": "",
        "prompt": "",
        "model": DEFAULT_MODEL,
        "max_tokens": "2500",
        "temperature": "0.4",
    }
    result_text = ""
    error_msg = ""
    info_msg = ""
    download_files: dict[str, str] = {}

    if request.method == "POST":
        data["url"] = (request.form.get("url") or "").strip()
        data["prompt"] = (request.form.get("prompt") or "").strip()
        data["model"] = (request.form.get("model") or DEFAULT_MODEL).strip()
        data["max_tokens"] = (request.form.get("max_tokens") or "2500").strip()
        data["temperature"] = (request.form.get("temperature") or "0.4").strip()

        api_key = (request.form.get("api_key") or "").strip()
        if not api_key:
            error_msg = "Please enter your Anthropic API key."
            return render_template(
                "index.html",
                data=data,
                result_text=result_text,
                error_msg=error_msg,
                info_msg=info_msg,
                download_files=download_files,
            )

        if not data["url"] or not data["prompt"]:
            error_msg = "URL and Prompt are required."
            return render_template(
                "index.html",
                data=data,
                result_text=result_text,
                error_msg=error_msg,
                info_msg=info_msg,
                download_files=download_files,
            )

        try:
            max_tokens = int(data["max_tokens"])
            temperature = float(data["temperature"])
        except ValueError:
            error_msg = "Invalid max_tokens or temperature value."
            return render_template(
                "index.html",
                data=data,
                result_text=result_text,
                error_msg=error_msg,
                info_msg=info_msg,
                download_files=download_files,
            )

        try:
            validate_source_url(data["url"])
            session = build_http_session()
            verify_bundle = get_verify_bundle()

            html = fetch_url_html(session, data["url"], verify=verify_bundle)
            page_title, page_text = html_to_text(html)

            result_text, was_truncated = call_claude(
                session=session,
                api_key=api_key,
                model=data["model"],
                prompt=data["prompt"],
                source_url=data["url"],
                page_title=page_title,
                page_text=page_text,
                verify=verify_bundle,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            file_id = uuid.uuid4().hex
            out_base = OUTPUT_DIR / f"ai_content_{file_id}"

            md_file = out_base.with_suffix(".md")
            md_file.write_text(result_text, encoding="utf-8")
            download_files["Markdown"] = md_file.name

            pdf_file = save_pdf_output(out_base, result_text)
            if pdf_file:
                download_files["PDF"] = pdf_file.name
            else:
                info_msg = "PDF export unavailable (install reportlab)."

            docx_file = save_docx_output(out_base, result_text)
            if docx_file:
                download_files["Word"] = docx_file.name
            else:
                if info_msg:
                    info_msg += " "
                info_msg += "Word export unavailable (install python-docx)."

            if was_truncated:
                if info_msg:
                    info_msg += " "
                info_msg += (
                    "Output reached token limit and was auto-continued."
                )

        except Exception as exc:
            error_msg = str(exc)

    return render_template(
        "index.html",
        data=data,
        result_text=result_text,
        error_msg=error_msg,
        info_msg=info_msg,
        download_files=download_files,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
