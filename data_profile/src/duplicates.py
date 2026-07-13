from __future__ import annotations

from schema import qualify_table_name, quote_identifier


def build_duplicate_count_query(catalog: str, schema: str, table: str, columns: list[str]) -> str:
    if not columns:
        return f"SELECT COUNT(*) FROM {qualify_table_name(catalog, schema, table)} WHERE 1 = 0"

    column_list = ", ".join(quote_identifier(column) for column in columns)
    return (
        f"SELECT COUNT(*) AS duplicate_count "
        f"FROM (SELECT {column_list} FROM {qualify_table_name(catalog, schema, table)} "
        f"GROUP BY {column_list} HAVING COUNT(*) > 1) AS grouped"
    )