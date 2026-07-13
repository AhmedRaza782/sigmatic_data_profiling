from __future__ import annotations

from schema import qualify_table_name, quote_identifier


NUMERIC_TYPES = {
    "INT",
    "BIGINT",
    "DOUBLE",
    "FLOAT",
    "DECIMAL",
    "NUMBER",
    "SMALLINT",
    "TINYINT",
}


def build_numeric_statistics_query(
    catalog: str,
    schema: str,
    table: str,
    column_name: str,
) -> str:

    return f"""
    SELECT

        MIN({quote_identifier(column_name)}) min_value,

        MAX({quote_identifier(column_name)}) max_value,

        AVG({quote_identifier(column_name)}) avg_value,

        SUM({quote_identifier(column_name)}) sum_value

    FROM {qualify_table_name(catalog,schema,table)}
    """


def normalize_numeric_statistics(column_name, rows):

    if not rows:
        return []

    row = rows[0]

    return [

        {

            "column_name": column_name,

            "min_value": row[0],

            "max_value": row[1],

            "avg_value": row[2],

            "sum_value": row[3],

        }

    ]