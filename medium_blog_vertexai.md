# I Upgraded My GCP VM Inventory AI Agent to Run Automatically Every Day - Vertex AI, Workload Identity Federation, and GitHub Actions: Zero Stored Credentials

**Bikram Singh**

---

## 🌐 Live Repository

🔗 **GitHub:** [github.com/bikram-singh/gcp-inventory-agent-vertexai](https://github.com/bikram-singh/gcp-inventory-agent-vertexai)

📖 **Previous article (Gemini API Key version):** [AI Agent That Fetch Entire GCP VM Inventory](https://medium.com/@bikram23march/ai-agent-that-fetch-entire-gcp-vm-inventory-de37c4790729)

---

## 🌟 Introduction

In my previous article, I built a GCP VM Inventory AI Agent using Google ADK and the Gemini API Key. It worked - scan VMs, check health, push to BigQuery, send a Slack report - all from a single natural language command in the ADK Web UI.

But it had two problems I wasn't happy with:

**Problem 1 - It required a Gemini API Key stored in a `.env` file.** In GitHub Actions, this meant storing a long-lived credential in GitHub Secrets. Not ideal.

**Problem 2 - It required a human to trigger it.** Every Monday morning I still had to open the ADK Web UI and type the command. The whole point was to eliminate manual work.

So I rebuilt it - properly this time.

This article covers the upgraded version:

🔐 **Vertex AI** instead of Gemini API Key - authentication flows through Workload Identity Federation, same OAuth token that already authenticates all GCP API calls  
🤖 **Same ADK Agent, same 5 tools** - nothing changed in the agent logic  
⏰ **GitHub Actions cron** - runs automatically every day at 2:00 PM IST  
🔑 **Zero stored credentials** - no JSON keys, no API keys, no `.env` in CI/CD  

The agent now wakes up every afternoon, scans your infrastructure, checks for issues, updates BigQuery, and drops a formatted report in Slack - without you touching anything.

---

## 🎯 What Changed vs the Previous Version

| Feature | Gemini API Version | Vertex AI Version (this article) |
|---|---|---|
| **LLM Auth** | Gemini API Key | WIF OAuth token |
| **Stored secrets** | API Key in `.env` | None |
| **Trigger** | Manual (ADK Web UI) | Automated daily + manual |
| **LLM endpoint** | `generativelanguage.googleapis.com` | `aiplatform.googleapis.com` |
| **Security** | API key risk | Zero stored credentials |
| **CI/CD** | Not scheduled | GitHub Actions cron ✅ |
| **Key file** | `adc-credentials.json` needed locally | WIF handles everything |

Everything else - the 5 tools, the 26-column Excel report, BigQuery schema, Slack Block Kit format, Looker Studio dashboard - stays exactly the same.

---

## 🏛️ Architecture

```
GitHub Actions (Cron: 2:00 PM IST daily)        Developer / Operator
              │                                           │
              │ run_agent_scheduled.py          ADK Web UI :8080
              ↓                                           ↓
        WIF Auth                                    WIF Auth
        OAuth token                                 OAuth token
              │                                           │
              └───────────────┬───────────────────────────┘
                              ↓
                    ADK Root Agent (agent.py)
                    Gemini 2.5 Flash Lite
                    via Vertex AI
                              │
              ┌───────────────┼───────────────────┐
              ↓               ↓                   ↓               ↓
    fetch_vm_inventory  check_vm_health  push_to_bigquery  send_slack
              │               │                   │               │
              ↓               ↓                   ↓               ↓
        GCP APIs         Excel .xlsx          BigQuery         Slack
        Compute Engine   (read + flag)        vm_details    Block Kit
        Monitoring                            partitioned   Excel file
        Resource Manager
        Guest Attributes
              │
              ↓
        gcp_vm_inventory.py
        26 fields per VM
              │
              ↓
        Excel Report (.xlsx)
              │
        ┌─────┴─────┐
        ↓           ↓
   BigQuery       Slack
        │
        ↓
  Looker Studio
  Dashboard
```

### 🔄 Full Pipeline Flow

```
Step 1  fetch_vm_inventory         →  Scan GCP · Collect 26 fields · Export .xlsx
Step 2  check_vm_health            →  Read .xlsx · Flag CPU/Backup/Idle issues
Step 3  push_inventory_to_bigquery →  Deduplicate · Append date partition to BQ
Step 4  send_slack_notification    →  Rich Block Kit message · Upload .xlsx to Slack
```

---

## 🔐 Why Vertex AI Instead of Gemini API Key

This is the most important architectural decision in this upgrade.

The original version used:
```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=AIza...
```

The problem: GitHub Actions with Workload Identity Federation sets `GOOGLE_APPLICATION_CREDENTIALS` automatically. When ADK sees this environment variable, it tries to use the WIF OAuth token to call the Gemini API - which rejects it because the Gemini API only accepts API Keys, not OAuth tokens.

This caused a persistent `401 UNAUTHENTICATED: ACCESS_TOKEN_TYPE_UNSUPPORTED` error.

The fix is simple and correct:

```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

Vertex AI accepts WIF OAuth tokens natively. The same credential that authenticates Compute Engine, BigQuery, and Cloud Monitoring API calls now also authenticates Gemini - through a single unified auth flow.

```
WIF OIDC token (generated per GitHub Actions run)
      ↓
GCP validates → issues OAuth token
      ↓
Works for ALL services in one token:
├── Compute Engine API  ✅
├── Cloud Monitoring    ✅
├── Resource Manager    ✅
├── BigQuery            ✅
└── Vertex AI (Gemini)  ✅  ← new
```

---

## 🏗️ GCP Setup - Additional Steps for Vertex AI

If you already have the previous version set up, you only need two additional commands.

### Enable Vertex AI API

```bash
gcloud services enable aiplatform.googleapis.com \
  --project=YOUR_PROJECT_ID
```

### Grant Vertex AI Role to Service Account

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Grant WIF Binding for the New Repo

Each GitHub repository needs its own WIF binding. Run once per repo:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-deploy@YOUR_PROJECT.iam.gserviceaccount.com \
  --project=YOUR_PROJECT_ID \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/attribute.repository/bikram-singh/gcp-inventory-agent-vertexai"
```

### Full IAM Roles Required

| Role | Purpose |
|---|---|
| `roles/compute.viewer` | Read VMs, disks, machine types, snapshots |
| `roles/monitoring.viewer` | Read CPU and RAM metrics |
| `roles/resourcemanager.organizationViewer` | Read org domain |
| `roles/bigquery.dataEditor` | Write rows to BigQuery |
| `roles/bigquery.jobUser` | Run BigQuery load jobs |
| `roles/aiplatform.user` | Call Vertex AI Gemini models ← new |
| `roles/iam.workloadIdentityUser` | Allow WIF authentication |

---

## 📁 Repository Structure

```
gcp-inventory-agent-vertexai/
│
├── 📁 .github/
│   └── 📁 workflows/
│       └── 📄 daily_adk_agent.yml      # GitHub Actions cron - 2:00 PM IST
│
├── 📁 agent/
│   ├── 📄 __init__.py                  # ADK module entry point
│   ├── 📄 agent.py                     # Root ADK agent - Vertex AI model
│   └── 📄 tools.py                     # All 5 tools (unchanged)
│
├── 📁 docs/snapshots/                  # Screenshots
│
├── 📄 gcp_vm_inventory.py              # Core inventory script (unchanged)
├── 📄 push_to_bigquery.py              # BigQuery push (unchanged)
├── 📄 run_agent_scheduled.py           # NEW - runs ADK agent programmatically
├── 📄 adk_vertex_ai_architecture.svg   # Architecture diagram
├── 📄 requirements.txt
└── 📄 README.md
```

The only new files compared to the previous version are:
- `run_agent_scheduled.py` - the headless pipeline runner
- `.github/workflows/daily_adk_agent.yml` - the GitHub Actions workflow

---

## 🤖 The Key Change - `agent/agent.py`

The agent definition changes by one environment variable check:

```python
# agent/agent.py
import os
from google.adk.agents import Agent
from agent.tools import (
    fetch_vm_inventory,
    fetch_multi_project_inventory,
    check_vm_health,
    push_inventory_to_bigquery,
    send_slack_notification,
)

# Auto-detect Vertex AI vs Gemini API Key based on env var
USE_VERTEXAI = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
MODEL = "gemini-2.5-flash-lite"

root_agent = Agent(
    name="agent",
    model=MODEL,
    description=(
        "A GCP infrastructure assistant that fetches VM inventory, "
        "runs health checks, pushes data to BigQuery, and sends Slack reports."
    ),
    instruction="""
You are a GCP infrastructure assistant specialising in VM inventory management.

RECOMMENDED FULL WORKFLOW:
   Step 1 → fetch_vm_inventory(project_id)
   Step 2 → check_vm_health(project_id)
   Step 3 → push_inventory_to_bigquery(project_id)
   Step 4 → send_slack_notification(project_id, counts from step 2)
""",
    tools=[
        fetch_vm_inventory,
        fetch_multi_project_inventory,
        check_vm_health,
        push_inventory_to_bigquery,
        send_slack_notification,
    ],
)
```

When `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, ADK automatically routes all LLM calls through `aiplatform.googleapis.com` using the ambient credentials - which in GitHub Actions means the WIF OAuth token.

---

## 🆕 The New File - `run_agent_scheduled.py`

This is the bridge between GitHub Actions and the ADK agent. It runs the agent programmatically - no web UI, no CLI, no interactive session.

```python
# run_agent_scheduled.py
import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta

# Read env vars
GCP_PROJECT_ID   = os.environ.get("GCP_PROJECT_ID", "")
GCP_LOCATION     = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
SLACK_BOT_TOKEN  = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID", "")

# Configure Vertex AI BEFORE importing ADK
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GOOGLE_CLOUD_PROJECT"]      = GCP_PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"]     = GCP_LOCATION

# IST timestamp
now_ist   = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
timestamp = now_ist.strftime("%d-%b-%Y %I:%M %p IST")

# Import ADK AFTER env vars are set
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from agent.agent import root_agent


async def run_agent_pipeline():
    """Runs the ADK agent programmatically - same as typing in the Web UI."""

    prompt = f"""
Run the full VM inventory pipeline for project: {GCP_PROJECT_ID}

Please execute all steps in sequence:
1. Fetch VM inventory for {GCP_PROJECT_ID}
2. Run health check on the generated Excel file
3. Push the inventory data to BigQuery
4. Send a Slack notification with the health summary and Excel report

This is an automated daily run triggered at {timestamp}.
"""

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

    message = Content(role="user", parts=[Part(text=prompt)])

    tool_calls = []
    async for event in runner.run_async(
        user_id="github-actions-scheduler",
        session_id=session.id,
        new_message=message,
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    print(f"   🔧 Tool called: {part.function_call.name}")
                    tool_calls.append(part.function_call.name)
                if hasattr(part, 'function_response') and part.function_response:
                    print(f"   ✅ Tool done  : {part.function_response.name}")


if __name__ == "__main__":
    asyncio.run(run_agent_pipeline())
```

Notice the critical ordering: environment variables are set **before** importing ADK. This is essential - ADK reads credentials at import time, not at runtime.

---

## 🔄 GitHub Actions Workflow - `daily_adk_agent.yml`

```yaml
# .github/workflows/daily_adk_agent.yml
name: Daily ADK Agent Pipeline

on:
  schedule:
    - cron: "30 8 * * *"    # 2:00 PM IST daily

  workflow_dispatch:
    inputs:
      project_id:
        description: "GCP Project ID (leave blank to use default)"
        required: false
        default: ""

permissions:
  contents: read
  id-token: write            # Required for WIF

jobs:
  run-adk-agent:
    name: Run ADK Agent
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      # WIF auth - one token covers GCP APIs + Vertex AI
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WIF_PROVIDER_NONPROD }}
          service_account: ${{ secrets.GCP_WIF_SERVICE_ACCOUNT_NONPROD }}

      - name: Set up gcloud CLI
        uses: google-github-actions/setup-gcloud@v2

      - name: Determine Project ID
        id: project
        run: |
          if [ -n "${{ github.event.inputs.project_id }}" ]; then
            echo "PROJECT_ID=${{ github.event.inputs.project_id }}" >> $GITHUB_OUTPUT
          else
            echo "PROJECT_ID=${{ secrets.GCP_PROJECT_ID }}" >> $GITHUB_OUTPUT
          fi

      - name: Run ADK Agent (Vertex AI + Tools)
        env:
          GOOGLE_GENAI_USE_VERTEXAI: "TRUE"
          GOOGLE_CLOUD_PROJECT: ${{ steps.project.outputs.PROJECT_ID }}
          GOOGLE_CLOUD_LOCATION: "us-central1"
          GCP_PROJECT_ID: ${{ steps.project.outputs.PROJECT_ID }}
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_CHANNEL_ID: ${{ secrets.SLACK_CHANNEL_ID }}
        run: python run_agent_scheduled.py

      - name: Upload Excel report as artifact
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: adk-vm-inventory-${{ steps.project.outputs.PROJECT_ID }}-${{ github.run_id }}
          path: "*.xlsx"
          retention-days: 30
          if-no-files-found: warn
