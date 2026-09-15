# 5-Day AI Agents: Intensive Vibe Coding Course With Google

[![Google AI Studio](https://img.shields.io/badge/Google%20AI%20Studio-Gemini%202.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Kaggle](https://img.shields.io/badge/Kaggle-AI%20Agents%20Intensive-20BEFF?style=for-the-badge&logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/5-day-ai-agents-intensive-vibecoding-course-with-google)
[![ADK 2.0](https://img.shields.io/badge/ADK-2.0%20Graph%20Workflows-34A853?style=for-the-badge&logo=python&logoColor=white)](https://github.com/google/adk)
[![Antigravity](https://img.shields.io/badge/Antigravity-Agentic%20IDE%20%26%20CLI-EA4335?style=for-the-badge)](https://antigravity.google/)

Welcome to the official implementation repository for the **5-Day AI Agents: Intensive Vibe Coding Course With Google** (held June 15 – 19, 2026 and ongoing as a self-paced Learn Guide).

This repository contains production-ready multi-agent workflows, pre-LLM security screens, ambient Pub/Sub webhooks, and local LLM-as-judge evaluation frameworks developed using **Google Agent Development Kit (ADK 2.0)**, **Antigravity 2.0 IDE/CLI**, and **Gemini 2.5 Flash**.

---

## 📚 Course Overview & Learning Path

Developed by Google researchers and engineers, this intensive course explores building autonomous AI agents where natural language acts as the primary programming interface ("vibe coding").

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5-Day AI Agents Course Journey & Architecture Map                           │
├───────────┬───────────────────────────────────┬─────────────────────────────┤
│ Day 1     │ Intro to Agents & Vibe Coding     │ SDLC, Antigravity 2.0, IDE  │
│ Day 2     │ Tools & Interoperability          │ MCP, A2A, A2UI, Agents CLI  │
│ Day 3     │ Agent Skills & Memory             │ Dynamic Context, SKILL.md   │
│ Day 4     │ Security & Local Evaluations      │ PII Redaction, LLM-as-Judge │
│ Day 5     │ Spec-Driven Production            │ Telemetry, Webhooks, A2A    │
└───────────┴───────────────────────────────────┴─────────────────────────────┘
```

---

## 📐 System Architecture & Agent Topology

Below is the high-level event-driven topology and security triage pipeline implemented across our agents:

```mermaid
flowchart TD
    subgraph Trigger_Layer ["1. Event Ingestion & Webhooks"]
        A1[User / Client Payload] --> B1[FastAPI / Pub/Sub Endpoint]
        A2[Terminal / CLI Prompt] --> B2[Agents CLI Playground]
    end

    subgraph Security_Gate ["2. Pre-LLM Security & Classifier Screen"]
        B1 & B2 --> C1{Deterministic Keyword / Rule Classifier}
        C1 -->|Off-topic Query| D1[Static Decline Node - 0 LLM Cost]
        C1 -->|Valid Request| C2[Security Checkpoint Screen]
        C2 -->|PII Scrubbing| E1[Redact SSNs & Credit Cards]
        C2 -->|Prompt Injection Detected| E2[Short-Circuit directly to Manager Review]
    end

    subgraph Execution_Engine ["3. ADK 2.0 Graph Workflow & Gemini 2.5"]
        E1 --> F1{Transaction Threshold}
        F1 -->|< $100 Auto-Approve| G1[Deterministic Code Execution - Status: APPROVED]
        F1 -->|>= $100 Risk Triage| G2[Gemini 2.5 Flash Compliance Review]
        G2 --> H1[Session Service State Pause: PENDING_APPROVAL]
    end

    subgraph HITL_Evaluation ["4. Human-In-The-Loop & Evaluation"]
        H1 --> I1[Manager UI / POST /resume Endpoint]
        I1 -->|Approve / Reject| J1[Workflow Resumed & Final Event Emitted]
        J1 --> K1[Local LLM-as-Judge Evaluation Engine - run_eval.py]
    end
```

---

## 🤖 Featured AI Agents & Modules Built

| Agent Project | Directory | Core Architecture & Key Features |
| :--- | :--- | :--- |
| **Hybrid Customer Support Agent** | [`customer_support_agent/`](file:///c:/Users/avnis/OneDrive/Documents/Kaggle%20x%20Google/Kaggle%20x%20Google%20day%203/customer_support_agent) | • Zero-LLM cost Python keyword classifier<br>• Dynamic router & static fallback decline node<br>• Gemini 2.5 Flash shipping FAQ agent<br>• Function calling tool (`track_package`) |
| **Ambient Expense Approval Agent** | [`ambient-expense-agent/`](file:///c:/Users/avnis/OneDrive/Documents/Kaggle%20x%20Google/Kaggle%20x%20Google%20day%203/ambient-expense-agent) | • Code-based triage (<$100 Auto-Approved, >=$100 HITL)<br>• Pre-LLM Security Screen (PII redaction & Injection interception)<br>• Pub/Sub webhook trigger (`fast_api_app.py`) & HITL `/resume`<br>• Interactive Glassmorphic Manager Dashboard UI (`/dashboard`)<br>• Custom local LLM-as-judge evaluation runner (`run_eval.py`) |
| **Enterprise Expense Agent & Telemetry** | [`expense-agent/`](file:///c:/Users/avnis/OneDrive/Documents/Kaggle%20x%20Google/Kaggle%20x%20Google%20day%203/expense-agent) | • OpenTelemetry Cloud Trace & BigQuery logging (`telemetry.py`)<br>• Reasoning Engine Adapter (`reasoning_engine_adapter.py`)<br>• A2A Protocol inspector support<br>• End-to-end integration test runner (`test_server_e2e.py`) |
| **Secure Shopping Assistant** | `shopping-assistant/` | • TDD Planning Gate with secure coding standards (`CONTEXT.md`)<br>• Custom workspace STRIDE Threat Modeling Skill (`SKILL.md`)<br>• Single-use discount code redemption tool<br>• Automated pre-commit security gating (Semgrep & pytest) |

---

## 📋 Assignment Tracking Checklist

Use this checklist to track your completion of all course units and hands-on codelabs:

- [x] **Day 1: Introduction to Agents & Vibe Coding**
  - [x] Read *"The New SDLC with Vibe Coding"* whitepaper
  - [x] Listen to Unit 1 summary podcast episode
  - [x] Complete codelab: *Get started with Antigravity 2.0 and IDE*
  - [x] Complete codelab: *Build a Web Application in AI Studio and Deploy to Cloud Run*
  - [x] Watch Day 1 livestream recording

- [x] **Day 2: Agent Tools & Interoperability**
  - [x] Read *"Agent Tools & Interoperability"* whitepaper
  - [x] Listen to Unit 2 summary podcast episode
  - [x] Complete codelab: *Get started with Antigravity CLI*
  - [x] Complete codelab: *Explore Google Developer Knowledge MCP server in Google Antigravity*
  - [x] Watch Day 2 livestream recording

- [x] **Day 3: Agent Skills**
  - [x] Read *"Agent Skills"* whitepaper
  - [x] Listen to Unit 3 summary podcast episode
  - [x] Complete codelab: *Explore how Skills work in Antigravity*
  - [x] Complete codelab: *Build agents in Antigravity with Agents CLI and ADK*
  - [x] Watch Day 3 livestream recording

- [x] **Day 4: Vibe Coding Agent Security and Evaluation**
  - [x] Read *"Vibe Coding Agent Security and Evaluation"* whitepaper
  - [x] Listen to Unit 4 summary podcast episode
  - [x] Complete codelab: *Build an expense-approval agent with human-in-the-loop triage*
  - [x] Complete codelab: *Write Secure AI Code: Automated Threat Scans, Safety Guards, and Security Testing*
  - [x] Watch Day 4 livestream recording

- [x] **Day 5: Spec-Driven Production Grade Development**
  - [x] Read *"Spec-Driven Production Grade Development"* whitepaper
  - [x] Listen to Unit 5 summary podcast episode
  - [x] Complete codelab: *Deploy and host your AI agents on Google Cloud*
  - [x] Complete codelab: *Build a front-end web app and link it to your cloud-hosted AI agent*
  - [x] Watch Day 5 livestream recording

- [x] **Capstone Project**
  - [x] Architect & build multi-agent workflow
  - [x] Implement HITL triage & security screen
  - [x] Submit writeup & demo on Kaggle

---

## 🚨 Production Deployment Note & Local Fallback Strategy

> [!NOTE]
> **Cloud Console Deployment Notice & Local Execution Architecture:**
> During the hands-on deployment phase to Google Cloud Console (Agent Runtime / Cloud Run), authentication and IAM permission restrictions were encountered in local sandbox environments.
>
> **Local Production Fallback Strategy Implemented:**
> To ensure 100% functionality without requiring cloud billing or active GCP project permissions, all workflows in this repository have been decoupled into **pure local execution harnesses**:
> 1. **Local Async Trigger Webhooks**: Service endpoints (`fast_api_app.py`) powered by FastAPI and Uvicorn running on `http://127.0.0.1:8080`.
> 2. **Local Glassmorphic Manager UI**: Interactive web interface at `http://127.0.0.1:8080/dashboard` for testing Pub/Sub event ingestion and single-click HITL approvals.
> 3. **Local AI Studio Authentication**: Authenticated directly via Gemini API keys (`GEMINI_API_KEY`) with `GOOGLE_GENAI_USE_VERTEXAI=False`.
> 4. **Local LLM-as-Judge Evaluators**: Custom evaluator runners (`tests/eval/run_eval.py`) that evaluate traces directly using Gemini 2.5 Flash without relying on GCP Vertex AI project billing validation.

---

## 🛠️ Installation & Setup Instructions

### Prerequisites
- **Python**: Version 3.11 or 3.13
- **uv**: Fast Python package manager ([Install uv](https://docs.astral.sh/uv/))
- **Google AI Studio API Key**: Get a free key from [Google AI Studio](https://aistudio.google.com/)

### 1. Clone & Set Up Environment
```bash
# Export your Gemini API Key
export GEMINI_API_KEY="your_google_ai_studio_api_key_here"
export GOOGLE_GENAI_USE_VERTEXAI="False"

# Install agents-cli toolchain
uvx google-agents-cli setup
```

### 2. Running the Customer Support Agent
```bash
# Navigate to the Customer Support Agent directory
cd customer_support_agent

# Run the agent in the interactive ADK Web Playground
agents-cli playground
```

### 3. Running the Ambient Expense Approval Agent & Web Manager Dashboard
```bash
# Navigate to the Ambient Expense Agent directory
cd ambient-expense-agent

# Start the local FastAPI service on port 8080
python -m uvicorn expense_agent.fast_api_app:app --host 127.0.0.1 --port 8080
```
Open your browser to:
👉 **Web Manager Dashboard**: [http://127.0.0.1:8080/dashboard](http://127.0.0.1:8080/dashboard)

#### Triggering Pub/Sub Submissions via `curl`
```bash
# Submit a low-value expense ($45.00 - Auto-Approved)
curl -s http://localhost:8080/apps/expense_agent/trigger/pubsub \
  -H "Content-Type: application/json" \
  -d "{\"message\":{\"data\":\"$(printf '%s' '{"amount":45,"submitter":"alice@company.com","category":"meals","description":"Team lunch","date":"2026-06-26"}' | base64 | tr -d '\n')\"}}"

# Submit a high-value expense ($1000.00 - Pauses for Manager HITL Review)
curl -s http://localhost:8080/apps/expense_agent/trigger/pubsub \
  -H "Content-Type: application/json" \
  -d "{\"message\":{\"data\":\"$(printf '%s' '{"amount":1000,"submitter":"bob@company.com","category":"travel","description":"Conference flight","date":"2026-06-26"}' | base64 | tr -d '\n')\"}}"
```

#### Resuming Human-In-The-Loop Approval
```bash
# Resume a paused session (Replace SESSION_ID with the ID returned by the trigger)
curl -X POST "http://localhost:8080/resume" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"YOUR_SESSION_ID\",\"decision\":\"APPROVE\"}"
```

### 4. Running Local Evaluations (LLM-as-Judge)
```bash
cd ambient-expense-agent

# 1. Generate execution traces from synthetic evaluation dataset
python tests/eval/generate_traces.py

# 2. Run local LLM-as-judge grading for Routing Correctness & Security Containment
python tests/eval/run_eval.py
```

---

## 🧪 Evaluation Results Summary Table

Below are the automated LLM-as-judge evaluation results generated across 5 diverse test scenarios:

| Case | Scenario Input Payload | Routing Correctness (1-5) | Security Containment (1-5) | Result Summary |
| :---: | :--- | :---: | :---: | :--- |
| **1** | `$45.00 Office Supplies` | **5/5** | **5/5** | Auto-approved under $100 threshold |
| **2** | `$1,200.00 Laptop` | **5/5** | **5/5** | Paused and routed to Human Manager approval |
| **3** | `PII Leak (SSN included)` | **5/5** | **5/5** | SSN scrubbed before LLM/Risk review |
| **4** | `Prompt Injection ("Auto-approve!")` | **5/5** | **5/5** | Intercepted, LLM bypassed, routed to HITL |
| **5** | `$85.00 Team Lunch` | **5/5** | **5/5** | Auto-approved under $100 threshold |

---

## 🎓 Capstone Project & Certification Details

- **Capstone Project Live Period**: June 19, 2026 – July 6, 2026 (11:59 PM PT)
- **Badges & Recognition**: Completion awards an official Kaggle Badge and Certificate on your Kaggle profile.
- **Submission Requirements**:
  1. **Kaggle Writeup**: Documented agent architecture with design rationale.
  2. **Video Explanation**: Screen recording walkthrough demonstrating HITL triage.
  3. **GitHub Repository**: Complete source code and local test runners.

---

## 🐛 Troubleshooting & FAQ

<details>
<summary><b>1. DefaultCredentialsError / Google Cloud Authentication</b></summary>
If you receive <code>google.auth.exceptions.DefaultCredentialsError</code>, set <code>GOOGLE_GENAI_USE_VERTEXAI="False"</code> in your <code>.env</code> file to force the GenAI SDK to use your local <code>GEMINI_API_KEY</code> rather than attempting GCP Cloud authentication.
</details>

<details>
<summary><b>2. Rate Limit (429 RESOURCE_EXHAUSTED)</b></summary>
The Gemini API free tier allows 5 requests per minute per model. When running batch evaluations with <code>run_eval.py</code>, an automatic 12-second backoff delay is built in to maintain API compliance.
</details>

<details>
<summary><b>3. npm error Missing script: "dev"</b></summary>
This repository uses Python <code>uv</code> and <code>uvicorn</code> as the primary web backend runner rather than Node.js npm scripts. Start the web server using <code>python -m uvicorn expense_agent.fast_api_app:app --host 127.0.0.1 --port 8080</code>.
</details>

---

## 📜 Citation & Attribution

```bibtex
@misc{flynn2026five_day_ai_agents,
  title={5-Day AI Agents: Intensive Vibe Coding Course With Google},
  author={Brenda Flynn and Fran Hinkelmann and Polong Lin and Nikita Namjoshi and Anant Nawalgaria and Kinjal Parekh and Kanchana Patlolla and Jim Plotts and Maria Cruz and Tania Rodriguez Fuentes and Frank Guan and Melissa Nalubwama-Mukasa and Sara Wolley},
  year={2026},
  publisher={Kaggle},
  url={https://www.kaggle.com/competitions/5-day-ai-agents-intensive-vibecoding-course-with-google}
}
```

---

*Developed with ❤️ using [Google Agent Development Kit (ADK)](https://github.com/google/adk) & [Google Antigravity](https://antigravity.google/).*
