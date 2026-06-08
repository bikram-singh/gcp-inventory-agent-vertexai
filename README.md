<div align="center">

# 🤖 GCP VM Inventory Agent - Vertex AI Edition

### AI-Powered Infrastructure Monitoring · Google ADK · Vertex AI · BigQuery · Slack · GitHub Actions

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Google ADK](https://img.shields.io/badge/Google_ADK-2.1.0-4285F4?logo=google&logoColor=white)](https://google.github.io/adk-docs/)
[![Vertex AI](https://img.shields.io/badge/Vertex_AI-Gemini_2.5_Flash_Lite-8E44AD?logo=google-cloud&logoColor=white)](https://cloud.google.com/vertex-ai)
[![BigQuery](https://img.shields.io/badge/BigQuery-Enabled-34A853?logo=google-cloud&logoColor=white)](https://cloud.google.com/bigquery)
[![Slack](https://img.shields.io/badge/Slack-Notifications-4A154B?logo=slack&logoColor=white)](https://slack.com)
[![GitHub Actions](https://img.shields.io/badge/Scheduled-2:00_PM_IST_Daily-2088FF?logo=github-actions&logoColor=white)](https://github.com/bikram-singh/gcp-inventory-agent-vertexai/actions)
[![WIF](https://img.shields.io/badge/Auth-Workload_Identity_Federation-FF6D00?logo=googlecloud&logoColor=white)](https://cloud.google.com/iam/docs/workload-identity-federation)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

*An AI-powered GCP VM inventory agent built with Google ADK and Vertex AI. Scans all virtual machines across GCP projects, performs health checks, pushes data to BigQuery for historical analytics, and sends rich formatted reports to Slack - triggered automatically every day at 2:00 PM IST via GitHub Actions. Zero stored credentials - powered by Workload Identity Federation.*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Agent Tools](#-agent-tools)
- [Repository Structure](#-repository-structure)
- [Prerequisites](#-prerequisites)
- [GitHub Actions Setup](#-github-actions-setup)
- [VM Inventory Columns](#-vm-inventory-columns)
- [BigQuery Schema](#-bigquery-schema)
- [Slack Notifications](#-slack-notifications)
- [Looker Studio Dashboard](#-looker-studio-dashboard)
- [Scheduled Pipeline](#-scheduled-pipeline)
- [Snapshots](#-snapshots)
- [Repository](#-repository)

---

## 🌐 Overview

This is the **Vertex AI edition** of the GCP VM Inventory Agent. Unlike the original version which uses a Gemini API Key for local development, this edition uses **Vertex AI** for LLM inference - allowing the agent to authenticate entirely through **Workload Identity Federation (WIF)** with zero stored credentials.

The pipeline runs automatically every day at **2:00 PM IST** via GitHub Actions - no manual trigger needed.

### 🔑 Key Facts

| Property | Value |
|---|---|
| 🤖 **Agent Framework** | Google Agent Development Kit (ADK) 2.1.0 |
| 🧠 **LLM** | Gemini 2.5 Flash Lite via **Vertex AI** |
| ☁️ **Cloud Platform** | Google Cloud Platform |
| 🔐 **Authentication** | Workload Identity Federation (WIF) - zero JSON keys |
| 📊 **Analytics** | BigQuery + Looker Studio |
| 📢 **Notifications** | Slack (Block Kit rich messages) |
| 📁 **Output Format** | Excel (.xlsx) with styled status cells |
| 🐍 **Language** | Python 3.11+ |
| ⏰ **Scheduled Run** | GitHub Actions · Daily at 2:00 PM IST |
| 🔄 **CI/CD** | `daily_adk_agent.yml` · `run_agent_scheduled.py` |

### ✨ What It Does

| Capability | Description |
|---|---|
| 🔍 **VM Scanning** | Scans all zones across one or multiple GCP projects |
| 🏥 **Health Check** | Flags High CPU (>80%), No Backup, and Idle VMs |
| 📤 **Excel Export** | Generates a styled 26-column Excel report |
| 🗄️ **BigQuery Push** | Appends date-partitioned rows with automatic deduplication |
| 📊 **Dashboard** | Looker Studio dashboard auto-updates from BigQuery |
| 📣 **Slack Report** | Rich Block Kit message with VM summary and Excel attachment |
| ⏰ **Auto Schedule** | GitHub Actions cron - runs daily at 2:00 PM IST automatically |

---

## 🏛️ Architecture

![GCP VM Inventory Agent - Vertex AI Architecture](docs/snapshots/gcp_vm_agent_architecture.png)

> The diagram shows both trigger paths - GitHub Actions cron (automated) and Developer via ADK Web UI (manual) - converging at the ADK Agent which uses Vertex AI for LLM inference.

### 🔄 Layer Breakdown

| Layer | Components |
|---|---|
| **Trigger Layer** | GitHub Actions Cron (2:00 PM IST) · Developer / ADK Web UI |
| **Auth Layer** | Workload Identity Federation → OAuth token → Vertex AI + GCP APIs |
| **AI Agent Layer** | ADK Root Agent (`agent.py`) · Gemini 2.5 Flash Lite via Vertex AI |
| **GCP Services Layer** | Compute Engine API · Cloud Monitoring · Resource Manager API · Guest Attributes API |
| **Data Layer** | `gcp_vm_inventory.py` · Excel Report (.xlsx) · BigQuery (`vm_inventory.vm_details`) |
| **Visualization Layer** | Looker Studio Dashboard (connected to BigQuery) |
| **Notification Layer** | Slack Block Kit messages + Excel file attachment |

### 🔄 Full Pipeline Flow

```
Step 1  fetch_vm_inventory         →  Scan GCP · Collect 26 fields · Export .xlsx
Step 2  check_vm_health            →  Read .xlsx · Flag CPU/Backup/Idle issues
Step 3  push_inventory_to_bigquery →  Deduplicate · Append date partition to BQ
Step 4  send_slack_notification    →  Rich Block Kit message · Upload .xlsx to Slack
```

---

## 🛠️ Agent Tools

The agent exposes **5 tools** that Gemini (via Vertex AI) orchestrates automatically:

### 1️⃣ `fetch_vm_inventory`
Scans all zones in a single GCP project and exports a full VM inventory to Excel.

### 2️⃣ `fetch_multi_project_inventory`
Scans multiple GCP projects in sequence, generating one Excel file per project.

### 3️⃣ `check_vm_health`
Reads the Excel report and flags VMs with issues:

| Flag | Condition |
|---|---|
| ⚠️ **High CPU** | CPU utilization mean > 80% |
| ⚠️ **No Backup** | No snapshot configured |
| 💤 **Idle/Stopped** | Machine status is Stopped or Terminated |

### 4️⃣ `push_inventory_to_bigquery`
Pushes Excel data to BigQuery with date partitioning and automatic deduplication.

### 5️⃣ `send_slack_notification`
Sends a rich formatted Slack Block Kit message with VM summary and health flags, then uploads the Excel report as an attachment.

---

## 📁 Repository Structure

```
gcp-inventory-agent-vertexai/
│
├── 📁 .github/
│   └── 📁 workflows/
│       └── 📄 daily_adk_agent.yml      # GitHub Actions - 2:00 PM IST daily
│
├── 📁 agent/
│   ├── 📄 __init__.py                  # ADK module entry point
│   ├── 📄 agent.py                     # Root ADK agent - Vertex AI model + tools
│   └── 📄 tools.py                     # All 5 tool implementations
│
├── 📁 docs/
│   └── 📁 snapshots/                   # Screenshots and architecture diagram
│
├── 📄 gcp_vm_inventory.py              # Core inventory script (v6.0)
│                                       #   Compute Engine · Monitoring · Resource Manager
│
├── 📄 push_to_bigquery.py              # BigQuery push with schema + deduplication
├── 📄 run_agent_scheduled.py           # Scheduled pipeline - runs ADK agent via Python
├── 📄 adk_vertex_ai_architecture.svg  # Architecture diagram
├── 📄 requirements.txt                 # Python dependencies
└── 📄 README.md                        # This file
```

---

## ✅ Prerequisites

| Requirement | Details |
|---|---|
| 🐍 **Python** | 3.11 or higher |
| ☁️ **GCP Account** | With required APIs enabled |
| 🔐 **WIF Setup** | Workload Identity Federation configured |
| 💬 **Slack Workspace** | With a Bot Token |

### 🔌 GCP APIs Required

```bash
gcloud services enable \
  compute.googleapis.com \
  monitoring.googleapis.com \
  cloudresourcemanager.googleapis.com \
  bigquery.googleapis.com \
  aiplatform.googleapis.com \
  --project=YOUR_PROJECT_ID
```

### 🔐 IAM Roles Required for Service Account

| Role | Purpose |
|---|---|
| `roles/compute.viewer` | Read VM instances, disks, machine types |
| `roles/monitoring.viewer` | Read CPU and RAM metrics |
| `roles/resourcemanager.organizationViewer` | Read org domain |
| `roles/bigquery.dataEditor` | Write to BigQuery tables |
| `roles/bigquery.jobUser` | Run BigQuery jobs |
| `roles/aiplatform.user` | Call Vertex AI (Gemini) models |
| `roles/iam.workloadIdentityUser` | Allow WIF authentication |

---

## ⚙️ GitHub Actions Setup

### 🔑 Required GitHub Secrets

Go to repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret | Value |
|---|---|
| `GCP_PROJECT_ID` | `dhg-vaccine-rateauto-nonpord` |
| `GCP_WIF_PROVIDER_NONPROD` | `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER` |
| `GCP_WIF_SERVICE_ACCOUNT_NONPROD` | `github-actions-deploy@PROJECT.iam.gserviceaccount.com` |
| `SLACK_BOT_TOKEN` | `xoxb-your-token` |
| `SLACK_CHANNEL_ID` | `C0XXXXXXXXX` |

> **Note:** No `GOOGLE_API_KEY` needed - Vertex AI uses WIF OAuth token directly.

### 🔗 WIF Binding for This Repo

Run once in Cloud Shell to allow this repo to authenticate:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-deploy@YOUR_PROJECT.iam.gserviceaccount.com \
  --project=YOUR_PROJECT_ID \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/attribute.repository/bikram-singh/gcp-inventory-agent-vertexai"
```

### 🔐 Auth Flow

```
GitHub Actions
      ↓
WIF OIDC token (auto-generated per run)
      ↓
GCP validates → issues OAuth token
      ↓
Works for ALL services:
├── Compute Engine API  ✅
├── Cloud Monitoring    ✅
├── BigQuery            ✅
└── Vertex AI (Gemini)  ✅
```

No JSON keys. No stored credentials. Tokens expire when the job ends.

---

## 📊 VM Inventory Columns

The generated Excel report contains **26 columns**:

| # | Column | Source |
|---|---|---|
| 1 | Project ID | Input |
| 2 | VM Instance Name | Compute API |
| 3 | Machine Status | Compute API |
| 4 | Instance ID | Compute API |
| 5 | Domain | Resource Manager API |
| 6 | OS/Image | Compute API |
| 7 | Application Type | Derived |
| 8 | Environment | Derived |
| 9 | Machine Type | Compute API |
| 10 | vCPU | Machine Type API |
| 11 | RAM (GB) | Machine Type API |
| 12 | Hostname | Guest Attributes |
| 13 | Storage GB (Boot Disk) | Disks API |
| 14 | Internal IP | Network Interface |
| 15 | Storage Type | Disks API |
| 16 | Target Network Project | Network Interface |
| 17 | VPC Name | Network Interface |
| 18 | Subnet Name | Network Interface |
| 19 | External IP | Network Interface |
| 20 | Snapshots | Snapshots API |
| 21 | Snapshot Dates | Snapshots API |
| 22 | Snapshot Schedules | Resource Policies API |
| 23 | Uptime (W) | Compute API |
| 24 | CPU utilization [MEAN] | Cloud Monitoring API |
| 25 | RAM usage | Cloud Monitoring API |
| 26 | Health | Derived |

---

## 🗄️ BigQuery Schema

**Dataset:** `vm_inventory` · **Table:** `vm_details` · **Partitioned by:** `snapshot_date`

### Sample Queries

```sql
-- Today's VM inventory
SELECT vm_instance_name, machine_status, machine_type, vcpu, environment, health
FROM `your-project.vm_inventory.vm_details`
WHERE snapshot_date = CURRENT_DATE()
ORDER BY vm_instance_name;

-- VMs with no backup
SELECT DISTINCT vm_instance_name, project_id
FROM `your-project.vm_inventory.vm_details`
WHERE snapshots IS NULL
AND snapshot_date = CURRENT_DATE();

-- VM count trend over time
SELECT snapshot_date, COUNT(*) as vm_count
FROM `your-project.vm_inventory.vm_details`
GROUP BY snapshot_date
ORDER BY snapshot_date;
```

---

## 📣 Slack Notifications

```
📊 GCP VM Inventory Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 Project    dhg-vaccine-rateauto-nonpord
🌍 Domain     gcpcloudhub.shop
⏱️ Generated  08-Jun-2026 02:00 PM IST
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

## 📊 Looker Studio Dashboard

1. Go to **https://lookerstudio.google.com**
2. **Create** → **Data Source** → **BigQuery**
3. Select your project → `vm_inventory` → `vm_details`
4. Click **Connect** → **Create Report**

### Recommended Charts

| Chart | Dimension | Metric | Purpose |
|---|---|---|---|
| Scorecard | - | Record Count | Total VMs |
| Scorecard | `machine_status` Contains `Running` | Record Count | Running VMs |
| Scorecard | `machine_status` Contains `Stopped` | Record Count | Stopped VMs |
| Scorecard | `snapshots` Is null | Record Count | No Backup VMs |
| Bar chart | `machine_status` | Record Count | VM Status |
| Bar chart | `machine_type` | Record Count | By Machine Type |
| Table | All key fields | - | Full inventory |
| Time series | `snapshot_date` | Record Count | VM count over time |

> **Tip:** Add a **Date Range Control** at the top set to `This week` so all charts always show current data.

---

## ⏰ Scheduled Pipeline

### How It Works

```
GitHub Actions Cron (2:00 PM IST daily)
         ↓
run_agent_scheduled.py
         ↓
ADK Agent → Vertex AI (Gemini 2.5 Flash Lite)
         ↓
Gemini orchestrates all 4 tools:
   Step 1 → fetch_vm_inventory
   Step 2 → check_vm_health
   Step 3 → push_inventory_to_bigquery
   Step 4 → send_slack_notification
         ↓
Excel artifact saved in GitHub Actions (30 days)
Slack report delivered to #gcm-vm-inventory
BigQuery updated for Looker Studio dashboard
```

### Schedule Configuration

| Setting | Value |
|---|---|
| **IST Time** | 2:00 PM |
| **UTC Time** | 8:30 AM |
| **Cron** | `30 8 * * *` |
| **Days** | Every day |
| **Workflow file** | `.github/workflows/daily_adk_agent.yml` |

### Manual Trigger

To run immediately without waiting for the schedule:

1. Go to **GitHub → Actions → Daily ADK Agent Pipeline**
2. Click **Run workflow** → **Run workflow**

### Key Difference from Gemini API Version

| Feature | Gemini API Version | Vertex AI Version (this repo) |
|---|---|---|
| **Auth** | Gemini API Key | WIF OAuth token |
| **Stored secrets** | API Key in `.env` | None |
| **Trigger** | Manual (ADK Web UI) | Automated daily + manual |
| **LLM endpoint** | `generativelanguage.googleapis.com` | `aiplatform.googleapis.com` |
| **Security** | API key risk | Zero stored credentials |
| **CI/CD** | Not scheduled | GitHub Actions cron ✅ |

---

## 📸 Snapshots

### 1️⃣ ADK Web UI - Agent Running
![ADK Web UI](docs/snapshots/1_adk_web_ui.png)

---

### 2️⃣ Full Pipeline Execution - All 4 Tools Chained
![Full Pipeline](docs/snapshots/2_full_pipeline_execution.png)

---

### 3️⃣ Excel Report - VM Inventory (26 Columns)
![Excel Report](docs/snapshots/3_excel_report.png)

---

### 4️⃣ BigQuery Table - vm_details
![BigQuery Table](docs/snapshots/4_bigquery_table.png)

---

### 5️⃣ Slack Notification - Rich Block Kit Report + Excel Attachment
![Slack Notification](docs/snapshots/5_slack_notification.png)

---

### 6️⃣ Looker Studio Dashboard
![Looker Studio Dashboard](docs/snapshots/6_looker_studio_dashboard.png)

---

### 7️⃣ GitHub Actions - Daily Scheduled Run
![GitHub Actions](docs/snapshots/gcp_vm_agent_architecture.png)

---

## 🔗 Repository

| Repository | Purpose |
|---|---|
| [`gcp-inventory-agent-vertexai`](https://github.com/bikram-singh/gcp-inventory-agent-vertexai) | Vertex AI · WIF · GitHub Actions scheduler |

---

<div align="center">

**Maintained by Bikram Singh**

`dhg-vaccine-rateauto-nonpord` · `us-central1` · Google Cloud Platform

*Built with Google ADK · Vertex AI · BigQuery · Slack · GitHub Actions*

</div>
