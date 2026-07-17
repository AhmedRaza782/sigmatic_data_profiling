from __future__ import annotations

from typing import Any


def calculate_quality_score(
    row_count: int,
    duplicate_count: int,
    null_percentages: dict[str, float],
    data_type_issues: list[dict[str, Any]] | None = None,
    candidate_primary_keys: list[str] | None = None,
) -> float:
    components = build_quality_score_components(
        row_count,
        duplicate_count,
        null_percentages,
        data_type_issues or [],
        candidate_primary_keys or [],
    )
    return round(components["overall_score"], 2)


def build_quality_score_components(
    row_count: int,
    duplicate_count: int,
    null_percentages: dict[str, float],
    data_type_issues: list[dict[str, Any]],
    candidate_primary_keys: list[str],
) -> dict[str, float]:
    if row_count <= 0:
        return {
            "completeness": 0.0,
            "uniqueness": 0.0,
            "validity": 0.0,
            "governance": 0.0,
            "overall_score": 0.0,
        }

    avg_null = sum(null_percentages.values()) / max(len(null_percentages), 1)
    completeness = max(0.0, 100.0 - avg_null * 0.7)

    duplicate_ratio = duplicate_count / max(row_count, 1)
    uniqueness = max(0.0, 100.0 - duplicate_ratio * 100.0)

    validity = 100.0
    if data_type_issues:
        validity = max(0.0, 100.0 - min(len(data_type_issues) * 10.0, 40.0))

    high_null_columns = [value for value in null_percentages.values() if 30.0 <= value < 100.0]
    fully_null_columns = [value for value in null_percentages.values() if value == 100.0]
    governance_penalty = len(high_null_columns) * 4.0 + len(fully_null_columns) * 8.0
    if not candidate_primary_keys and row_count > 0:
        governance_penalty += 4.0
    governance = max(0.0, 100.0 - min(governance_penalty, 30.0))

    overall_score = (
        completeness * 0.4
        + uniqueness * 0.3
        + validity * 0.2
        + governance * 0.1
    )

    return {
        "completeness": round(completeness, 2),
        "uniqueness": round(uniqueness, 2),
        "validity": round(validity, 2),
        "governance": round(governance, 2),
        "overall_score": round(overall_score, 2),
    }


def build_quality_warnings(
    schema_rows: list[dict[str, Any]],
    null_percentages: dict[str, float],
    duplicate_count: int,
    candidate_primary_keys: list[str],
    row_count: int,
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []

    if duplicate_count > 0:
        severity = "High" if duplicate_count / max(row_count, 1) > 0.01 else "Medium"
        warnings.append(
            {
                "warning_type": "Duplicate Records",
                "details": f"{duplicate_count:,} duplicate records were detected.",
                "severity": severity,
            }
        )

    fully_null_columns = [
        column_name
        for column_name, percent in null_percentages.items()
        if percent == 100.0
    ]
    if fully_null_columns:
        warnings.append(
            {
                "warning_type": "Fully Null Columns",
                "details": f"The following columns are fully null: {', '.join(fully_null_columns)}.",
                "severity": "High",
            }
        )

    for column_name, percent in sorted(null_percentages.items(), key=lambda item: -item[1]):
        if 50.0 <= percent < 100.0:
            severity = "High"
        elif 25.0 <= percent < 50.0:
            severity = "Medium"
        else:
            continue
        warnings.append(
            {
                "warning_type": "Elevated Null Rate",
                "details": f"{column_name} is {percent:.2f}% null.",
                "severity": severity,
            }
        )

    if row_count > 0 and not candidate_primary_keys:
        warnings.append(
            {
                "warning_type": "Primary Key Candidate",
                "details": "No perfect unique key candidate was identified for this table.",
                "severity": "Low",
            }
        )

    return warnings