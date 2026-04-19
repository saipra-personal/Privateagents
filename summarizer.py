"""AI summarization using Claude API."""

import os
import json
import anthropic


SYSTEM_PROMPT = """You are an expert at analyzing spoken content and structuring it into clear, concise presentations.

Given a transcription of spoken content, you will:
1. Identify the main topic
2. Extract key points (maximum 5-7 bullet points per slide)
3. Suggest a logical slide structure
4. Create a concise summary suitable for a PowerPoint presentation

Return your response as valid JSON in this exact format:
{
  "title": "Main presentation title",
  "subtitle": "Optional subtitle or presenter name placeholder",
  "slides": [
    {
      "title": "Slide title",
      "bullets": ["Point 1", "Point 2", "Point 3"],
      "notes": "Optional speaker notes for this slide"
    }
  ],
  "summary": "One paragraph executive summary of the entire content"
}

Keep bullet points concise (under 15 words each). Aim for 3-6 slides total."""


def summarize(transcription: str, api_key: str | None = None) -> dict:
    """
    Send transcription to Claude and get structured presentation data.
    Returns parsed JSON dict with title, slides, summary.
    """
    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    print("Sending to Claude for summarization...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Please analyze and structure the following transcription into a PowerPoint presentation:\n\n{transcription}",
            }
        ],
    )

    response_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(response_text)