```

**Key points:**

`cron: "30 8 * * *"` = **2:00 PM IST (8:30 AM UTC)** - IST is UTC+5:30, so subtract 5h30m.

`GOOGLE_GENAI_USE_VERTEXAI: "TRUE"` - this single env var switches ADK from Gemini API to Vertex AI.

No `GOOGLE_API_KEY` anywhere - WIF handles everything.

---

## 🔑 GitHub Secrets Required

Go to repo → **Settings** → **Secrets and variables** → **Actions**:

| Secret | Value |
|---|---|
| `GCP_PROJECT_ID` | `your-project-id` |
| `GCP_WIF_PROVIDER_NONPROD` | `projects/NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER` |
| `GCP_WIF_SERVICE_ACCOUNT_NONPROD` | `github-actions-deploy@project.iam.gserviceaccount.com` |
| `SLACK_BOT_TOKEN` | `xoxb-your-token` |
| `SLACK_CHANNEL_ID` | `C0XXXXXXXXX` |

No `GOOGLE_API_KEY` needed. That's the whole point.

---

## ⚠️ Challenges and Solutions

### Challenge 1 - 401 UNAUTHENTICATED on Gemini API

```
google.genai.errors.ClientError: 401 UNAUTHENTICATED
reason: ACCESS_TOKEN_TYPE_UNSUPPORTED
```

**Cause:** WIF sets `GOOGLE_APPLICATION_CREDENTIALS` with an OAuth token. ADK passed this OAuth token to the Gemini API which only accepts API Keys.

**Fix:** Switch to Vertex AI - it accepts OAuth tokens natively.

---

### Challenge 2 - Import order matters

Even after switching to Vertex AI, the error persisted because ADK was reading credentials at import time:

```python
# WRONG - ADK imports before env vars are set
from google.adk.runners import Runner
from agent.agent import root_agent

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"  # Too late
```

```python
# CORRECT - set env vars first, then import
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"   # First
os.environ["GOOGLE_CLOUD_PROJECT"]      = project_id

