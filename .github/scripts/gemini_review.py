"""
Gemini code review script.

Reads the diff from /tmp/pr.diff, sends it to the Gemini API with the review
prompt, and writes the structured review to /tmp/gemini_review.md.

Environment variables (all required):
  GEMINI_API_KEY   Google Gemini API key
  PR_TITLE         Pull request title
  ADDED_LINES      Number of added lines (excluding generated files)
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

MAX_REVIEW_LINES = 800
PROMPT_FILE = ".github/prompts/gemini-review.md"
DIFF_FILE = "/tmp/pr.diff"
OUTPUT_FILE = "/tmp/gemini_review.md"
MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
DEFAULT_RETRY_WAIT = 60


def load_prompt() -> str:
    with open(PROMPT_FILE) as f:
        return f.read()


def load_diff() -> str:
    try:
        with open(DIFF_FILE) as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("No diff file found at %s", DIFF_FILE)
        return ""


def build_message(prompt: str, diff: str, pr_title: str) -> str:
    return f"{prompt}\n\n## Pull request title\n\n{pr_title}\n\n## Diff\n\n```diff\n{diff}\n```"


def _extract_retry_after(error_message: str) -> float:
    """Parse the suggested retry delay from a RESOURCE_EXHAUSTED error message."""
    match = re.search(r"retry in ([\d.]+)s", error_message)
    if match:
        return float(match.group(1)) + 5.0
    return DEFAULT_RETRY_WAIT


def call_gemini(api_key: str, message: str) -> str:
    client = genai.Client(api_key=api_key)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Calling Gemini API (attempt %d/%d)...", attempt, MAX_RETRIES)
            response = client.models.generate_content(
                model=MODEL,
                contents=message,
            )
            return response.text  # type: ignore[return-value]
        except Exception as exc:
            logger.exception("Gemini API call failed on attempt %d", attempt)
            if attempt < MAX_RETRIES:
                wait = _extract_retry_after(str(exc))
                logger.info("Retrying in %.1f seconds...", wait)
                time.sleep(wait)

    raise RuntimeError("All Gemini API retries exhausted")


def write_github_env(key: str, value: str) -> None:
    github_env = os.environ.get("GITHUB_ENV", "/dev/null")
    with open(github_env, "a") as f:
        f.write(f"{key}={value}\n")


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    pr_title = os.environ.get("PR_TITLE", "")
    added_lines = int(os.environ.get("ADDED_LINES", "0"))

    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set")
        sys.exit(1)

    diff = load_diff()

    if not diff.strip():
        logger.info("Empty diff -- skipping review")
        with open(OUTPUT_FILE, "w") as f:
            f.write("No code changes detected in this pull request.")
        return

    if added_lines > MAX_REVIEW_LINES:
        logger.warning(
            "PR adds %d lines (limit %d) -- posting size warning",
            added_lines,
            MAX_REVIEW_LINES,
        )
        with open(OUTPUT_FILE, "w") as f:
            f.write(
                f"**Must fix**\n\n"
                f"- **PR too large to review effectively** -- {added_lines} added lines "
                f"(limit {MAX_REVIEW_LINES}, excluding migrations, lockfiles, and docs). "
                f"Split into smaller, independently reviewable pull requests. (`PR size`)"
            )
        write_github_env("HAS_BLOCKING", "true")
        return

    prompt = load_prompt()
    message = build_message(prompt, diff, pr_title)

    logger.info("Sending diff (%d added lines) to Gemini for review...", added_lines)
    try:
        review = call_gemini(api_key, message)
    except Exception:
        logger.exception("Gemini review failed -- writing infra-error notice")
        with open(OUTPUT_FILE, "w") as f:
            f.write(
                "## Gemini Review -- Infrastructure Error\n\n"
                "The Gemini API call failed after all retries. "
                "Check the [workflow run logs]"
                f"(https://github.com/{os.environ.get('GITHUB_REPOSITORY', '')}/actions) "
                "for details.\n\n"
                "Push a new commit to retry."
            )
        write_github_env("HAS_BLOCKING", "false")
        return

    with open(OUTPUT_FILE, "w") as f:
        f.write(review)

    has_blocking = "**Must fix**" in review
    write_github_env("HAS_BLOCKING", "true" if has_blocking else "false")

    logger.info("Review written to %s (blocking=%s)", OUTPUT_FILE, has_blocking)


if __name__ == "__main__":
    main()
