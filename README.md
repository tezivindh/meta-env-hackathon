# Code Review Environment (OpenEnv)

## Overview

This project implements a custom OpenEnv environment for evaluating AI agents on real-world code review tasks.

The environment simulates a code review workflow where an agent analyzes code snippets, generates feedback, and receives a reward based on correctness.

It combines:
- Deterministic grading for evaluation
- LLM-based reasoning using OpenAI
- Hybrid fallback logic for reliability
- Dockerized deployment

---

## Tasks

### 1. Bug Detection (Easy)
Detect logical issues such as off-by-one errors.

Example:
```python
for i in range(len(arr)+1): print(arr[i])
```

---

### 2. Security Audit (Medium)

Identify vulnerabilities such as SQL injection.

Example:

```python
query = 'SELECT * FROM users WHERE id=' + user_input
```

---

### 3. PR Review (Hard)

Suggest improvements for performance and readability.

Example:

```python
for i in range(len(data)):
    result.append(data[i] * 2)
```

---

## Action Space

```python
CodeReviewAction:
    review: str
```

The agent submits a textual code review describing issues or improvements.

## Observation Space

```python
CodeReviewObservation:
    code_snippet: str
    feedback: str
    score: float
```

The environment returns the code snippet, feedback message, and evaluation score.

---

## Project Structure

```
code_review_env/
├── server/
│   ├── app.py
│   ├── code_review_env_environment.py
│   ├── tasks/
│   └── Dockerfile
├── models.py
├── inference.py
├── pyproject.toml
├── uv.lock
├── openenv.yaml
└── README.md
```

---

## Setup and Run

### 1. Build Docker Image

```bash
docker build -t code-review-env -f server/Dockerfile .
```

### 2. Run Container

```bash
docker run --env-file .env -p 8000:8000 code-review-env
```

### 3. Test API

```bash
curl -X POST http://127.0.0.1:8000/reset -H "Content-Type: application/json" -d '{}'
```

---

## Environment Variables

Create a `.env` file:

```
OPENAI_API_KEY=your_api_key
API_BASE_URL=http://127.0.0.1:8000
MODEL_NAME=gpt-4o-mini
```

---

## Running the Agent

```bash
python inference.py
```

---

## Sample Output

```
[START] task=bug_detection
[OBSERVATION]
for i in range(len(arr)+1): print(arr[i])

[ACTION]
There is an off-by-one error in the loop.

[STEP] reward=1.0 done=True
[END] task=bug_detection reward=1.0

[START] task=security_audit
[STEP] reward=1.0 done=True

[START] task=pr_review
[STEP] reward=1.0 done=True

FINAL SCORE: 3.0/3
```

---

## Baseline Performance

The provided inference script achieves the following scores:

- Bug Detection: 1.0
- Security Audit: 1.0
- PR Review: 1.0

Final Score: 3.0 / 3.0

---

## Design Decisions

### Hybrid LLM + Rule-Based Approach

The system combines LLM-generated feedback with rule-based guarantees to ensure both natural responses and consistent scoring.

### Deterministic Grading

All tasks use deterministic graders to ensure reproducible evaluation with rewards between 0.0 and 1.0.

### Robustness

* Retry mechanism for API requests
* Graceful handling of LLM failures
* Fallback logic ensures consistent performance

---

## Reward Design

Each task provides graded rewards between 0.0 and 1.0 based on the quality of the agent's review.

- 1.0 -> Correct identification of the issue with clear explanation
- 0.5 -> Partial understanding (mentions issue but unclear reasoning)
- 0.0 -> Incorrect or irrelevant feedback

This allows partial progress signals instead of purely binary evaluation.

---

## Episode Design

Each episode consists of a single-step interaction:

1. `reset()` provides a code snippet for review
2. Agent generates a review (action)
3. `step(action)` evaluates the review and assigns reward
4. Episode terminates (`done = True`)

This design simplifies evaluation while maintaining realistic task structure.

---

## OpenEnv Compliance

* reset() implemented
* step() implemented
* Structured action and observation models
* Reward system (0.0 to 1.0)
* Dockerized deployment
* Successfully passes `openenv validate`

---

## Real-World Motivation

Code review is a fundamental part of modern software development. Engineers routinely analyze code for bugs, security vulnerabilities, and performance improvements.

This environment simulates that workflow, making it useful for evaluating AI agents in practical, real-world scenarios such as automated code review, developer assistance tools, and CI/CD pipelines.

---

## Why This Project Stands Out

* Combines LLM reasoning with deterministic evaluation
* Simulates real-world code review workflows
* Production-ready architecture with Docker and API
* Demonstrates strong backend and AI integration skills

---

## Future Improvements

* Multi-step reasoning agents
* More advanced grading rubrics
* Integration with real GitHub pull requests
* Extended evaluation metrics

---

## Author

Team stateshift