from google.adk.runners import Runner               # Then import
from agent.agent import root_agent
```

---

### Challenge 3 - GitHub Actions cron not triggering

After pushing the workflow file, the scheduled trigger wasn't firing. Root cause: when a commit-pushed workflow run fails, GitHub suspends the schedule for that workflow.

**Fix:**
1. Delete all failed workflow runs from GitHub Actions history
2. Disable the workflow → wait 30 seconds → enable it
3. Push a clean commit - if the commit-triggered run succeeds, the schedule registers correctly

**Important:** GitHub cron schedules can be delayed by up to 60 minutes during peak UTC hours. `30 8 * * *` (2 PM IST = 8:30 AM UTC) is a relatively quiet time and fires reliably.

---

### Challenge 4 - Org policy blocks JSON key creation

```
ERROR: FAILED_PRECONDITION: Key creation is not allowed on this service account.
constraints/iam.disableServiceAccountKeyCreation
```

This was actually the org policy doing its job - enforcing the "no JSON keys" policy that makes WIF necessary in the first place. The solution was to use Vertex AI + WIF instead of trying to create a JSON key.

---

## 💬 What the Scheduled Run Looks Like

At 2:00 PM IST every day, GitHub Actions fires automatically. The logs show:

```
✅ ADK imported successfully
✅ Agent loaded: agent | Model: gemini-2.5-flash-lite | Tools: 5
🔗 ADK Session: a31608fb-d609-494e-8b73-d1b693f90517
   Gemini (Vertex AI) orchestrating pipeline...

   🔧 Tool called: fetch_vm_inventory
   ✅ Tool done  : fetch_vm_inventory
   🔧 Tool called: check_vm_health
   ✅ Tool done  : check_vm_health
   🔧 Tool called: push_inventory_to_bigquery
   ✅ Tool done  : push_inventory_to_bigquery
   🔧 Tool called: send_slack_notification
   ✅ Tool done  : send_slack_notification

