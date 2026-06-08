# run_agent_scheduled.py
# ─────────────────────────────────────────────────────────────────────────────
# Runs the actual ADK Agent programmatically (no UI, no CLI needed)
# GitHub Actions triggers this at 6:15 PM IST daily
# Auth: WIF → Vertex AI (Gemini) — no JSON key, no Gemini API key needed
# Flow: GitHub Actions → ADK Agent → Vertex AI Gemini → Tools → Slack
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta

# ── Read env vars ─────────────────────────────────────────────────────────────
GCP_PROJECT_ID   = os.environ.get("GCP_PROJECT_ID", "")
GCP_LOCATION     = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
SLACK_BOT_TOKEN  = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID", "")

if not GCP_PROJECT_ID:
    print("❌ GCP_PROJECT_ID not set.", file=sys.stderr)
    sys.exit(1)

# ── Configure ADK to use Vertex AI (WIF OAuth token) ─────────────────────────
# No API key needed — WIF credentials authenticate to Vertex AI automatically
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GOOGLE_CLOUD_PROJECT"]      = GCP_PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"]     = GCP_LOCATION

# ── IST timestamp ─────────────────────────────────────────────────────────────
now_ist   = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
timestamp = now_ist.strftime("%d-%b-%Y %I:%M %p IST")

print("=" * 65)
print(f"🤖 ADK Agent Scheduled Run")
print(f"   Project   : {GCP_PROJECT_ID}")
print(f"   Location  : {GCP_LOCATION}")
print(f"   Time      : {timestamp}")
print(f"   Model     : gemini-2.5-flash-lite (via Vertex AI)")
print(f"   Auth      : WIF → Vertex AI ✅ (no API key needed)")
print(f"   Trigger   : GitHub Actions Cron (6:15 PM IST daily)")
print("=" * 65)

# ── Import ADK after env vars are set ────────────────────────────────────────
try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai.types import Content, Part
    print("   ✅ ADK imported successfully")
except ImportError as e:
    print(f"❌ ADK import failed: {e}", file=sys.stderr)
    sys.exit(1)

# ── Import the root agent ─────────────────────────────────────────────────────
try:
    from agent.agent import root_agent
    print(f"   ✅ Agent loaded: {root_agent.name}")
    print(f"   ✅ Model      : {root_agent.model}")
    print(f"   ✅ Tools      : {len(root_agent.tools)} tools registered")
except Exception as e:
    print(f"❌ Agent import failed: {e}", file=sys.stderr)
    sys.exit(1)


async def run_agent_pipeline():
    """Runs the ADK agent with the full pipeline prompt."""

    prompt = f"""
Run the full VM inventory pipeline for project: {GCP_PROJECT_ID}

Please execute all steps in sequence:
1. Fetch VM inventory for {GCP_PROJECT_ID}
2. Run health check on the generated Excel file
3. Push the inventory data to BigQuery
4. Send a Slack notification with the health summary and Excel report

This is an automated daily run triggered at {timestamp}.
"""

    print(f"\n📝 Prompt sent to ADK Agent:")
    print(f"   {prompt.strip()[:120]}...")

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="gcp-vm-inventory-agent",
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="gcp-vm-inventory-agent",
        user_id="github-actions-scheduler",
    )

    print(f"\n🔗 ADK Session: {session.id}")
    print(f"   Gemini (Vertex AI) orchestrating pipeline...\n")

    message = Content(
        role="user",
        parts=[Part(text=prompt)]
    )

    final_response = ""
    tool_calls     = []

    try:
        async for event in runner.run_async(
            user_id="github-actions-scheduler",
            session_id=session.id,
            new_message=message,
        ):
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        tool_name = part.function_call.name
                        tool_calls.append(tool_name)
                        print(f"   🔧 Tool called: {tool_name}")
                    if hasattr(part, 'function_response') and part.function_response:
                        tool_name = part.function_response.name
                        response  = str(part.function_response.response)
                        print(f"   ✅ Tool done  : {tool_name}")
                        print(f"      {response[:120]}")

            if hasattr(event, 'is_final_response') and event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text

    except Exception as e:
        print(f"\n❌ Agent error: {e}", file=sys.stderr)
        _send_failure_alert(str(e), timestamp)
        sys.exit(1)

    print("\n" + "=" * 65)
    print("✅ ADK Agent completed successfully!")
    print(f"   Tools used : {' → '.join(tool_calls)}")
    print(f"   Response   : {final_response[:300]}")
    print("=" * 65)


def _send_failure_alert(error: str, timestamp: str):
    """Sends Slack failure alert if agent crashes."""
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        return
    try:
        from slack_sdk import WebClient
        client = WebClient(token=SLACK_BOT_TOKEN)
        client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text="❌ ADK Agent Scheduled Run FAILED",
            blocks=[
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "❌ ADK Agent Failed", "emoji": True}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"🏢 *Project*\n{GCP_PROJECT_ID}"},
                        {"type": "mrkdwn", "text": f"⏱️ *Time*\n{timestamp}"},
                        {"type": "mrkdwn", "text": f"🤖 *Model*\ngemini-2.5-flash-lite (Vertex AI)"},
                        {"type": "mrkdwn", "text": f"❌ *Error*\n```{error[:200]}```"},
                    ]
                }
            ]
        )
    except Exception as e:
        print(f"   ⚠️  Slack alert failed: {e}")


if __name__ == "__main__":
    asyncio.run(run_agent_pipeline())
