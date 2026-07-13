from __future__ import annotations

from typing import Any


def build_recommendations(schema_rows: list[dict[str, Any]], null_percentages: dict[str, float], quality_score: float) -> list[str]:
    recommendations: list[str] = []
    if quality_score < 85.0:
        recommendations.append("Review the highest-null columns and fill gaps before downstream reporting.")

    if any(row.get("is_nullable") == "YES" for row in schema_rows):
        recommendations.append("Consider enforcing NOT NULL constraints on critical business columns.")

    if any(percent > 10.0 for percent in null_percentages.values()):
        recommendations.append("Investigate columns with elevated null rates to improve data completeness.")

    if not recommendations:
        recommendations.append("The table looks healthy. Continue monitoring for drift and freshness.")

    return recommendations