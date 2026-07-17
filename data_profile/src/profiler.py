from __future__ import annotations

import logging
from typing import Any

from cardinality import build_unique_count_query
from datatypes import detect_data_type_issues
from duplicates import build_duplicate_count_query
from nulls import build_null_percentage_query
from quality import (
    build_quality_score_components,
    build_quality_warnings,
    calculate_quality_score,
)
from recommendations import build_recommendations
from schema import (
    build_schema_query,
    normalize_schema_rows,
    qualify_table_name,
    quote_identifier,
)
from statistics import build_numeric_statistics_query, normalize_numeric_statistics

logger = logging.getLogger(__name__)


class DataProfiler:
    """Execute reusable profiling queries against a Databricks SQL Warehouse."""

    def __init__(self, connection: Any, catalog: str, schema: str, table: str) -> None:
        self.connection = connection
        self.catalog = catalog
        self.schema = schema
        self.table = table
        self.table_name = qualify_table_name(catalog, schema, table)

    def _execute_query(
        self,
        sql_text: str,
        parameters: tuple[Any, ...] | None = None,
    ) -> list[tuple[Any, ...]]:

        cursor = self.connection.cursor()

        try:

            logger.info(sql_text)

            if parameters:
                cursor.execute(sql_text, parameters)
            else:
                cursor.execute(sql_text)

            return cursor.fetchall()

        except Exception as e:

            logger.exception("SQL FAILED")

            logger.exception(sql_text)

            raise

        finally:

            cursor.close()

    def _get_row_count(self) -> int:
        rows = self._execute_query(f"SELECT COUNT(*) AS row_count FROM {self.table_name}")
        return int(rows[0][0]) if rows else 0

    def _get_schema_rows(self) -> list[dict[str, Any]]:
        query, parameters = build_schema_query(self.catalog, self.schema, self.table)
        rows = self._execute_query(query, parameters)
        return normalize_schema_rows(list(rows))

    def _get_sample_rows(self, column_names: list[str]) -> list[dict[str, Any]]:
        if not column_names:
            return []

        quoted_columns = ", ".join(quote_identifier(column_name) for column_name in column_names)
        query = f"SELECT {quoted_columns} FROM {self.table_name} LIMIT 5"
        rows = self._execute_query(query)
        sample_rows: list[dict[str, Any]] = []
        for row in rows:
            sample_rows.append({column_names[index]: row[index] for index in range(len(column_names))})
        return sample_rows

    def profile(self) -> dict[str, Any]:
        row_count = self.get_row_count()
        schema_rows = self._get_schema_rows()
        column_names = [row["column_name"] for row in schema_rows]

        null_percentages: dict[str, float] = {}
        for column_name in column_names:
            query = build_null_percentage_query(self.catalog, self.schema, self.table, column_name)
            result = self._execute_query(query)
            null_count = int(result[0][0]) if result else 0
            null_percentages[column_name] = round((null_count / row_count * 100.0) if row_count else 0.0, 2)

        duplicate_count = 0
        if column_names:
            duplicate_query = build_duplicate_count_query(self.catalog, self.schema, self.table, column_names)
            duplicate_result = self._execute_query(duplicate_query)
            duplicate_count = int(duplicate_result[0][0]) if duplicate_result else 0

        unique_counts: dict[str, int] = {}
        for column_name in column_names:
            unique_query = build_unique_count_query(self.catalog, self.schema, self.table, column_name)
            unique_result = self._execute_query(unique_query)
            unique_counts[column_name] = int(unique_result[0][0]) if unique_result else 0

        numeric_statistics: list[dict[str, Any]] = []

        NUMERIC_TYPES = {
            "INT",
            "INTEGER",
            "BIGINT",
            "SMALLINT",
            "TINYINT",
            "DOUBLE",
            "FLOAT",
            "REAL",
            "DECIMAL",
            "NUMERIC",
            "LONG",
            "SHORT",
        }

        for row in schema_rows:
        
            column_name = row["column_name"]

            data_type = row["data_type"].upper().split("(")[0]

            if data_type not in NUMERIC_TYPES:
                continue
            
            numeric_query = build_numeric_statistics_query(
                self.catalog,
                self.schema,
                self.table,
                column_name,
            )

            numeric_result = self._execute_query(numeric_query)

            numeric_statistics.extend(
                normalize_numeric_statistics(
                    column_name,
                    numeric_result,
                )
            )

        candidate_primary_keys = [
            column_name for column_name, unique_count in unique_counts.items() if unique_count == row_count and row_count > 0
        ]
        data_type_issues = detect_data_type_issues(schema_rows)
        quality_score_components = build_quality_score_components(
            row_count,
            duplicate_count,
            null_percentages,
            data_type_issues,
            candidate_primary_keys,
        )
        quality_score = quality_score_components["overall_score"]
        quality_warnings = build_quality_warnings(
            schema_rows,
            null_percentages,
            duplicate_count,
            candidate_primary_keys,
            row_count,
        )
        sample_rows = self._get_sample_rows(column_names)

        recommendations = build_recommendations(
            schema_rows,
            null_percentages,
            quality_score,
            candidate_primary_keys,
            duplicate_count,
            data_type_issues,
        )

        return {
            "row_count": row_count,
            "column_count": len(column_names),
            "schema": schema_rows,
            "sample_rows": sample_rows,
            "null_percentages": null_percentages,
            "duplicate_count": duplicate_count,
            "unique_counts": unique_counts,
            "numeric_statistics": numeric_statistics,
            "candidate_primary_keys": candidate_primary_keys,
            "data_type_issues": data_type_issues,
            "quality_score": quality_score,
            "quality_score_components": quality_score_components,
            "quality_warnings": quality_warnings,
            "recommendations": recommendations,
            "catalog": self.catalog,
            "schema_name": self.schema,
            "table_name": self.table,
            "qualified_table_name": self.table_name,
        }

    def get_row_count(self) -> int:
        return self._get_row_count()

    def get_column_count(self) -> int:
        return len(self._get_schema_rows())

    def get_schema(self) -> list[dict[str, Any]]:
        return self._get_schema_rows()

    def get_null_percentages(self) -> dict[str, float]:
        row_count = self.get_row_count()
        schema_rows = self._get_schema_rows()
        null_percentages: dict[str, float] = {}
        for row in schema_rows:
            column_name = row["column_name"]
            query = build_null_percentage_query(self.catalog, self.schema, self.table, column_name)
            result = self._execute_query(query)
            null_count = int(result[0][0]) if result else 0
            null_percentages[column_name] = round((null_count / row_count * 100.0) if row_count else 0.0, 2)
        return null_percentages

    def get_duplicate_count(self) -> int:
        schema_rows = self._get_schema_rows()
        column_names = [row["column_name"] for row in schema_rows]
        if not column_names:
            return 0
        query = build_duplicate_count_query(self.catalog, self.schema, self.table, column_names)
        result = self._execute_query(query)
        return int(result[0][0]) if result else 0

    def get_unique_counts(self) -> dict[str, int]:
        schema_rows = self._get_schema_rows()
        unique_counts: dict[str, int] = {}
        for row in schema_rows:
            column_name = row["column_name"]
            query = build_unique_count_query(self.catalog, self.schema, self.table, column_name)
            result = self._execute_query(query)
            unique_counts[column_name] = int(result[0][0]) if result else 0
        return unique_counts

    def get_numeric_statistics(self) -> list[dict[str, Any]]:
        schema_rows = self._get_schema_rows()
        statistics: list[dict[str, Any]] = []
        for row in schema_rows:
            column_name = row["column_name"]
            query = build_numeric_statistics_query(self.catalog, self.schema, self.table, column_name)
            result = self._execute_query(query)
            statistics.extend(normalize_numeric_statistics(list(result)))
        return statistics

    def get_candidate_primary_keys(self) -> list[str]:
        row_count = self.get_row_count()
        unique_counts = self.get_unique_counts()
        return [column_name for column_name, unique_count in unique_counts.items() if unique_count == row_count and row_count > 0]

    def get_data_type_issues(self) -> list[dict[str, Any]]:
        return detect_data_type_issues(self._get_schema_rows())

    def get_quality_score(self) -> float:
        null_percentages = self.get_null_percentages()
        duplicate_count = self.get_duplicate_count()
        row_count = self.get_row_count()
        return calculate_quality_score(row_count, duplicate_count, null_percentages)