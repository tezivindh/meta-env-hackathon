from openenv.core.env_server import create_app
from .code_review_env_environment import CodeReviewEnv
from models import CodeReviewAction, CodeReviewObservation

app = create_app(
    env=CodeReviewEnv,
    action_cls=CodeReviewAction,
    observation_cls=CodeReviewObservation,
)

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()