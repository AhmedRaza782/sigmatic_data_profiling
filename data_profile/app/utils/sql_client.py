from __future__ import annotations

import logging
import os
from typing import Any

from .databricks_client import WarehouseOption

logger = logging.getLogger(__name__)


def create_sql_connection(warehouse_name: str, warehouses: list[WarehouseOption]) -> Any:
    """Create a SQL Warehouse connection using the Databricks SQL connector."""
    selected_warehouse = next((warehouse for warehouse in warehouses if warehouse.name == warehouse_name), None)
    if selected_warehouse is None:
        raise ValueError("Selected SQL warehouse is not available")

    try:
        from databricks import sql
    except ImportError as exc:  # pragma: no cover - import guard
        logger.exception("databricks-sql-connector is not installed: %s", exc)
        raise ImportError(
            "The Databricks SQL connector package is required. Install it with 'pip install databricks-sql-connector'."
        ) from exc

    from databricks.sdk import WorkspaceClient

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