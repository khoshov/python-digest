# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based automated content pipeline for **Python Digest** - a weekly newsletter for Python developers. The system processes Python-related content through a multi-agent pipeline:

1. **Scout** - Collection of Python content from specialized RSS feeds and Google Custom Search
2. **Filter** - Content relevance filtering through Flowise (focuses on Python development)
3. **Copywriter** - Post creation following specific format requirements
4. **Image Generator** - Image generation through OpenAI DALL-E
5. **Email Sender** - HTML email notifications to subscribers

## Running the Application

**Main execution:**
```bash
python main.py
```

The script runs as a complete pipeline and outputs results to an `output/` directory with timestamped markdown files.

## Project Structure

The codebase includes:
- `main.py` - The complete pipeline runner
- `config.py` - Configuration management with environment variables
- `email_sender.py` - Email notification functionality
- `pyproject.toml` - Python project configuration with dependencies
- `.env.example` - Environment variables template
- Missing dependencies: The script imports `agents.pipeline` module that doesn't exist yet

## Key Architecture Notes

**Pipeline Flow:**
- Python sources (RSS, blogs, communities) → Scout → Filter → Copywriter → Image Generator → Email → Output

**Content Focus:**
- Python news and tool releases
- Technical articles on Python development
- Learning materials for Python engineers
- Python community stories and memes
- Time period: 7 days (168 hours)
- Output: 8 posts sorted by relevance

**Post Format (per specifications):**
- **Title**: max 100 characters, Russian (except proper names)
- **Type**: article, news, video, story, meme, etc.
- **Description**: max 350 characters, Russian summary
- **Link**: source URL

**Configuration System:**
Environment variables loaded through `config.py`:
- `flowise_host`, `flowise_filter_id`, `flowise_copywriter_id` (required)
- `google_api_key`, `google_cse_id` (for Google News, optional)
- `openai_api_key` (for image generation, optional)
- Email settings: `smtp_server`, `smtp_username`, `smtp_password`, `email_recipients`
- `rss_hours_period=168` (7 days)

**Output Management:**
- Creates timestamped log files in `logs/` directory
- Saves results as markdown files in `output/` directory
- Generates summary files with post statistics
- Sends HTML email notifications with Python branding and file attachments

**Missing Components:**
The project references but may lack:
- Individual agent modules: `scout.py`, `filter.py`, `copywriter.py`, `image_generator.py` in `agents/` directory

## Development Setup

The project uses Python 3.12+ and appears to be configured for PyCharm IDE.

**Installation:**
```bash
pip install -e .
```

**Configuration:**
1. Copy `.env.example` to `.env`
2. Fill in your API keys and email settings
3. Configure SMTP settings for email notifications

**Required external services:**
- Flowise instance for AI processing
- Google Custom Search API (optional)
- OpenAI API (optional, for image generation)
- SMTP server for email notifications (Gmail, Yandex, etc.)