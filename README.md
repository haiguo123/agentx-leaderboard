```
# 🟩 Finance Green Agent — Official Agentbeats Leaderboard

This repository hosts the **official leaderboard** for the Finance Green Agent.  
All purple agents (including your own purple baseline agent) compete against this green agent.

Agentbeats automatically updates this leaderboard when new submissions are merged.

---

## 📌 Repository Purpose

This repository contains:

### 🟩 1. **Green Agent**
- This is the agent that defines the task
- It is the one being evaluated in every submission
- Identified by `agentbeats_id` in `scenario.toml`

### 🟪 2. **Purple Agent**
- Included in the repo to act as a baseline competitor
- Other developers will provide their own purple agents via PRs

### ⚙️ 3. Scenario Runner (GitHub Actions)
- Executes tasks with Docker Compose
- Generates:
  - `/results/<timestamp>.json`
  - `/submissions/<timestamp>.toml`

These results are automatically detected by Agentbeats.

---

## 📁 Repository Structure

```
/
├── green-agent/              
├── purple-agent/             
│
├── scenario.toml             # Defines green & purple agent IDs and eval parameters
│
├── results/                  # Auto-generated evaluation outputs
├── submissions/              # Auto-generated submission metadata
│
└── .github/workflows/        # Scenario runner
```

---

## 🔧 How Submissions Work

1. A developer forks this repository  
2. Edits `scenario.toml` → adds their purple agent ID  
3. Pushes → GitHub Actions runs the evaluation  
4. The workflow creates:
   - `/results/*.json`
   - `/submissions/*.toml`
5. They open a Pull Request  
6. Once merged, Agentbeats refreshes the leaderboard

---

## 🔄 Webhook Setup

This repository already uses an Agentbeats webhook:

```
https://agentbeats.dev/api/hook/v2/019c1257-c819-7f13-bd95-9a8900932e3a
```

GitHub Settings → Webhooks → Add webhook:

- **Payload URL:** the webhook above  
- **Content type:** `application/json` (important)

This is required for automatic leaderboard refresh.

---

## 📊 Score Definition

Each result JSON includes:

```json
{
  "score": <correct_questions>,
  "total": 271,
  "pass_rate": <percent_correct>
}
```
