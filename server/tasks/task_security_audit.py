"""
TASK 2: Security Audit (Medium)
--------------------------------
The agent is shown a Flask login endpoint with TWO security issues:
  1. SQL injection via string formatting
  2. Password stored/compared in plaintext (no hashing)

Scoring:
  0.35 — identified the SQL injection
  0.25 — explained WHY SQL injection is dangerous (not just named it)
  0.25 — identified the plaintext password issue
  0.15 — suggested parameterized queries OR password hashing as fixes

Total: 1.0 max
"""

CODE = '''
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # SECURITY ISSUE 1: SQL injection via string formatting
    query = f"SELECT * FROM users WHERE username = \\'{username}\\' AND password = \\'{password}\\'"
    cursor.execute(query)
    user = cursor.fetchone()

    if user:
        return jsonify({"status": "logged in", "user": user[0]})
    else:
        return jsonify({"status": "invalid credentials"}), 401
'''

TASK_DESCRIPTION = (
    "Perform a security audit on this Flask login endpoint. "
    "Identify ALL security vulnerabilities, explain why each is dangerous, "
    "and suggest how to fix them."
)

# Grading keyword sets
SQL_INJECTION_KEYWORDS = [
    "sql injection", "sqli", "string format", "f-string", "f\"", "f'",
    "string concatenat", "unsanitized", "user input", "inject"
]
SQL_DANGER_KEYWORDS = [
    "bypass", "authenticate", "drop table", "arbitrary query", "any user",
    "without password", "attacker", "malicious", "' or '1'='1", "or 1=1",
    "database", "all records", "dump"
]
PASSWORD_KEYWORDS = [
    "plaintext", "plain text", "unhashed", "no hash", "password hash",
    "bcrypt", "argon2", "pbkdf2", "sha", "md5", "store password",
    "password storage", "hardcoded", "clear text", "cleartext"
]
FIX_KEYWORDS = [
    "parameterized", "prepared statement", "placeholder", "cursor.execute(query, (",
    "?", "%s", "hash", "bcrypt", "werkzeug", "check_password_hash"
]

MIN_SCORE = 0.01
MAX_SCORE = 0.99


def grade(review: str) -> tuple[float, str]:
    """
    Grade the agent's security audit.

    Returns:
        (score, feedback) where score is 0.0-1.0
    """
    review_lower = review.lower()
    score = 0.0
    feedback_parts = []

    # Check 1: Did they spot SQL injection?
    found_sqli = any(kw in review_lower for kw in SQL_INJECTION_KEYWORDS)
    if found_sqli:
        score += 0.35
        feedback_parts.append("✓ Identified SQL injection vulnerability.")
    else:
        feedback_parts.append("✗ Missed the SQL injection vulnerability.")

    # Check 2: Did they explain WHY SQL injection is dangerous?
    found_danger = any(kw in review_lower for kw in SQL_DANGER_KEYWORDS)
    if found_danger:
        score += 0.25
        feedback_parts.append("✓ Explained the impact/danger of the SQL injection.")
    else:
        feedback_parts.append("✗ Did not explain why the SQL injection is dangerous.")

    # Check 3: Did they spot plaintext passwords?
    found_password = any(kw in review_lower for kw in PASSWORD_KEYWORDS)
    if found_password:
        score += 0.25
        feedback_parts.append("✓ Identified the plaintext password storage issue.")
    else:
        feedback_parts.append("✗ Missed the plaintext password storage issue.")

    # Check 4: Did they suggest fixes?
    found_fix = any(kw in review_lower for kw in FIX_KEYWORDS)
    if found_fix:
        score += 0.15
        feedback_parts.append("✓ Suggested appropriate fixes.")
    else:
        feedback_parts.append("✗ Did not suggest concrete fixes.")

    feedback = " | ".join(feedback_parts)
    # Validator requires score to be strictly between 0 and 1.
    clamped_score = min(max(round(score, 2), MIN_SCORE), MAX_SCORE)
    return clamped_score, feedback
