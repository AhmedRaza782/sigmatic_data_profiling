from __future__ import annotations

from typing import Any


def build_recommendations(
    schema_rows: list[dict[str, Any]],
    null_percentages: dict[str, float],
    quality_score: float,
    candidate_primary_keys: list[str],
    duplicate_count: int,
    data_type_issues: list[dict[str, Any]],
) -> list[str]:
    recommendations: list[str] = []

    fully_null_columns = [
        column_name
        for column_name, percent in null_percentages.items()
        if percent == 100.0
    ]
    high_null_columns = sorted(
        [
            (column_name, percent)
            for column_name, percent in null_percentages.items()
            if percent >= 25.0 and percent < 100.0
        ],
        key=lambda item: -item[1],
    )

    if fully_null_columns:
        recommendations.append(
            f"Review or remove fully null columns: {', '.join(fully_null_columns)}."
        )

    if high_null_columns:
        top_columns = ", ".join(
            [f"{column_name} ({percent:.0f}%)" for column_name, percent in high_null_columns[:4]]
        )
        recommendations.append(
            f"Target cleanup on high-null columns such as {top_columns} to improve completeness and reporting reliability."
        )

    if duplicate_count > 0:
        recommendations.append(
            f"Investigate the {duplicate_count:,} duplicate records detected to confirm whether they are true duplicates or ingestion artifacts."
        )
    else:
        recommendations.append(
            "No duplicate record risk was detected. Keep deduplication checks in place for new data loads."
        )

    if candidate_primary_keys:
        recommendations.append(
            f"Treat {candidate_primary_keys[0]} as a strong primary key candidate and validate it across refreshes."
        )
        if len(candidate_primary_keys) > 1:
            recommendations.append(
                f"Additional unique key candidates identified: {', '.join(candidate_primary_keys[1:])}."
            )
    else:
        recommendations.append(
            "No clear primary key candidate was found; validate candidate business keys before downstream modeling."
        )

    if data_type_issues:
        issues = "; ".join(str(issue.get("issue", "")) for issue in data_type_issues)
        recommendations.append(f"Review data type concerns: {issues}.")

    if quality_score < 75.0:
        recommendations.append(
            "Address the most severe completeness and governance issues first, then rerun profiling to confirm improvement."
        )

    if not recommendations:
        recommendations.append(
            "The table looks healthy. Continue monitoring quality and freshness on a regular cadence."
        )

    return recommendations