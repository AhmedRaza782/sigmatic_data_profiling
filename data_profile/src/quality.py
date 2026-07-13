from __future__ import annotations

from typing import Any


def calculate_quality_score(row_count: int, duplicate_count: int, null_percentages: dict[str, float]) -> float:
    if row_count <= 0:
        return 0.0

    null_penalty = sum(percent for percent in null_percentages.values()) / max(len(null_percentages), 1)
    duplicate_penalty = duplicate_count / max(row_count, 1) * 100.0
    score = 100.0 - (null_penalty * 0.6) - (duplicate_penalty * 0.4)
    return round(max(score, 0.0), 2)


def build_quality_warnings(schema_rows: list[dict[str, Any]], null_percentages: dict[str, float]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for row in schema_rows:
        column_name = row.get("column_name")
        if column_name and null_percentages.get(str(column_name), 0.0) > 25.0:
            warnings.append(
                {
                    "column_name": column_name,
                    "warning": "High null percentage",
                    "value": null_percentages[str(column_name)],
                }
            )
    return warnings