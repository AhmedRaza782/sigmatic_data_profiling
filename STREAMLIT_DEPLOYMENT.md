# Streamlit Cloud Deployment Guide

## Local Development Setup

### 1. Create a local secrets file

Copy the example secrets file:
```bash
cp data_profile/.streamlit/secrets.toml.example data_profile/.streamlit/secrets.toml
```

### 2. Fill in your Databricks credentials

Edit `data_profile/.streamlit/secrets.toml` with your actual Databricks credentials:

```toml
DATABRICKS_HOST = "https://dbc-xxxxxxxx.cloud.databricks.com"
DATABRICKS_CLIENT_ID = "your-client-id"
DATABRICKS_CLIENT_SECRET = "your-client-secret"
```

### 3. Run the app locally

```bash
cd data_profile
streamlit run app/app.py
```

**NOTE:** The `secrets.toml` file is in `.gitignore` and should NEVER be committed to git.

---

## Streamlit Cloud Deployment

### 1. Deploy your app

Push your code to GitHub (already done).

Visit https://streamlit.io/cloud and connect your repository.

### 2. Add Secrets to Streamlit Cloud

After deployment, in your Streamlit Cloud app dashboard:

1. Go to **Settings** → **Secrets**
2. Add the following three secrets:

```
DATABRICKS_HOST=https://dbc-xxxxxxxx.cloud.databricks.com
DATABRICKS_CLIENT_ID=your-client-id
DATABRICKS_CLIENT_SECRET=your-client-secret
```

3. Click **Save**

The app will automatically restart with the new secrets as environment variables.

---

## How Authentication Works

### Local Development
- `streamlit run` reads from `data_profile/.streamlit/secrets.toml`
- Secrets become available as environment variables

### Streamlit Cloud
- Secrets you add in the dashboard become environment variables
- No need for `.databrickscfg` or any local files

### Code
Both `databricks_client.py` and `sql_client.py` now read these environment variables:

```python
from databricks.sdk import WorkspaceClient

workspace = WorkspaceClient(
    host=os.environ["DATABRICKS_HOST"],
    client_id=os.environ["DATABRICKS_CLIENT_ID"],
    client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
)
```

---

## Troubleshooting

**Error: `KeyError: 'DATABRICKS_HOST'`**

→ You haven't set up the secrets file (local) or secrets in dashboard (Streamlit Cloud)

**Error: `ValueError: Unable to verify credentials`**

→ Check that your credentials are correct and still active in Databricks

**Error: `databricks-sql-connector is not installed`**

→ Run `pip install databricks-sql-connector>=4.0.0` locally, or ensure it's in `requirements.txt` for Streamlit Cloud
