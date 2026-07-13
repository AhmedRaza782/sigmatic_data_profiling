from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

print("Connected!")

print("\nCatalogs:")

for c in w.catalogs.list():
    print(c.name)