---
title: Code Review Environment
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# 🔍 Code Review Environment

An RL environment where an LLM agent reviews code snippets and receives graded feedback. Built on [OpenEnv](https://github.com/meta-pytorch/openenv).

The agent gets up to **3 attempts** per task. Each attempt is scored by a keyword-based grader and the agent receives structured feedback to improve its next review.

## Tasks

| Task | Difficulty | Description | Passing Score |
|------|-----------|-------------|:---:|
| `bug_detection` | 🟢 Easy | Find a single planted bug in a Python function | 0.85 |
| `security_audit` | 🟡 Medium | Identify 2 security vulnerabilities in a Flask login endpoint | 0.85 |
| `pr_review` | 🔴 Hard | Review a multi-file PR with 3 issues (concurrency, validation, resources) | 0.85 |

## Quick Start

```python
import asyncio
from code_review_env import CodeReviewAction, CodeReviewEnvClient

async def main():
    async with CodeReviewEnvClient(base_url="http://localhost:8000") as env:
        # Reset with a specific task
        result = await env.reset(task_type="bug_detection")
        obs = result.observation

        print(f"Task: {obs.task_type}")
        print(f"Instructions: {obs.task_description}")
        print(f"Code to review:\n{obs.code_snippet}")

        # Submit a review
        result = await env.step(
            CodeReviewAction(review="Line 7 has a bug: `len(numbers) + 1` should be `len(numbers)`. This off-by-one error causes the average to be incorrect.")
        )
        obs = result.observation

        print(f"Score: {obs.score}")
        print(f"Feedback: {obs.feedback}")
        print(f"Done: {obs.done}")
        print(f"Reward: {result.reward}")

asyncio.run(main())
```

## Running Locally

### 1. Start the environment server

```bash
cd code_review_env
uv sync
uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
```

### 2. Run the inference agent

```bash
# Set required environment variables
export API_BASE_URL="https://api.groq.com/openai/v1"
export MODEL_NAME="llama-3.1-8b-instant"
export HF_TOKEN="your-api-key"

python inference.py
```

The inference script runs all 3 tasks sequentially, logs results in the mandated `[START]`/`[STEP]`/`[END]` format, and prints a final average score.

## Building & Running with Docker

```bash
# Build the Docker image
docker build -t code_review_env:latest -f server/Dockerfile .

# Run the container
docker run -p 8000:8000 code_review_env:latest
```

## Deploying to Hugging Face Spaces

```bash
# From the environment directory (where openenv.yaml is located)
openenv push

# Or specify options
openenv push --repo-id my-org/code-review-env --private
```

After deployment, your space will be available at `https://huggingface.co/spaces/<repo-id>` with:
- **Web Interface** at `/web` — interactive UI for exploring the environment
- **API Docs** at `/docs` — full OpenAPI/Swagger interface
- **Health Check** at `/health` — container health monitoring
- **WebSocket** at `/ws` — persistent session endpoint for low-latency interactions

## Environment API

### Action

**`CodeReviewAction`** — what the agent sends to the environment:

| Field | Type | Description |
|-------|------|-------------|
| `review` | `str` | The agent's code review text |

### Observation

**`CodeReviewObservation`** — what the environment returns:

| Field | Type | Description |
|-------|------|-------------|
| `code_snippet` | `str` | The code the agent must review |
| `task_type` | `str` | `"bug_detection"`, `"security_audit"`, or `"pr_review"` |
| `task_description` | `str` | Plain English instructions for the task |
| `feedback` | `str` | Grader feedback on the last review (empty on reset) |
| `score` | `float` | Score for the last submission (0.0–1.0) |
| `done` | `bool` | Whether the episode has ended |
| `reward` | `float` | Reward for this step (equals score) |

### Episode Flow

```
reset(task_type) → Observation (code + instructions)
     ↓
step(review)     → Observation (feedback + score)     ← up to 3 attempts
     ↓
Episode ends when: score ≥ 0.85 (passed) OR 3 steps used
```

## Grading Rubrics

### 🟢 Bug Detection (Easy)

The agent reviews a `calculate_average()` function with an off-by-one division bug.

| Criterion | Points | What the grader checks |
|-----------|:------:|----------------------|
| Location | 0.40 | Mentions `len(numbers) + 1`, `+ 1`, or the return line |
| Description | 0.30 | Explains what the bug does (off-by-one, wrong divisor, etc.) |
| Fix | 0.30 | Suggests using `len(numbers)` without `+ 1` |

### 🟡 Security Audit (Medium)

The agent reviews a Flask `/login` endpoint with SQL injection and plaintext passwords.

| Criterion | Points | What the grader checks |
|-----------|:------:|----------------------|
| SQL Injection | 0.35 | Identifies the SQL injection via string formatting |
| Impact | 0.25 | Explains why it's dangerous (bypass auth, dump data, etc.) |
| Plaintext Password | 0.25 | Identifies passwords stored/compared in plaintext |
| Fixes | 0.15 | Suggests parameterized queries or password hashing |

### 🔴 PR Review (Hard)

The agent reviews a 3-file PR diff with a race condition, missing validation, and a resource leak.

| Criterion | Points | What the grader checks |
|-----------|:------:|----------------------|
| Race Condition | 0.30 | Identifies the thread-unsafe counter in `analytics.py` |
| Input Validation | 0.25 | Identifies missing checks for negative quantity/price |
| Resource Leak | 0.25 | Identifies the unclosed file handle in `reporter.py` |
| Review Quality | 0.20 | Uses severity labels, priorities, and recommendations (3+ quality keywords) |

## Environment Variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `API_BASE_URL` | ✅ | LLM API endpoint (e.g. `https://api.groq.com/openai/v1`) |
| `MODEL_NAME` | ✅ | Model identifier (e.g. `llama-3.1-8b-instant`) |
| `HF_TOKEN` | ✅ | API key for the LLM provider |
| `ENV_BASE_URL` | ❌ | Environment server URL (default: `http://127.0.0.1:8000`) |

## Stdout Logging Format

The inference script outputs logs in the format required by the automated checker. **Any deviation in field names, ordering, or formatting will result in incorrect evaluation scoring.**

```
[START] task=bug_detection env=code_review_env model=llama-3.1-8b-instant
[STEP]  step=1 action='Line 7 has a bug...' reward=0.70 done=false error=null
[STEP]  step=2 action='The return statement...' reward=0.99 done=true error=null
[END]   success=true steps=2 score=0.563 rewards=0.70,0.99
```

## Infrastructure Restrictions

> [!WARNING]
> - **Runtime** of `inference.py` must be **less than 20 minutes**
> - Environment and inference must run on a machine with **vcpu=2, memory=8GB**
> - All LLM calls must use the **OpenAI client** with the `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` env vars

## Validation

Run the pre-submission validator to check everything is working:

```bash
./pre_validation.sh https://your-space.hf.space .
```

This checks:
1. ✅ HF Space is live and responds to `/reset`
2. ✅ Docker image builds successfully
3. ✅ `openenv validate` passes

## Project Structure

```
code_review_env/
├── __init__.py              # Package exports
├── README.md                # This file
├── requirements.txt         # All project dependencies
├── openenv.yaml             # OpenEnv manifest (tasks, config)
├── pyproject.toml           # Project metadata and dependencies
├── client.py                # CodeReviewEnvClient (async WebSocket client)
├── models.py                # CodeReviewAction & CodeReviewObservation
├── inference.py             # LLM agent that runs all 3 tasks
├── pre_validation.sh        # Submission validator script
├── .env.example             # Example environment variables
└── server/
    ├── __init__.py          # Server module exports
    ├── app.py               # FastAPI app (HTTP + WebSocket via openenv)
    ├── code_review_env_environment.py  # Core RL environment logic
    ├── Dockerfile           # Container image definition
    ├── requirements.txt     # Server-only dependencies (Docker build)
    └── tasks/
        ├── task_bug_detection.py    # 🟢 Easy — off-by-one bug
        ├── task_security_audit.py   # 🟡 Medium — SQL injection + plaintext passwords
        └── task_pr_review.py        # 🔴 Hard — race condition + validation + resource leak
```

## Deliverables Checklist

Before submitting, ensure you have:

- [ ] Public GitHub repository with environment code
- [ ] `requirements.txt` in the root directory
- [ ] `inference.py` in the root directory (named exactly this)
- [ ] `README.md` with environment description, action/observation spaces, and setup instructions
- [ ] Deployed Hugging Face Spaces URL with working demo
- [ ] Pre-submission validation script passing: `./pre_validation.sh https://your-space.hf.space .`
- [ ] All env vars set: `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`
- [ ] Inference runtime < 20 minutes on vcpu=2 / 8GB RAM

## License

BSD-style license. See the LICENSE file in the root directory.
