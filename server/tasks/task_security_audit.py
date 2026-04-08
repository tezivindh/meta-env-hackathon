def grade(review: str) -> float:
    review = review.lower()

    if "sql injection" in review:
        return 1.0
    elif "security" in review:
        return 0.5
    return 0.0