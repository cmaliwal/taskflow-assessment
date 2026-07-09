"""
Gemini release notes generator.

Reads the diff from /tmp/pr.diff, calls Gemini to produce user-facing release
notes, and writes the result to /tmp/release_notes.md.

Environment variables:
  GEMINI_API_KEY   Google Gemini API key (required)
  PR_TITLE         Pull request title
  PR_BODY          Existing PR description (may be empty)
"""

import logging
import os
import re
import sys
import time

from google import genai

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

DIFF_FILE = "/tmp/pr.diff"
OUTPUT_FILE = "/tmp/release_notes.md"
MODEL = "gemini-2.5-flash"
MAX_DIFF_CHARS = 8_000
MAX_RETRIES = 3
DEFAULT_RETRY_WAIT = 60


def load_diff() -> str:
    try:
        with open(DIFF_FILE) as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("No diff file found at %s", DIFF_FILE)
        return ""


def build_prompt(diff: str, pr_title: str, pr_body: str) -> str:
    return (
        "You are generating release notes for a pull request into main.\n\n"
        "Write a concise, user-facing release note in markdown.\n\n"
        "Format:\n"
        "## What changed\n\n"
        "- Clear, non-technical bullet points describing what this PR does\n"
        "- Focus on user-visible behavior, not implementation details\n\n"
        "## Technical summary\n\n"
        "- 2-3 bullets on the implementation approach\n\n"
        "## Migration / deployment notes\n\n"
        "- Any database migrations, env var changes, or deployment steps required\n"
        '- If none: "No action required."\n\n'
        "---\n\n"
        f"PR title: {pr_title}\n\n"
        f"Existing description:\n{pr_body or '(none)'}\n\n"
        f"Diff:\n```diff\n{diff[:MAX_DIFF_CHARS]}\n```"
    )


def _extract_retry_after(error_message: str) -> float:
    match = re.search(r"retry in ([\d.]+)s", error_message)
    if match:
        return float(match.group(1)) + 5.0
    logger.warning(
        "Could not parse retry-after from error message; falling back to %ds",
        int(DEFAULT_RETRY_WAIT),
    )
    return DEFAULT_RETRY_WAIT


def call_gemini(api_key: str, prompt: str) -> str:
    client = genai.Client(api_key=api_key)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Calling Gemini API (attempt %d/%d)...", attempt, MAX_RETRIES)
            response = client.models.generate_content(model=MODEL, contents=prompt)
            text = response.text or ""
            # Strip any code-fence wrapping the model may have added
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```[a-z]*\n?", "", text)
                text = re.sub(r"\n?```$", "", text)
            return text.strip()
        except Exception as exc:
            logger.exception("Gemini API call failed on attempt %d", attempt)
            if attempt < MAX_RETRIES:
                wait = _extract_retry_after(str(exc))
                logger.info("Retrying in %.1f seconds...", wait)
                time.sleep(wait)

    raise RuntimeError("All Gemini API retries exhausted")


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    pr_title = os.environ.get("PR_TITLE", "")
    pr_body = os.environ.get("PR_BODY", "")

    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set")
        sys.exit(1)

    diff = load_diff()

    if not diff.strip():
        logger.info("Empty diff -- skipping release notes generation")
        with open(OUTPUT_FILE, "w") as f:
            f.write("")
        return

    prompt = build_prompt(diff, pr_title, pr_body)

    try:
        notes = call_gemini(api_key, prompt)
    except Exception:
        logger.exception("Release notes generation failed after all retries")
        with open(OUTPUT_FILE, "w") as f:
            f.write("")
        return

    with open(OUTPUT_FILE, "w") as f:
        f.write(notes)

    logger.info("Release notes written to %s (%d chars)", OUTPUT_FILE, len(notes))


if __name__ == "__main__":
    main()
