"""
TASK 3: PR Review (Hard)
--------------------------
The agent is shown a multi-function diff simulating a real PR.
It has THREE issues across different files/functions:
  1. Race condition in a counter update (no locking)
  2. Missing input validation (negative numbers accepted)
  3. Resource leak (file opened but not closed if exception occurs)

This is hard because:
  - Issues are spread across different functions
  - The agent must demonstrate architectural thinking, not just spot syntax
  - Partial credit encourages genuine effort

Scoring:
  0.30 — identified the race condition
  0.25 — identified missing input validation
  0.25 — identified the resource leak / missing error handling
  0.20 — quality of the overall review (mentions severity, suggests priority)

Total: 1.0 max
"""

CODE = '''
# PR: Add user stats tracking to the analytics module
# Files changed: analytics.py, validator.py, reporter.py

# ---- analytics.py ----
import threading

view_count = 0  # shared state

def record_view(user_id: str):
    """Record a page view for analytics."""
    global view_count
    # ISSUE 1: Race condition — read-modify-write without a lock
    # Two threads can read view_count=5 simultaneously, both write 6, losing a count
    view_count = view_count + 1
    log_event(user_id, view_count)

# ---- validator.py ----
def validate_purchase(item_id: str, quantity: int, price: float):
    """Validate a purchase request before processing."""
    if not item_id:
        raise ValueError("item_id cannot be empty")
    # ISSUE 2: No validation for quantity or price being negative
    # A user could submit quantity=-1 or price=-99.99 and corrupt the database
    return {"item_id": item_id, "quantity": quantity, "total": quantity * price}

# ---- reporter.py ----
def generate_report(filename: str) -> str:
    """Read a report file and return its contents."""
    # ISSUE 3: Resource leak — if read() raises an exception,
    # the file handle is never closed
    f = open(filename, "r")
    content = f.read()
    f.close()
    return content
'''

TASK_DESCRIPTION = (
    "Review this pull request diff. It touches three different files. "
    "Find all issues — consider concurrency, input validation, and resource management. "
    "For each issue: name it, explain the risk, and suggest a fix. "
    "Also comment on the overall code quality and review priority."
)

RACE_CONDITION_KEYWORDS = [
    "race condition", "race", "thread", "concurrent", "lock", "mutex",
    "atomic", "thread-safe", "threading.lock", "view_count", "global",
    "read-modify-write", "lost update", "synchroniz"
]
VALIDATION_KEYWORDS = [
    "validat", "negative", "input", "quantity", "price", "negative quantity",
    "negative price", "zero", "< 0", "<= 0", "positive", "sanitiz",
    "bounds check", "no check"
]
RESOURCE_LEAK_KEYWORDS = [
    "resource leak", "file leak", "file handle", "not closed", "exception",
    "with open", "context manager", "try", "finally", "with statement",
    "close()", "leak", "handle"
]
QUALITY_KEYWORDS = [
    "severity", "critical", "high", "medium", "low", "priority",
    "recommend", "suggest", "overall", "architecture", "pattern",
    "best practice", "should", "consider"
]


def grade(review: str) -> tuple[float, str]:
    """
    Grade the agent's full PR review.

    Returns:
        (score, feedback) where score is 0.0-1.0
    """
    review_lower = review.lower()
    score = 0.0
    feedback_parts = []

    # Check 1: Race condition
    found_race = any(kw in review_lower for kw in RACE_CONDITION_KEYWORDS)
    if found_race:
        score += 0.30
        feedback_parts.append("✓ Identified the race condition in analytics.py.")
    else:
        feedback_parts.append("✗ Missed the race condition (hint: what happens with two threads calling record_view() simultaneously?).")

    # Check 2: Input validation
    found_validation = any(kw in review_lower for kw in VALIDATION_KEYWORDS)
    if found_validation:
        score += 0.25
        feedback_parts.append("✓ Identified the missing input validation in validator.py.")
    else:
        feedback_parts.append("✗ Missed the missing input validation (hint: what if quantity is -5?).")

    # Check 3: Resource leak
    found_leak = any(kw in review_lower for kw in RESOURCE_LEAK_KEYWORDS)
    if found_leak:
        score += 0.25
        feedback_parts.append("✓ Identified the resource leak in reporter.py.")
    else:
        feedback_parts.append("✗ Missed the resource leak (hint: what happens if read() throws an exception?).")

    # Check 4: Review quality
    found_quality = sum(1 for kw in QUALITY_KEYWORDS if kw in review_lower)
    if found_quality >= 3:
        score += 0.20
        feedback_parts.append("✓ Review demonstrates good engineering judgment (severity, priority, recommendations).")
    elif found_quality >= 1:
        score += 0.10
        feedback_parts.append("~ Review shows some judgment but could be more structured.")
    else:
        feedback_parts.append("✗ Review lacks severity assessment or actionable recommendations.")

    feedback = " | ".join(feedback_parts)
    return round(score, 2), feedback
