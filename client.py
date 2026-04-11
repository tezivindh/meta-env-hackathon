"""Code Review Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import CodeReviewAction, CodeReviewObservation


class CodeReviewEnvClient(
    EnvClient[CodeReviewAction, CodeReviewObservation, State]
):
    """
    Client for the Code Review Environment.

    Example (async):
        async with CodeReviewEnvClient(base_url="http://localhost:8000") as client:
            result = await client.reset()
            result = await client.step(CodeReviewAction(review="SQL injection found."))
            print(result.observation.feedback)
    """

    def _step_payload(self, action: CodeReviewAction) -> Dict:
        return {"review": action.review}

    def _parse_result(self, payload: Dict) -> StepResult[CodeReviewObservation]:
        obs_data = payload.get("observation", {})
        observation = CodeReviewObservation(
            code_snippet=obs_data.get("code_snippet", ""),
            task_type=obs_data.get("task_type", ""),
            task_description=obs_data.get("task_description", ""),
            feedback=obs_data.get("feedback", ""),
            score=obs_data.get("score", 0.0),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
