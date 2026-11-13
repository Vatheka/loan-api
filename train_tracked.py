"""Train at least six loan-default candidates and track every run in MLflow."""
import matplotlib

matplotlib.use("Agg")

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import RocCurveDisplay, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from data import FEATURES, make_data

mlflow.set_experiment("loan-default")

df = make_data()
X_train, X_test, y_train, y_test = train_test_split(
    df[FEATURES], df.defaulted, test_size=0.2, random_state=42
)

candidates = [
    ("logreg", {"C": 0.1, "class_weight": None}),
    ("logreg", {"C": 0.1, "class_weight": "balanced"}),
    ("logreg", {"C": 1.0, "class_weight": "balanced"}),
    ("forest", {"max_depth": 4, "class_weight": None}),
    ("forest", {"max_depth": 8, "class_weight": "balanced"}),
    ("forest", {"max_depth": 12, "class_weight": "balanced"}),
]

for kind, params in candidates:
    if kind == "logreg":
        model = make_pipeline(StandardScaler(), LogisticRegression(**params))
    else:
        model = RandomForestClassifier(n_estimators=200, random_state=42, **params)

    run_name = f"{kind}-" + "-".join(f"{key}={value}" for key, value in params.items())
    with mlflow.start_run(run_name=run_name):
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        predicted = proba >= 0.5
        metrics = {
            "auc": roc_auc_score(y_test, proba),
            "recall": recall_score(y_test, predicted),
            "precision": precision_score(y_test, predicted),
        }

        mlflow.log_params({"model": kind, **{key: str(value) for key, value in params.items()}})
        mlflow.log_metrics(metrics)
        mlflow.log_figure(
            RocCurveDisplay.from_predictions(y_test, proba).figure_, "roc_curve.png"
        )
        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            signature=infer_signature(X_test, model.predict_proba(X_test)),
            input_example=X_test.head(3),
            pyfunc_predict_fn="predict_proba",
            skops_trusted_types=["sklearn.tree._tree.Tree"] if kind == "forest" else None,
        )
        print(
            f"{kind:<6} {params}  auc={metrics['auc']:.3f}  "
            f"recall={metrics['recall']:.3f}  precision={metrics['precision']:.3f}"
        )
