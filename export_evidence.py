"""Export reproducible Module 5 tables and charts from the MLflow server."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mlflow import MlflowClient

OUTPUT = Path("evidence")
OUTPUT.mkdir(exist_ok=True)
client = MlflowClient()

experiment = client.get_experiment_by_name("loan-default")
runs = client.search_runs(
    [experiment.experiment_id], order_by=["metrics.auc DESC"]
)

records = []
for run in runs:
    records.append(
        {
            "run_name": run.data.tags["mlflow.runName"],
            "run_id": run.info.run_id,
            "auc": run.data.metrics["auc"],
            "recall": run.data.metrics["recall"],
            "precision": run.data.metrics["precision"],
            "url": f"http://127.0.0.1:5000/#/experiments/{experiment.experiment_id}/runs/{run.info.run_id}",
        }
    )

names = [record["run_name"].replace("-class_weight=", "\nweight=") for record in records]
x = np.arange(len(records))
width = 0.24
fig, ax = plt.subplots(figsize=(11, 5.6))
for offset, metric, color in [
    (-width, "auc", "#24557A"),
    (0, "recall", "#2F7D6D"),
    (width, "precision", "#C07A3D"),
]:
    bars = ax.bar(
        x + offset,
        [record[metric] for record in records],
        width,
        label=metric.capitalize(),
        color=color,
    )
    ax.bar_label(bars, fmt="%.3f", padding=2, fontsize=7)
ax.set_ylim(0, 1.05)
ax.set_ylabel("Score")
ax.set_title("Loan default candidate comparison")
ax.set_xticks(x, names, fontsize=8)
ax.legend(ncols=3, frameon=False, loc="lower center")
ax.grid(axis="y", alpha=0.2)
fig.tight_layout()
fig.savefig(OUTPUT / "experiment_comparison.png", dpi=180)
plt.close(fig)

monitoring = client.get_experiment_by_name("loan-default-monitoring")
monitor_run = client.search_runs(
    [monitoring.experiment_id],
    filter_string="tags.mlflow.runName = 'daily-drift-check'",
    order_by=["attributes.start_time DESC"],
    max_results=1,
)[0]

histories = {}
for metric in [
    "psi_monthly_income_usd",
    "psi_amount_usd",
    "psi_late_payments",
    "mean_predicted_default",
    "actual_default_rate",
]:
    histories[metric] = [
        {"step": item.step, "value": item.value}
        for item in client.get_metric_history(monitor_run.info.run_id, metric)
    ]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
for metric, label, color in [
    ("psi_monthly_income_usd", "Monthly income", "#24557A"),
    ("psi_amount_usd", "Loan amount", "#2F7D6D"),
    ("psi_late_payments", "Late payments", "#C07A3D"),
]:
    points = histories[metric]
    ax1.plot(
        [point["step"] for point in points],
        [point["value"] for point in points],
        marker="o",
        label=label,
        color=color,
    )
ax1.axhline(0.1, color="#777777", linestyle="--", linewidth=1, label="Moderate 0.1")
ax1.axhline(0.2, color="#B33A3A", linestyle="--", linewidth=1, label="Significant 0.2")
ax1.set_ylabel("PSI")
ax1.set_title("Fourteen day feature drift")
ax1.grid(alpha=0.2)
ax1.legend(ncols=3, fontsize=8, frameon=False)

for metric, label, color in [
    ("mean_predicted_default", "Mean predicted default", "#24557A"),
    ("actual_default_rate", "Actual default rate", "#C07A3D"),
]:
    points = histories[metric]
    ax2.plot(
        [point["step"] for point in points],
        [point["value"] for point in points],
        marker="o",
        label=label,
        color=color,
    )
ax2.set_xlabel("Day")
ax2.set_ylabel("Rate")
ax2.set_xticks(range(1, 15))
ax2.grid(alpha=0.2)
ax2.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUTPUT / "drift_chart.png", dpi=180)
plt.close(fig)

registry = []
alias_targets = {
    alias: client.get_model_version_by_alias("loan-default", alias).version
    for alias in ["champion", "challenger"]
}
for version in client.search_model_versions(f"name = 'loan-default'"):
    registry.append(
        {
            "version": version.version,
            "aliases": [
                alias for alias, target in alias_targets.items() if target == version.version
            ],
            "run_id": version.run_id,
            "description": version.description,
        }
    )

evidence = {
    "experiment_id": experiment.experiment_id,
    "runs": records,
    "registry": registry,
    "monitoring_experiment_id": monitoring.experiment_id,
    "monitoring_run_id": monitor_run.info.run_id,
    "monitoring_run_url": f"http://127.0.0.1:5000/#/experiments/{monitoring.experiment_id}/runs/{monitor_run.info.run_id}",
    "metric_histories": histories,
}
(OUTPUT / "results.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(f"Exported {len(records)} experiment runs, {len(registry)} registry versions, and 14 drift days")
