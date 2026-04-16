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

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install Dependencies

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### 4) Set API Key

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

Optional (persistent in zsh):

```bash
echo 'export ANTHROPIC_API_KEY="your_anthropic_api_key"' >> ~/.zshrc
source ~/.zshrc
```

## Quick Start

```bash
python3 claude_blog_writer.py \
  --url "https://cigmaaccounting.co.uk/understanding-directors-loans/" \
  --prompt-file "cigma_prompt.txt" \
  --model "claude-sonnet-4-6" \
  --format md \
  --out "./output/directors_loan_blog"
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
