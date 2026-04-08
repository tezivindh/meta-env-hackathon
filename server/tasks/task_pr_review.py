def grade(review: str) -> float:
    review = review.lower()
    score = 0.0

    if "bug" in review:
        score += 0.3
    if "security" in review:
        score += 0.3
    if "style" in review:
        score += 0.4

    return min(score, 1.0)