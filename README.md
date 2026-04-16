# AI Content Writer (Claude API)

Generate blog content from a URL and prompt using Anthropic Claude.

## Files

- `claude_blog_writer.py`: CLI script to fetch a page, send context + prompt to Claude, and save output as `md`, `txt`, or `pdf`.
- `cigma_prompt.txt`: Example long-form SEO prompt template.

## Setup

```bash
python3 -m pip install --user requests certifi reportlab
export ANTHROPIC_API_KEY="your_api_key"
```

## Example

```bash
python3 claude_blog_writer.py \
  --url "https://cigmaaccounting.co.uk/understanding-directors-loans/" \
  --prompt-file "cigma_prompt.txt" \
  --model "claude-sonnet-4-6" \
  --format md \
  --out "./output/directors_loan_blog"
```

