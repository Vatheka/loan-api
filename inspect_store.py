"""Read MLflow's SQLite backend and local artifact store for evidence."""
import sqlite3
from pathlib import Path

db = sqlite3.connect("mlflow.db")
tables = [
    row[0]
    for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
]
print(
    len(tables),
    "tables, including:",
    [
        table
        for table in tables
        if table
        in (
            "experiments",
            "runs",
            "params",
            "latest_metrics",
            "registered_models",
            "model_versions",
        )
    ],
)

for name, auc in db.execute(
    """
    SELECT r.name, ROUND(m.value, 3)
    FROM runs AS r JOIN latest_metrics AS m ON m.run_uuid = r.run_uuid
    WHERE m.key = 'auc'
    ORDER BY m.value DESC
    """
):
    print(f"{auc}  {name}")

for png in sorted(Path("mlartifacts").rglob("roc_curve.png")):
    print(png)
