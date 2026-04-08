import json
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from agent.browser import BrowserController

load_dotenv(override=True)

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a browser automation agent. You see a screenshot of a web page and must decide the single next action to complete the given task.

Respond ONLY with a valid JSON object in this exact schema:
{
  "observation": "<what you see on screen right now>",
  "reasoning": "<why this is the next best action>",
  "action": "<one of: click | click_selector | type | fill | scroll | press | navigate | extract | done>",
  "params": {
    // for click:          { "x": int, "y": int, "description": "what you're clicking" }
    // for click_selector: { "selector": "css selector", "description": "what you're clicking" }
    // for type:           { "text": "text to type" }
    // for fill:           { "selector": "css selector", "text": "value" }
    // for scroll:         { "direction": "down" | "up" }
    // for press:          { "key": "Enter" | "Tab" | "Escape" | etc }
    // for navigate:       { "url": "https://..." }
    // for extract:        { "result": "the final answer to the task" }
    // for done:           { "result": "the final answer to the task" }
  }
}

General rules:
- Only ONE action per response.
- If the task is complete, use action "done" with the answer in params.result.
- If you need to extract specific data from the page, use "extract" and put the answer in params.result.
- Never guess URLs — only navigate to URLs you can see on screen or that are given in the task.
- Prefer fill+selector over click+coords when interacting with form inputs.
- If you see a cookie/consent banner or GDPR dialog, click the accept/agree button FIRST before doing anything else.
- If you see a Cloudflare or security challenge page, use action "scroll" (direction: down) to wait and let it resolve — do NOT declare done.
- If the page appears blank or still loading, use action "scroll" (direction: down) to trigger rendering — do NOT declare done.
- NEVER use action "done" with an error message — only use "done" when you have the actual answer to the task.

Filter / search form rules:
- Prefer click_selector over click+coords when opening filter sections — it is more reliable. For AutoScout24's price filter try: click_selector with selector "button[data-testid*='price']", or "button:has-text('Preis')", or "[aria-label*='Preis']".
- On AutoScout24, filter sections (Preis, Kilometerstand, etc.) open as FULL-SCREEN OVERLAY PANELS when clicked. Inside the overlay you will see min/max input fields and a large button at the bottom showing "X Angebote anzeigen". Fill the input fields, then click_selector that button to apply and return to results.
- Inside an open price filter overlay, try fill with selector "input[data-testid*='price-max']", "input[placeholder*='bis']", or "input[name*='price']" for the max price field.
- If an unexpected overlay is blocking the page, press Escape to close it before continuing.
- After applying a filter, the result count appears as "X Angebote" near the top. Extract that number.

Contact form rules:
- If the task says "Do NOT click send / Senden / Absenden": fill every requested field using the fill action, then use "extract" to return the answer. Never click the submit button.
- Fill form fields one at a time. Try these selectors in order: input[name="name"], input[placeholder*="Name"], then input[type="email"], input[name="email"], then input[type="tel"], input[name="phone"], then textarea for the message.
- After filling all fields, note the seller or dealer name visible on the page (usually shown near the listing title or in the contact panel) and use extract to return it.
"""


def analyze_screen(
    screenshot_bytes: bytes,
    task: str,
    action_history: list[dict],
) -> dict:
    """
    Send a screenshot + task context to GPT-4o and get back a structured action.

    Returns a dict with keys: observation, reasoning, action, params
    """
    history_text = _format_history(action_history)

    user_content = [
        {
            "type": "text",
            "text": (
                f"TASK: {task}\n\n"
                f"ACTIONS TAKEN SO FAR ({len(action_history)}):\n{history_text}\n\n"
                "What is the single next action to take?"
            ),
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{BrowserController.to_base64(screenshot_bytes)}",
                "detail": "high",
            },
        },
    ]

    logger.debug("Sending screenshot to GPT-4o (history length=%d)", len(action_history))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        max_tokens=500,
        temperature=0.2,
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)
    result = _validate(parsed)
    logger.debug("GPT-4o decided: action=%s reasoning=%s", result["action"], result.get("reasoning", "")[:100])
    return result


# --- Helpers ---

def _format_history(history: list[dict]) -> str:
    if not history:
        return "None"
    recent = history[-3:]  # only last 3 to avoid bloating the prompt
    lines = []
    for i, h in enumerate(recent, 1):
        lines.append(f"{i}. action={h.get('action')} params={h.get('params')}")
    return "\n".join(lines)


def _validate(parsed: dict) -> dict:
    required = {"observation", "reasoning", "action", "params"}
    missing = required - parsed.keys()
    if missing:
        raise ValueError(f"GPT-4o response missing fields: {missing}. Got: {parsed}")

    valid_actions = {"click", "click_selector", "type", "fill", "scroll", "press", "navigate", "extract", "done"}
    if parsed["action"] not in valid_actions:
        raise ValueError(f"Unknown action: {parsed['action']}")

    return parsed