✅ ADK Agent completed successfully!
   Tools used : fetch_vm_inventory → check_vm_health →
                push_inventory_to_bigquery → send_slack_notification
```

And Slack receives:

```
📊 GCP VM Inventory Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 Project    dhg-vaccine-rateauto-nonpord
🌍 Domain     gcpcloudhub.shop
⏱️ Generated  08-Jun-2026 02:01 PM IST
📎 Report     dhg-vaccine-rateauto-nonpord-vms.xlsx

📈 VM Summary
🖥️ Total: 3    ✅ Running: 1    ■ Stopped: 2    🔄 Healthy: 3

🏥 Health Check
💤 Idle/Stopped : 2 VM(s)

🤖 Daily Automated Report | GCP VM Inventory Bot | Powered by Google ADK + Gemini
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📎 dhg-vaccine-rateauto-nonpord-vms.xlsx   [Excel Spreadsheet]
```

---

## 🔍 End-to-End Verification

After setup, verify each component:

**GitHub Actions:**
```
Actions → Daily ADK Agent Pipeline → Run #1 ✅ Success
```

**BigQuery:**
```sql
SELECT * FROM `your-project.vm_inventory.vm_details`
WHERE snapshot_date = CURRENT_DATE()
```

**Slack:**
Check `#gcm-vm-inventory` - report should appear within 2 minutes of the cron trigger.

