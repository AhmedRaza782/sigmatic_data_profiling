from __future__ import annotations

from typing import Any


def quote_identifier(identifier: str) -> str:
    return f"`{identifier}`"


def qualify_table_name(catalog: str, schema: str, table: str) -> str:
    return f"{catalog}.{schema}.{table}"


def build_schema_query(catalog: str, schema: str, table: str) -> tuple[str, tuple[str, str, str]]:
    table_fqn = qualify_table_name(catalog, schema, table)
    sql = f"DESCRIBE TABLE {table_fqn}"
    return sql, ()


def normalize_schema_rows(rows):

    schema=[]

    ordinal=1

    for row in rows:

        if len(row)<2:
            continue

        col=str(row[0]).strip()

        dtype=str(row[1]).strip()

        if (
            col==""
            or col.startswith("#")
            or col.lower()=="col_name"
        ):
            continue

        schema.append(

            {

                "column_name":col,

                "data_type":dtype,

                "is_nullable":"YES",

                "ordinal_position":ordinal

            }

        )

        ordinal+=1

    return schema
