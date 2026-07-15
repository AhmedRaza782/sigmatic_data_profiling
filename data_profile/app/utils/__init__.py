import os

from databricks.sdk import WorkspaceClient


class DatabricksMetadataClient:
    """Thin wrapper around Databricks SDK for metadata discovery."""

    def __init__(self) -> None:

        # =====================================================
        # Streamlit Cloud
        # =====================================================

        if (
            "DATABRICKS_HOST" in os.environ
            and "DATABRICKS_TOKEN" in os.environ
        ):

            self._workspace = WorkspaceClient(
                host=os.environ["DATABRICKS_HOST"],
                token=os.environ["DATABRICKS_TOKEN"],
            )

        # =====================================================
        # Local Development
        # =====================================================

        else:

            self._workspace = WorkspaceClient(
                profile="data_profile"
            )