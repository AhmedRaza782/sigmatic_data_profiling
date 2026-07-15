from __future__ import annotations

import logging
import os
from typing import Any

from databricks.sdk import WorkspaceClient

from .databricks_client import WarehouseOption

logger = logging.getLogger(__name__)


def create_sql_connection(
    warehouse_name: str,
    warehouses: list[WarehouseOption],
) -> Any:
    """Create a SQL Warehouse connection."""

    selected_warehouse = next(
        (w for w in warehouses if w.name == warehouse_name),
        None,
    )

    if selected_warehouse is None:
        raise ValueError("Selected SQL warehouse is not available")

    try:
        from databricks import sql
    except ImportError as exc:
        logger.exception(exc)
        raise ImportError(
            "Install databricks-sql-connector"
        ) from exc

    # ----------------------------------------------------
    # Streamlit Cloud
    # ----------------------------------------------------
    if (
        "DATABRICKS_HOST" in os.environ
        and "DATABRICKS_CLIENT_ID" in os.environ
        and "DATABRICKS_CLIENT_SECRET" in os.environ
    ):

        workspace = WorkspaceClient(
            host=os.environ["DATABRICKS_HOST"],
            client_id=os.environ["DATABRICKS_CLIENT_ID"],
            client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
        )

        return sql.connect(
            server_hostname=workspace.config.host.replace("https://", ""),
            http_path=selected_warehouse.http_path,
            credentials_provider=lambda: workspace.config.authenticate,
        )

    # ----------------------------------------------------
    # Local Development
    # ----------------------------------------------------
    workspace = WorkspaceClient(profile="data_profile")

    return sql.connect(
        server_hostname=workspace.config.host.replace("https://", ""),
        http_path=selected_warehouse.http_path,
        credentials_provider=lambda: workspace.config.authenticate,
    )