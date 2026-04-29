"""
SoulSync AI - Suggestion Engine
Generates smart suggestions based on detected patterns.

Rule-based logic:
  - IF user skips gym often → suggest easier alternatives
  - IF user is stressed frequently → suggest stress management
  - IF productivity is low → suggest focus techniques
  - IF positive streak → reinforce it
"""

from backend.suggestion.analyzer import get_full_analysis


# ─── Suggestion Rules ─────────────────────────────────────

def generate_suggestions(user_id: str) -> list:
    """
    Analyze user patterns and generate actionable suggestions.

    Returns:
        List of suggestion strings
    """
    analysis = get_full_analysis(user_id)

    if not analysis["has_data"]:
        return ["Start logging your daily activities to get personalized insights!"]

    suggestions = []

    # ── Emotion-based suggestions ──────────────────────────
    emotions = analysis["emotions"]
    dominant = analysis["dominant_emotion"]

    if emotions.get("tired", 0) >= 2:
        suggestions.append(
            "💤 You've been feeling tired often. Consider improving your sleep schedule."
        )

    if emotions.get("stressed", 0) >= 2:
        suggestions.append(
            "😰 Stress detected multiple times. Try 5-minute breathing exercises daily."
        )

    if emotions.get("sad", 0) >= 2:
        suggestions.append(
            "💙 You've been feeling down. Reach out to friends or try a mood-boosting activity."
        )

    if emotions.get("happy", 0) >= 3:
        suggestions.append(
            "🎉 Great to see you happy often! Keep doing what's working for you."
        )

    # ── Activity-based suggestions ─────────────────────────
    activities = analysis["activities"]

    for activity, stats in activities.items():
        missed    = stats.get("missed", 0)
        completed = stats.get("completed", 0)

        if activity == "gym" and missed >= 2:
            suggestions.append(
                "🏋️ You've skipped gym multiple times. Try shorter 15-min workouts instead."
            )

        if activity == "work" and missed >= 2:
            suggestions.append(
                "💼 Work focus issues detected. Try the Pomodoro technique (25 min focus blocks)."
            )

        if activity == "study" and completed >= 3:
            suggestions.append(
                "📚 Great study consistency! Keep up the learning momentum."
            )

    # ── Productivity-based suggestions ─────────────────────
    productivity = analysis["productivity"]

    if productivity.get("low", 0) >= 3:
        suggestions.append(
            "📉 Low productivity detected often. Try time-blocking your day."
        )

    if productivity.get("high", 0) >= 3:
        suggestions.append(
            "🚀 You're on a productivity streak! Document what's working for you."
        )

    # ── Default if no patterns yet ─────────────────────────
    if not suggestions:
        suggestions.append(
            f"Your dominant emotion is '{dominant}'. Keep tracking to unlock deeper insights."
        )

    return suggestions


def get_suggestion_summary(user_id: str) -> dict:
    """
    Get analysis + suggestions in one call.
    Used by API endpoint.
    """
    analysis    = get_full_analysis(user_id)
    suggestions = generate_suggestions(user_id)

    return {
        "user_id"     : user_id,
        "analysis"    : analysis,
        "suggestions" : suggestions,
        "count"       : len(suggestions),
    }
