"""Move the champion alias to a specified registered model version."""
import argparse

from mlflow import MlflowClient

parser = argparse.ArgumentParser()
parser.add_argument("version", help="Registered loan-default version")
args = parser.parse_args()

client = MlflowClient()
client.set_registered_model_alias("loan-default", "champion", args.version)
version = client.get_model_version_by_alias("loan-default", "champion")
print(f"champion -> loan-default version {version.version}")
