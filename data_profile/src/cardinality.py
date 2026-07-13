from __future__ import annotations

from schema import qualify_table_name, quote_identifier


def build_unique_count_query(catalog: str, schema: str, table: str, column_name: str) -> str:
    return (
        f"SELECT COUNT(DISTINCT {quote_identifier(column_name)}) AS unique_count "
        f"FROM {qualify_table_name(catalog, schema, table)}"
    )
