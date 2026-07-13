from __future__ import annotations

from typing import Any


def detect_data_type_issues(schema_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    numeric_types = {"INT", "BIGINT", "DECIMAL", "DOUBLE", "FLOAT", "NUMBER", "TINYINT", "SMALLINT"}

    for row in schema_rows:
        column_name = str(row.get("column_name", "")).lower()
        data_type = str(row.get("data_type", "")).upper()

        if "id" in column_name and data_type not in numeric_types:
            issues.append(
                {
                    "column_name": row.get("column_name"),
                    "issue": "Identifier-like column is not numeric",
                    "data_type": row.get("data_type"),
                }
            )

    return issues
