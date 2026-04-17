# AI Content Writer (Claude API)

Generate high-quality content from a source URL + custom prompt using Anthropic Claude.

This CLI tool:
- Fetches page content from a URL
- Extracts readable text context
- Sends context + your prompt to Claude
- Saves output as `md`, `txt`, or `pdf`

## Features

- URL-to-content workflow for blog/article generation
- Supports both short prompts (`--prompt`) and long prompts (`--prompt-file`)
- Automatic HTTP retry for temporary `429/5xx` responses
- Markdown, plain text, and PDF output
- Better macOS SSL reliability using `certifi`

## Project Files

- `claude_blog_writer.py`: Main CLI script
- `ui_app.py`: Basic web UI (URL + prompt form, generate output, download PDF/Word)
- `cigma_prompt.txt`: Sample long-form prompt
- `requirements.txt`: Python dependencies

## Requirements

- Python 3.10+
- Anthropic API key
- Internet access for source URL + Claude API

## Full Setup

### 1) Clone Repository

```bash
git clone https://github.com/ziservices/ai-content-writer.git
cd ai-content-writer
```

### 2) Create Virtual Environment (Recommended)

macOS/Linux (zsh/bash):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows (CMD):
```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3) Install Dependencies

macOS/Linux:
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Windows:
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Web UI (Basic)

You can use a browser-based UI where you:
- Enter source URL
- Paste your prompt
- Generate output
- Download as PDF and Word (`.docx`)

### Run UI on macOS/Linux

```bash
python3 ui_app.py
```

### Run UI on Windows

```powershell
python ui_app.py
```

Open:

```text
http://127.0.0.1:5050
```

Notes:
- API key is entered in UI form and used for that request.
- Generated files are stored in `generated_outputs/`.

## Deploy on Vercel

This project is now Vercel-ready with:
- `app.py` entrypoint
- Serverless-safe output path (`/tmp/generated_outputs` on Vercel)

### Steps

1. Push code to GitHub.
2. Import repository into Vercel.
3. Add environment variable in Vercel project settings:
   - `ANTHROPIC_API_KEY`
4. Deploy.

Note:
- No custom `vercel.json` is required for this setup.

### Optional CLI Deploy

```bash
npm i -g vercel
vercel
vercel --prod
```

### 4) Set API Key

macOS/Linux:
```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

Windows PowerShell:
```powershell
$env:ANTHROPIC_API_KEY="your_anthropic_api_key"
```

Windows CMD:
```bat
set ANTHROPIC_API_KEY=your_anthropic_api_key
```

Optional persistent key:

macOS (`~/.zshrc`):
```bash
echo 'export ANTHROPIC_API_KEY="your_anthropic_api_key"' >> ~/.zshrc
source ~/.zshrc
```

Windows PowerShell (current user):
```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY","your_anthropic_api_key","User")
```

## Quick Start

macOS/Linux:
```bash
python3 ./claude_blog_writer.py \
  --url "https://cigmaaccounting.co.uk/understanding-directors-loans/" \
  --prompt-file "cigma_prompt.txt" \
  --model "claude-sonnet-4-6" \
  --format md \
  --out "./output/directors_loan_blog"
```

Windows:
```powershell
python .\claude_blog_writer.py `
  --url "https://cigmaaccounting.co.uk/understanding-directors-loans/" `
  --prompt-file ".\cigma_prompt.txt" `
  --model "claude-sonnet-4-6" `
  --format md `
  --out ".\output\directors_loan_blog"
```

The above command creates:
- `./output/directors_loan_blog.md`

## Usage

### A) Use Single-Line Prompt

```bash
python3 claude_blog_writer.py \
  --url "https://example.com" \
  --prompt "Write a clear SEO blog post for UK SMB owners with H2s and FAQs." \
  --model "claude-sonnet-4-6" \
  --format md \
  --out "./output/blog_post"
```

### B) Use Long Prompt File (Recommended)

```bash
python3 claude_blog_writer.py \
  --url "https://example.com" \
  --prompt-file "./cigma_prompt.txt" \
  --model "claude-sonnet-4-6" \
  --format md \
  --out "./output/blog_post"
```

### C) Export PDF

```bash
python3 claude_blog_writer.py \
  --url "https://example.com" \
  --prompt-file "./cigma_prompt.txt" \
  --model "claude-sonnet-4-6" \
  --format pdf \
  --out "./output/blog_post"
```

### D) Save as Plain Text

```bash
python3 claude_blog_writer.py \
  --url "https://example.com" \
  --prompt "Summarize this page for a newsletter." \
  --format txt \
  --out "./output/newsletter"
```

## CLI Options

```text
--url             Source URL to read (required)
--prompt          Inline prompt text (use either --prompt OR --prompt-file)
--prompt-file     Path to prompt text file
--model           Claude model ID (default: claude-sonnet-4-6)
--format          txt | md | pdf (default: md)
--out             Output filename base (no extension)
--max-tokens      Max output tokens (default: 1800)
--temperature     Sampling temperature (default: 0.4)
```

## Output Behavior

- `--format md` -> writes `*.md`
- `--format txt` -> writes `*.txt`
- `--format pdf` -> writes `*.pdf`
- If PDF dependency is missing, script falls back to Markdown and tells you why.

## Troubleshooting

### 1) 404 Not Found (Wrong URL Variant)

Some sites work on non-`www` only or `www` only.

Example:
- Works: `https://radhakrishnawebsolution.in/welcome`
- Fails: `https://www.radhakrishnawebsolution.in/welcome`

Fix: test the URL in browser/curl first and use the working one.

### 2) 429 Too Many Requests

Cause: source site rate limit.

Fix:
- Wait 2-5 minutes and retry
- Reduce request frequency
- Try alternate source URL/page

The script already retries temporary `429/5xx`.

### 3) SSL Certificate Verify Failed (macOS)

Run:

```bash
python3 -m pip install --upgrade certifi requests
/Applications/Python\ 3.12/Install\ Certificates.command
```

If you use venv, reinstall inside that venv.

### 3b) SSL Certificate Verify Failed (Windows)

Run inside your active environment:

```powershell
python -m pip install --upgrade certifi requests
```

If you are behind a corporate proxy, configure proxy/SSL trust for your environment.

### 4) `zsh: command not found` After Pasting Prompt

Cause: broken multiline command or unmatched quotes.

Fix:
- Use `--prompt-file` for long prompts
- Avoid pasting huge quoted text directly in terminal

### 5) API Key Errors / Permission Issues

- Ensure `ANTHROPIC_API_KEY` is set in current shell
- Verify key is active and not revoked
- Confirm your account has access to the model ID you use

## Security Notes

- Never hardcode API keys in source files.
- Do not commit `.env` files with real secrets.
- If a key is exposed, revoke and rotate immediately.

## Suggested Content Workflow

1. Create a dedicated prompt file per client/industry.
2. Generate draft using this CLI.
3. Manually fact-check tax/legal/compliance references.
4. Final edit for brand voice before publishing.

## License

Use internally or adapt for your own projects.
