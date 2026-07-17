from __future__ import annotations

from typing import Any


def detect_data_type_issues(schema_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    date_types = {
        "DATE",
        "TIMESTAMP",
        "DATETIME",
        "TIMESTAMP_NTZ",
        "TIMESTAMP_LTZ",
        "TIMESTAMP_TZ",
    }

    for row in schema_rows:
        column_name = str(row.get("column_name", "")).lower()
        data_type = str(row.get("data_type", "")).upper()

        if "date" in column_name and data_type not in date_types and not data_type.startswith("STRING"):
            issues.append(
                {
                    "column_name": row.get("column_name"),
                    "issue": "Date-like column is not stored as a date/time type",
                    "data_type": row.get("data_type"),
                    "severity": "Medium",
                }
            )

    return issues
