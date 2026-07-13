from __future__ import annotations

from schema import qualify_table_name, quote_identifier


def build_null_percentage_query(catalog: str, schema: str, table: str, column_name: str) -> str:
    return (
        f"SELECT COUNT(*) AS null_count "
        f"FROM {qualify_table_name(catalog, schema, table)} "
        f"WHERE {quote_identifier(column_name)} IS NULL"
    )