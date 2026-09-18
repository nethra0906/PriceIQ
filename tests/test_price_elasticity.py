import numpy as np
import pandas as pd

from src.price_elasticity import compute_elasticity


def test_compute_elasticity_recovers_known_slope():
    rng = np.random.default_rng(42)
    prices = rng.uniform(500, 1500, size=200)
    true_elasticity = -1.8
    demand = 1000 * (prices / 1000) ** true_elasticity

    df = pd.DataFrame({
        "Product_ID": "LAPTOP001",
        "Date": pd.date_range("2023-01-01", periods=200),
        "Actual_Price": prices,
        "Units_Sold": demand.astype(int).clip(min=1),
    })

    elasticity = compute_elasticity(df, "LAPTOP001")

    assert elasticity < 0
    assert abs(elasticity - true_elasticity) < 0.3