**Looker Studio:**
Open your dashboard - scorecards should reflect today's data. Remember to set the Date Range Control to **This week** so today's data is included.

---

## 🎯 Key Design Decisions

### 1. Vertex AI over Gemini API Key

The Gemini API Key approach works fine for local development. The moment you add WIF to the picture, the credentials conflict. Vertex AI eliminates the conflict entirely by accepting the same OAuth token that all other GCP services use.

### 2. Environment variables before imports

ADK initialises its credential chain at import time. Setting `GOOGLE_GENAI_USE_VERTEXAI=TRUE` after importing ADK has no effect. This is not documented clearly - it took several failed runs to discover.

### 3. No push trigger in the workflow

The workflow only has `schedule` and `workflow_dispatch` triggers - no `push`. Adding a `push` trigger means every git commit fires the agent. When those commit-triggered runs fail (due to missing env vars or transient errors), GitHub suspends the schedule. Keeping the workflow to schedule-only prevents this entirely.

### 4. Set environment variables before ADK imports

```python
# Always do this first - before any ADK import
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GOOGLE_CLOUD_PROJECT"]      = project_id
os.environ["GOOGLE_CLOUD_LOCATION"]     = "us-central1"

# Then import
from google.adk.runners import Runner
from agent.agent import root_agent
```

---

## 🎯 Conclusion

The upgrade from Gemini API Key to Vertex AI + WIF is the right architectural choice for production. The agent now runs on a schedule with zero manual intervention and zero stored credentials.

Here's what the full system delivers every day at 2:00 PM IST without anyone touching a keyboard:

✅ **Scans all GCP VMs** across all zones in the project  
✅ **Flags health issues** - no backup, high CPU, idle VMs  
✅ **Updates BigQuery** - Looker Studio dashboard refreshes automatically  
✅ **Sends Slack report** - full summary + Excel attachment in the team channel  
✅ **Zero credentials stored** - WIF tokens expire when the job ends  
✅ **Gemini orchestrates the tools** - the real ADK agent, not just a Python script  

The two repos serve different purposes:

`gcp-vm-inventory-agent` - for local development and interactive use via ADK Web UI with Gemini API Key.

`gcp-inventory-agent-vertexai` - for production automated scheduling with Vertex AI and WIF. No API keys. No stored secrets. Runs itself.

The full source code for this version is at:

**[github.com/bikram-singh/gcp-inventory-agent-vertexai](https://github.com/bikram-singh/gcp-inventory-agent-vertexai)**

---

*If you haven't read the original article building the base agent, start there first - this article assumes familiarity with the agent architecture and tools.*

📖 **Part 1:** [AI Agent That Fetch Entire GCP VM Inventory](https://medium.com/@bikram23march/ai-agent-that-fetch-entire-gcp-vm-inventory-de37c4790729)

---

**Tags:** `Google Cloud` · `Vertex AI` · `AI Agents` · `Google ADK` · `GitHub Actions` · `DevOps` · `Python` · `BigQuery` · `Workload Identity Federation` · `Slack` · `Infrastructure Automation` · `GCP` · `Zero Trust`
