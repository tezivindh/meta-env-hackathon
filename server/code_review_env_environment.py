from openenv.core.env_server import Environment
from openenv.core.client_types import StepResult

from models import CodeReviewAction, CodeReviewObservation

from server.tasks.task_bug_detection import grade as bug_grade
from server.tasks.task_security_audit import grade as sec_grade
from server.tasks.task_pr_review import grade as pr_grade


class CodeReviewEnv(Environment):
    
    @property
    def state(self):
        return {
            "task": self.task,
            "code": self.code
        }

    def reset(self, task: str = "bug_detection"):
        self.task = task

        if task == "bug_detection":
            self.code = "for i in range(len(arr)+1): print(arr[i])"
        elif task == "security_audit":
            self.code = "query = 'SELECT * FROM users WHERE id=' + user_input"
        else:
            self.code = """
def process(data):
    result = []
    for i in range(len(data)):
        result.append(data[i] * 2)
    return result
"""

        return CodeReviewObservation(
            code_snippet=self.code,
            feedback="Review the code",
            score=0.0,
            reward=0.0,
            done=False
        )
    def step(self, action: CodeReviewAction, state: dict = None):

        if state:
            self.task = state.get("task")
            self.code = state.get("code")

        review = action.review

        if self.task == "bug_detection":
            score = bug_grade(review)
        elif self.task == "security_audit":
            score = sec_grade(review)
        else:
            score = pr_grade(review)

        return CodeReviewObservation(
                code_snippet=self.code,
                feedback="Graded",
                score=score,
                reward=score,
                done=True
        )
        