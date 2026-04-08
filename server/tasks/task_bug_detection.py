def grade(review: str) -> float:
    review = review.lower()

    if "off by one" in review or "index error" in review:
        return 1.0
    elif "bug" in review:
        return 0.5
    return 0.0