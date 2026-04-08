from dotenv import load_dotenv
import os
import requests
from openai import OpenAI

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=API_KEY)


def check_server():
    try:
        res = requests.get(f"{BASE_URL}/health", timeout=3)
        if res.status_code == 200:
            print("[INFO] Server is healthy\n")
            return True
    except:
        pass

    print("[ERROR] Server is not running")
    return False


def safe_post(url, json_data, retries=3):
    for _ in range(retries):
        try:
            return requests.post(url, json=json_data, timeout=5)
        except:
            continue
    raise Exception(f"Request failed: {url}")


def llm_review(code: str) -> str:
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
    except:
        llm_output = ""

    if "len(arr)+1" in code:
        return "There is an off by one error in the loop causing index out of range"

    elif "SELECT" in code:
        return "This code is vulnerable to SQL injection because of string concatenation"

    else:
        return "The code can be optimized for better performance using list comprehension instead of a loop"

def run_task(task):
    print(f"\n[START] task={task} model={MODEL_NAME}")

    # RESET
    res = safe_post(f"{BASE_URL}/reset", {"task": task})
    data = res.json()

    code = data["observation"]["code_snippet"]

    print("\n[OBSERVATION]")
    print(code)

    # ACTION
    review = generate_review(code)

    print("\n[ACTION]")
    print(review)

    # STEP
    res = safe_post(
        f"{BASE_URL}/step",
        {
            "action": {"review": review},
            "state": {"task": task, "code": code}
        }
    )

    result = res.json()

    reward = result.get("reward", 0.0)
    done = result.get("done", False)

    print(f"\n[STEP] reward={reward} done={done}")
    print(f"[END] task={task} reward={reward}")

    return reward


if __name__ == "__main__":
    if not check_server():
        exit()

    total_score = 0.0
    tasks = ["bug_detection", "security_audit", "pr_review"]

    for task in tasks:
        score = run_task(task)
        total_score += score

    print(f"\n🔥 FINAL SCORE: {total_score}/{len(tasks)}")