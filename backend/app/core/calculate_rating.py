def calculate_new_rating(rating_A: int, rating_B: int, score_A: float) -> tuple[int, int]:
    """
    Подсчитать рейтинг игроков после матча
    score_A: 1.0 — победа A, 0.5 — ничья, 0.0 — победа B
    """
    K = 35
    expected_point_A = round(1 / (1 + 10**((rating_B-rating_A)/400)), 3)
    expected_point_B = round(1 - expected_point_A, 3)

    new_rating_A = rating_A + K * (score_A - expected_point_A)
    new_rating_B = rating_B + K * ((1 - score_A) - expected_point_B)

    return int(new_rating_A), int(new_rating_B)
