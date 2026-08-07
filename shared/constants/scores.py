class ScoreCategories:
    EXCELLENT = "Excellent"
    GOOD = "Good"
    NEEDS_IMPROVEMENT = "Needs Improvement"
    POOR = "Poor"

    @staticmethod
    def get_category(score: float) -> str:
        if score >= 85.0:
            return ScoreCategories.EXCELLENT
        elif score >= 70.0:
            return ScoreCategories.GOOD
        elif score >= 50.0:
            return ScoreCategories.NEEDS_IMPROVEMENT
        return ScoreCategories.POOR


APP_VERSION = "2.0.0"
SCHEMA_VERSION_V1 = "1.0.0"
SCHEMA_VERSION_V2 = "2.0.0"
