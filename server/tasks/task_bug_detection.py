"""
TASK 1: Bug Detection (Easy)
----------------------------
The agent is shown a Python function with ONE planted bug.
It must identify the bug in its review.

Scoring:
  0.4 — mentioned the correct line or variable name
  0.3 — described what the bug actually does (e.g. "off by one", "wrong operator")
  0.3 — suggested a correct fix

Total: 1.0 max
"""

# The buggy code the agent will see
CODE = '''
def calculate_average(numbers):
    """Returns the average of a list of numbers."""
    total = 0
    for num in numbers:
        total += num
    # BUG: divides by len+1 instead of len
    return total / (len(numbers) + 1)

# Example usage
print(calculate_average([10, 20, 30]))  # Should print 20.0, but prints 15.0
'''

TASK_DESCRIPTION = (
    "Review the function below. There is exactly one bug. "
    "Identify: (1) where the bug is, (2) what it does wrong, (3) how to fix it."
)

# Keywords the grader looks for in the agent's review
# We check for these case-insensitively
LOCATION_KEYWORDS = ["len(numbers) + 1", "len + 1", "+ 1", "line 7", "return total"]
DESCRIPTION_KEYWORDS = ["off by one", "wrong divisor", "incorrect denominator",
                         "divides by", "division", "denominator", "average is wrong",
                         "incorrect", "should be len(numbers)"]
FIX_KEYWORDS = ["len(numbers)", "remove + 1", "remove the + 1", "delete + 1",
                 "total / len", "/ len(numbers)"]


def grade(review: str) -> tuple[float, str]:
    """
    Grade the agent's bug detection review.

    Returns:
        (score, feedback) where score is 0.0-1.0
    """
    review_lower = review.lower()
    score = 0.0
    feedback_parts = []

    # Check 1: Did they find WHERE the bug is?
    found_location = any(kw.lower() in review_lower for kw in LOCATION_KEYWORDS)
    if found_location:
        score += 0.4
        feedback_parts.append("✓ Correctly identified the location of the bug.")
    else:
        feedback_parts.append("✗ Did not clearly identify where the bug is (hint: look at the return statement).")

    # Check 2: Did they describe WHAT is wrong?
    found_description = any(kw.lower() in review_lower for kw in DESCRIPTION_KEYWORDS)
    if found_description:
        score += 0.3
        feedback_parts.append("✓ Correctly described what the bug does.")
    else:
        feedback_parts.append("✗ Did not describe what the bug actually causes.")

    # Check 3: Did they suggest a FIX?
    found_fix = any(kw.lower() in review_lower for kw in FIX_KEYWORDS)
    if found_fix:
        score += 0.3
        feedback_parts.append("✓ Provided a correct fix.")
    else:
        feedback_parts.append("✗ Did not suggest a correct fix.")

    feedback = " | ".join(feedback_parts)
    return round(score, 2), feedback
