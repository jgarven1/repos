"""
Claude API processor for Plaud transcripts.

For each transcript:
  - Sends content to claude-sonnet-4-6
  - Extracts title, summary, attendees, action items, key decisions, topics
  - Saves structured JSON to APP_SUPPORT/processed/

For querying:
  - Loads all processed summaries
  - Optionally includes raw transcripts for relevant matches
  - Asks Claude a natural language question about your meetings
"""

import json
import pathlib
import re

import anthropic
import security

PROCESSED_DIR   = security.APP_SUPPORT / "processed"
MODEL           = "claude-sonnet-4-6"
MAX_TOKENS      = 2048
QUERY_MAX_TOKENS = 4096


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------

def get_api_key():
    return security.get_api_key()


def has_api_key():
    return bool(get_api_key())


# ---------------------------------------------------------------------------
# Process a single transcript
# ---------------------------------------------------------------------------

EXTRACT_PROMPT = """\
You are analyzing a meeting transcript. Extract the following and respond with \
valid JSON only — no markdown, no explanation, just the JSON object.

{{
  "title": "short descriptive title for this meeting",
  "date": "YYYY-MM-DD if detectable, else null",
  "duration_minutes": integer or null,
  "attendees": ["list of speaker names"],
  "summary": "2-4 sentence summary of what was discussed",
  "action_items": ["each action item as a string"],
  "key_decisions": ["each key decision made"],
  "topics": ["main topics covered"],
  "sentiment": "positive | neutral | negative | mixed"
}}

Transcript:
{transcript}
"""


def process_transcript(transcript_path, account="default"):
    """
    Send a transcript to Claude and save the structured result.
    Returns the processed dict, or raises on failure.
    """
    transcript_path = pathlib.Path(transcript_path)
    text = transcript_path.read_text(encoding="utf-8")

    client = anthropic.Anthropic(api_key=get_api_key())
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{
            "role": "user",
            "content": EXTRACT_PROMPT.format(transcript=text),
        }],
    )

    raw = message.content[0].text.strip()
    # Strip any accidental markdown code fences
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    result = json.loads(raw)
    result["source_file"] = transcript_path.name
    result["account"]     = account

    # Save to processed/
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / (transcript_path.stem + ".json")
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    security.set_secure_permissions(out_path)

    return result


def is_processed(transcript_path):
    """Return True if a processed JSON already exists for this transcript."""
    stem = pathlib.Path(transcript_path).stem
    return (PROCESSED_DIR / (stem + ".json")).exists()


def load_all_processed():
    """Return a list of all processed transcript dicts."""
    if not PROCESSED_DIR.exists():
        return []
    results = []
    for f in sorted(PROCESSED_DIR.glob("*.json")):
        try:
            results.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return results


def process_all_unprocessed(account="default", progress_cb=None):
    """
    Find every exported transcript that hasn't been processed yet and
    send it through Claude.  Calls progress_cb(message) if provided.
    Returns (succeeded, failed) counts.
    """
    td = security.transcripts_path(account)
    if not td.exists():
        return 0, 0

    transcripts = sorted(td.glob("*.txt")) + sorted(td.glob("*.docx"))
    todo = [t for t in transcripts if not is_processed(t)]

    succeeded = failed = 0
    for t in todo:
        if progress_cb:
            progress_cb(f"Processing '{t.name}'…")
        try:
            process_transcript(t, account=account)
            succeeded += 1
            if progress_cb:
                progress_cb(f"✓ '{t.name}'")
        except Exception as exc:
            failed += 1
            if progress_cb:
                progress_cb(f"✗ '{t.name}': {exc}")

    return succeeded, failed


# ---------------------------------------------------------------------------
# Query across all meetings
# ---------------------------------------------------------------------------

QUERY_SYSTEM = """\
You are a helpful assistant with access to a person's meeting transcripts.
Answer the user's question using only the meeting data provided.
Be specific — reference meeting titles, dates, and attendees where relevant.
If the answer isn't in the data, say so clearly.
"""


def ask(question, account="default", include_raw=False):
    """
    Ask a natural language question about the user's meetings.
    Loads processed summaries (and optionally raw transcripts) as context.
    Returns the answer string.
    """
    summaries = load_all_processed()
    if not summaries:
        return "No processed transcripts found. Run 'Process with Claude' first."

    # Filter to the requested account
    summaries = [s for s in summaries if s.get("account", "default") == account]
    if not summaries:
        return f"No processed transcripts found for the '{account}' account."

    context_parts = ["## Meeting Summaries\n"]
    for s in summaries:
        context_parts.append(
            f"### {s.get('title', s.get('source_file', 'Unknown'))}"
            f" ({s.get('date', 'date unknown')})\n"
            f"Attendees: {', '.join(s.get('attendees', []))}\n"
            f"Summary: {s.get('summary', '')}\n"
            f"Action items: {'; '.join(s.get('action_items', []))}\n"
            f"Key decisions: {'; '.join(s.get('key_decisions', []))}\n"
            f"Topics: {', '.join(s.get('topics', []))}\n"
        )

    if include_raw:
        td = security.transcripts_path(account)
        context_parts.append("\n## Raw Transcripts\n")
        for s in summaries:
            raw_file = td / s.get("source_file", "")
            if raw_file.exists():
                context_parts.append(
                    f"### {s.get('title', raw_file.name)}\n"
                    + raw_file.read_text(encoding="utf-8")[:6000]
                    + "\n"
                )

    context = "\n".join(context_parts)

    client = anthropic.Anthropic(api_key=get_api_key())
    message = client.messages.create(
        model=MODEL,
        max_tokens=QUERY_MAX_TOKENS,
        system=QUERY_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"{context}\n\n---\n\nQuestion: {question}",
        }],
    )
    return message.content[0].text.strip()
