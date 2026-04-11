# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Code Review Environment Implementation.

This environment presents the agent with code review challenges across 3 tasks:
  1. bug_detection  — find a single planted bug (easy)
  2. security_audit — find 2 security vulnerabilities (medium)
  3. pr_review      — review a multi-file PR with 3 issues (hard)

Each task runs for MAX_STEPS steps. The agent submits a review each step and
receives a score + feedback. The episode ends when MAX_STEPS is reached OR
the agent scores >= PASSING_SCORE.

How episode state works:
  - self._task_type: which of the 3 tasks is active (set by reset())
  - self._step_count: how many steps taken so far
  - self._best_score: best score achieved this episode (for the final reward)
  - self._done: whether the episode has ended
"""

from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import CodeReviewAction, CodeReviewObservation
    from .tasks import task_bug_detection, task_security_audit, task_pr_review
except ImportError:
    from models import CodeReviewAction, CodeReviewObservation
    from .tasks import task_bug_detection, task_security_audit, task_pr_review

# How many attempts the agent gets per task
MAX_STEPS = 3

# If the agent hits this score, we end early (they passed)
PASSING_SCORE = 0.85

# Map task name -> the grader module
TASK_REGISTRY = {
    "bug_detection": task_bug_detection,
    "security_audit": task_security_audit,
    "pr_review": task_pr_review,
}

# Default task (can be overridden by passing task_type to reset)
DEFAULT_TASK = "bug_detection"


class CodeReviewEnvironment(Environment):
    """
    Code Review RL Environment.

    The agent receives a code snippet and must review it.
    It gets up to MAX_STEPS attempts. Each attempt is graded.
    The reward for each step equals the grader score (0.0-1.0).
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._task_type = DEFAULT_TASK
        self._best_score = 0.0
        self._done = False

    def reset(self, task_type: str = DEFAULT_TASK) -> CodeReviewObservation:
        """
        Start a new episode.

        Args:
            task_type: which task to run ('bug_detection', 'security_audit', 'pr_review')

        Returns:
            Observation containing the code snippet and instructions
        """
        # Validate the task type
        if task_type not in TASK_REGISTRY:
            task_type = DEFAULT_TASK

        self._task_type = task_type
        self._best_score = 0.0
        self._done = False
        self._state = State(episode_id=str(uuid4()), step_count=0)

        task_module = TASK_REGISTRY[self._task_type]

        return CodeReviewObservation(
            code_snippet=task_module.CODE,
            task_type=self._task_type,
            task_description=task_module.TASK_DESCRIPTION,
            feedback="",
            score=0.0,
            done=False,
            reward=0.0,
        )

    def step(self, action: CodeReviewAction) -> CodeReviewObservation:
        """
        Grade the agent's review and return feedback + score.

        Args:
            action: CodeReviewAction with the agent's review text

        Returns:
            Observation with grader feedback and score
        """
        # If already done, just return a terminal observation
        if self._done:
            return CodeReviewObservation(
                code_snippet="",
                task_type=self._task_type,
                task_description="Episode already ended.",
                feedback="Episode already ended.",
                score=self._best_score,
                done=True,
                reward=0.0,
            )

        self._state.step_count += 1

        # Run the grader for the current task
        task_module = TASK_REGISTRY[self._task_type]
        score, feedback = task_module.grade(action.review)

        # Track best score
        if score > self._best_score:
            self._best_score = score

        # Episode ends if: max steps reached OR agent passed
        steps_used = self._state.step_count
        passed = score >= PASSING_SCORE
        out_of_steps = steps_used >= MAX_STEPS
        self._done = passed or out_of_steps

        # Add a summary message if the episode is ending
        if self._done:
            if passed:
                feedback += f" | Episode complete — passed with score {score:.2f}!"
            else:
                feedback += f" | Episode complete — best score was {self._best_score:.2f}."

        return CodeReviewObservation(
            code_snippet=task_module.CODE,
            task_type=self._task_type,
            task_description=task_module.TASK_DESCRIPTION,
            feedback=feedback,
            score=score,
            done=self._done,
            reward=score,  # reward = score for each step
        )

    @property
    def state(self) -> State:
        return self._state
