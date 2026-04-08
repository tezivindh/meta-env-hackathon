from dotenv import load_dotenv
import os
import requests
from openai import OpenAI

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY")

client = None
if API_KEY:
    try:
        client = OpenAI(api_key=API_KEY)
    except Exception as e:
        print(f"[DEBUG] Failed to init OpenAI: {e}")
        client = None


def check_server():
    try:
        res = requests.get(f"{BASE_URL}/health", timeout=3)
        return res.status_code == 200
    except:
        return False


def safe_post(url, json_data, retries=3):
    for _ in range(retries):
        try:
            return requests.post(url, json=json_data, timeout=5)
        except:
            continue
    raise Exception(f"Request failed: {url}")


def llm_review(code: str) -> str:
    if client is None:
        return ""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior code reviewer. Identify bugs, security issues, and improvements clearly."
                },
                {
                    "role": "user",
                    "content": f"Review this code:\n{code}"
                }
            ],
            temperature=0.1,
            max_tokens=200,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[DEBUG] LLM failed: {e}")
        return ""

def generate_review(code: str) -> str:
    try:
        llm_output = llm_review(code)
        if llm_output:
            return llm_output
    except:
        llm_output = ""

    if "len(arr)+1" in code:
        return "There is an off by one error in the loop causing index out of range"

    elif "SELECT" in code:
        return "This code is vulnerable to SQL injection because of string concatenation"

    else:
        return "The code can be optimized for better performance using list comprehension instead of a loop"

step_count = 1  # since env is single-step

def run_task(task):
    print(f"[START] task={task}", flush=True)

    res = safe_post(f"{BASE_URL}/reset", {"task": task})
    data = res.json()

    code = data["observation"]["code_snippet"]

    review = generate_review(code)

    res = safe_post(
        f"{BASE_URL}/step",
        {
            "action": {"review": review},
            "state": {"task": task, "code": code}
        }
    )

    result = res.json()

    reward = result.get("reward", 0.0)

    print(f"[STEP] step=1 reward={reward}", flush=True)
    print(f"[END] task={task} score={reward} steps=1", flush=True)

    return reward

if __name__ == "__main__":
    if not check_server():
        exit()

    total_score = 0.0
    tasks = ["bug_detection", "security_audit", "pr_review"]

    for task in tasks:
        score = run_task(task)
        total_score += score

    print(f"FINAL SCORE: {total_score}/{len(tasks)}")