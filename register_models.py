"""Register the selected candidates and assign champion/challenger roles."""
import mlflow
from mlflow import MlflowClient

EXPERIMENT = "loan-default"
MODEL_NAME = "loan-default"
SELECTIONS = [
    (
        "logreg-C=1.0-class_weight=balanced",
        "champion",
        "Balanced logistic regression selected for its highest recall (0.865), with AUC 0.923 and precision 0.611.",
    ),
    (
        "forest-max_depth=8-class_weight=balanced",
        "challenger",
        "Balanced depth-8 random forest retained as challenger for its best AUC (0.925), recall 0.788, and precision 0.742.",
    ),
]

client = MlflowClient()
experiment = client.get_experiment_by_name(EXPERIMENT)
if experiment is None:
    raise RuntimeError(f"Experiment {EXPERIMENT!r} does not exist")

for run_name, alias, description in SELECTIONS:
    runs = client.search_runs(
        [experiment.experiment_id],
        filter_string=f"tags.mlflow.runName = '{run_name}'",
        order_by=["attributes.start_time DESC"],
        max_results=1,
    )
    if not runs:
        raise RuntimeError(f"Run {run_name!r} was not found")

    run = runs[0]
    version = mlflow.register_model(
        model_uri=f"runs:/{run.info.run_id}/model", name=MODEL_NAME
    )
    client.update_model_version(
        name=MODEL_NAME, version=version.version, description=description
    )
    client.set_registered_model_alias(MODEL_NAME, alias, version.version)
    print(
        f"{alias}: version {version.version}, run {run.info.run_id}, "
        f"auc={run.data.metrics['auc']:.3f}, recall={run.data.metrics['recall']:.3f}, "
        f"precision={run.data.metrics['precision']:.3f}"
    )
