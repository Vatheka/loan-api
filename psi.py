"""Population Stability Index for comparing feature distributions."""
import numpy as np


def psi(reference, current, bins=10):
    edges = np.quantile(reference, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    ref_share = np.histogram(reference, edges)[0] / len(reference)
    cur_share = np.histogram(current, edges)[0] / len(current)
    ref_share = np.clip(ref_share, 1e-6, None)
    cur_share = np.clip(cur_share, 1e-6, None)
    return float(np.sum((cur_share - ref_share) * np.log(cur_share / ref_share)))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    training_income = rng.normal(400, 150, 5000)
    same_month = rng.normal(400, 150, 800)
    after_floods = rng.normal(300, 150, 800)
    print(f"PSI, similar month:  {psi(training_income, same_month):.3f}")
    print(f"PSI, after floods:   {psi(training_income, after_floods):.3f}")
