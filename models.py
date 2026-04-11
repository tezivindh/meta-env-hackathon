# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Code Review Environment.

Action  = what the LLM agent sends TO the environment (its review)
Observation = what the environment sends BACK to the agent (the code + feedback)
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class CodeReviewAction(Action):
    """
    The agent's response — its code review.

    The agent reads the code challenge and submits a review as plain text.
    Example: "Line 5 has a SQL injection vulnerability. The query is built
              using string concatenation instead of parameterized queries."
    """
    review: str = Field(..., description="The agent's code review text")


class CodeReviewObservation(Observation):
    """
    What the agent sees each step.

    - code_snippet: the code the agent must review
    - task_type: which task this is ('bug_detection', 'security_audit', 'pr_review')
    - task_description: plain English instructions for the agent
    - feedback: after submission, what the grader says (empty on first step)
    - score: the grader's score for the last submission (0.0 to 1.0)
    """
    code_snippet: str = Field(default="", description="The code the agent must review")
    task_type: str = Field(default="", description="Type of review task")
    task_description: str = Field(default="", description="What the agent should do")
    feedback: str = Field(default="", description="Grader feedback on the last review")
    score: float = Field(default=0.0, description="Score for the last submission (0.0-1.0)")
