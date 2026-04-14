"""
inference.py — Code Review Env
===================================
MANDATORY environment variables:
    API_BASE_URL        The API endpoint for the LLM (e.g. https://api.groq.com/openai/v1)
    MODEL_NAME          The model identifier to use for inference
    HF_TOKEN            Your Hugging Face / Groq / OpenAI API key
    LOCAL_IMAGE_NAME    Docker image name (only if using from_docker_image())

STDOUT FORMAT (exact — automated checker will verify):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...,rn>
"""

import asyncio
import os
import textwrap
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from code_review_env import CodeReviewAction, CodeReviewEnvClient

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
# API_BASE_URL is the LLM endpoint per hackathon spec
API_BASE_URL = os.getenv("API_BASE_URL") or "https://api.groq.com/openai/v1"
MODEL_NAME   = os.getenv("MODEL_NAME")   or "llama-3.1-8b-instant"
API_KEY      = os.getenv("HF_TOKEN")     or os.getenv("OPENAI_API_KEY")

# Local environment server URL (separate from LLM API)
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://127.0.0.1:8000")

BENCHMARK               = "code_review_env"
MAX_STEPS               = 3
MAX_TOTAL_REWARD        = float(MAX_STEPS)   # reward per step is in [0, 1]
SUCCESS_SCORE_THRESHOLD = 0.85
TASKS                   = ["bug_detection", "security_audit", "pr_review"]
TEMPERATURE             = 0.1
MAX_TOKENS              = 1024

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a principal software engineer performing a structured code review.

    For EACH issue you find, you MUST provide all four of these:
    1. LOCATION — the exact line number or variable name with the issue
    2. PROBLEM  — what it does wrong (bug, security flaw, resource leak, etc.)
    3. FIX       — a concrete, specific code change to resolve it
    4. SEVERITY  — Critical / High / Medium / Low

    Do not write general advice. Be precise and to-the-point.
    Cover bugs, security vulnerabilities, and resource issues.
    Reply with your structured review only — no preamble.
    """
).strip()


# ── Log helpers (field names and format are spec-mandated) ────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float,
             done: bool, error: Optional[str]) -> None:
    action_clean = action.replace("\n", " ").replace("\r", "")[:120]
    done_str  = str(done).lower()
    error_str = error if error else "null"
    print(f"[STEP] step={step} action={action_clean!r} "
          f"reward={reward:.2f} done={done_str} error={error_str}", flush=True)


def log_end(success: bool, steps: int,
            score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} "
          f"score={score:.3f} rewards={rewards_str}", flush=True)


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_user_prompt(code: str, task_desc: str, feedback: str, step: int) -> str:
    prior = ""
    if feedback:
        prior = (f"\n\nYour previous review got this feedback:\n{feedback}"
                 f"\n\nImprove your review based on this feedback.")
    return textwrap.dedent(
        f"""
        Task: {task_desc}

        Code:
        ```
        {code}
        ```{prior}
        """
    ).strip()


# ── LLM call (synchronous OpenAI client, as required by spec) ────────────────

def get_review(client: OpenAI, code: str, task_desc: str,
               feedback: str, step: int) -> str:
    user_prompt = build_user_prompt(code, task_desc, feedback, step)
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text if text else "This code has issues that need review."
    except Exception as exc:
        print(f"[DEBUG] LLM request failed: {exc}", flush=True)
        return "This code has issues that need review."


# ── Episode runner ────────────────────────────────────────────────────────────

async def run_task(client: OpenAI, task: str) -> float:
    rewards: List[float] = []
    steps_taken = 0
    score   = 0.0
    success = False
    error   = None

    log_start(task=task, env=BENCHMARK, model=MODEL_NAME)

    async with CodeReviewEnvClient(base_url=ENV_BASE_URL) as env:
        try:
            result    = await env.reset(task_type=task)
            obs       = result.observation
            code      = obs.code_snippet
            task_desc = obs.task_description
            feedback  = ""
            done      = obs.done

            for step in range(1, MAX_STEPS + 1):
                if done:
                    break

                review = get_review(client, code, task_desc, feedback, step)

                try:
                    result   = await env.step(CodeReviewAction(review=review))
                    obs      = result.observation
                    reward   = float(result.reward or 0.0)
                    done     = result.done
                    feedback = obs.feedback
                    code     = obs.code_snippet
                    error    = None
                except Exception as exc:
                    reward, done, error = 0.0, False, str(exc)
                    print(f"[DEBUG] step error: {exc}", flush=True)

                rewards.append(reward)
                steps_taken = step
                log_step(step=step, action=review,
                         reward=reward, done=done, error=error)

                if done:
                    break

            raw_score = max(rewards) if rewards else 0.0
            score   = min(max(raw_score, 0.001), 0.999)
            success = score >= SUCCESS_SCORE_THRESHOLD

        except Exception as exc:
            print(f"[DEBUG] episode error: {exc}", flush=True)
            score = 0.001
        finally:
            score = min(max(score, 0.001), 0.999)
            log_end(success=success, steps=steps_taken,
                    score=score, rewards=rewards)

    return score


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    import httpx
    try:
        async with httpx.AsyncClient() as http:
            r = await http.get(f"{ENV_BASE_URL}/health", timeout=5)
            r.raise_for_status()
    except Exception as exc:
        print(f"[DEBUG] Server not reachable at {ENV_BASE_URL}: {exc}", flush=True)
        raise SystemExit(1)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    total = 0.0
    for task in TASKS:
        s = await run_task(client, task)
        total += s
        print(f"[DEBUG] {task} => {s:.3f}", flush=True)

    print(f"[DEBUG] FINAL_AVG={total / len(TASKS):.3f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
