from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from databricks.sdk import WorkspaceClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WarehouseOption:
    name: str
    http_path: str


class DatabricksMetadataClient:
    """Thin wrapper around Databricks SDK for metadata discovery."""

    def __init__(self) -> None:
        self._workspace = WorkspaceClient(
            host=os.environ["DATABRICKS_HOST"],
            client_id=os.environ["DATABRICKS_CLIENT_ID"],
            client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
        )

    def list_warehouses(self) -> list[WarehouseOption]:
        warehouses: list[WarehouseOption] = []
        for warehouse in self._workspace.warehouses.list():
            if getattr(warehouse, "enable_serverless_compute", False):
                path = getattr(getattr(warehouse, "odbc_params", None), "path", None)
                if path:
                    warehouses.append(WarehouseOption(name=warehouse.name, http_path=path))
        return warehouses

    def list_catalogs(self) -> list[str]:
        try:
            return [getattr(catalog, "name", "") for catalog in self._workspace.catalogs.list() if getattr(catalog, "name", "")]
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.exception("Unable to list catalogs: %s", exc)
            return []

    def list_schemas(self, catalog: str) -> list[str]:
        if not catalog or catalog in {"No catalogs available", ""}:
            return []
        try:
            rows = self._workspace.schemas.list(catalog_name=catalog)
            return [getattr(row, "name", None) for row in rows if getattr(row, "name", None)]
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.exception("Unable to list schemas: %s", exc)
            return []

    def list_tables(self, catalog: str, schema: str) -> list[str]:
        if not catalog or not schema or catalog in {"No catalogs available", ""} or schema in {"No schemas available", ""}:
            return []
        try:
            rows = self._workspace.tables.list(catalog_name=catalog, schema_name=schema)
            return [getattr(row, "name", None) for row in rows if getattr(row, "name", None)]
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.exception("Unable to list tables: %s", exc)
            return []


def build_metadata_client(profile: str = "data_profile") -> DatabricksMetadataClient:
    return DatabricksMetadataClient(profile=profile)