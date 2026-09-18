import numpy as np
import pandas as pd

from src.demand_forecasting import train_model, predict_demand
from src.optimization import optimize_price, BASE_PRICES


def _make_cleaned_dataset(n_per_product=150, seed=7):
    rng = np.random.default_rng(seed)
    rows = []
    for product_id, base_price in BASE_PRICES.items():
        for i in range(n_per_product):
            actual_price = base_price * rng.uniform(0.8, 1.2)
            competitor_price = base_price * rng.uniform(0.8, 1.2)
            discount = rng.choice([0, 0.05, 0.1])
            demand = 100 * (actual_price / base_price) ** -1.8
            demand *= rng.uniform(0.9, 1.1)

            rows.append({
                "Date": pd.Timestamp("2023-01-01") + pd.Timedelta(days=i),
                "Product_ID": product_id,
                "Actual_Price": actual_price,
                "Competitor_Price": competitor_price,
                "Discount": discount,
                "Inventory": rng.integers(50, 400),
                "Holiday_Flag": int(rng.random() < 0.1),
                "Weekend_Flag": int(rng.random() < 0.3),
                "Month": rng.integers(1, 13),
                "Day_of_Week": i % 7,
                "Quarter": rng.integers(1, 5),
                "Price_Gap": actual_price - competitor_price,
                "Price_Gap_Pct": (actual_price - competitor_price) / competitor_price,
                "Price_to_Base_Ratio": actual_price / base_price,
                "Is_Discounted": int(discount > 0),
                "Units_Sold": max(0, int(demand)),
            })
    return pd.DataFrame(rows)


def test_train_predict_and_optimize_round_trip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    df = _make_cleaned_dataset()
    csv_path = tmp_path / "cleaned.csv"
    df.to_csv(csv_path, index=False)

    model, le = train_model(filepath=str(csv_path))

    demand = predict_demand(
        price=75000, competitor_price=73000, discount=0.0,
        inventory=200, holiday=False, weekend=False,
        month=11, day_of_week=1, quarter=4,
        product_id="LAPTOP001", model=model, le=le,
    )
    assert isinstance(demand, int)
    assert demand >= 0

    best, opt_df = optimize_price(
        product_id="LAPTOP001", competitor_price=73000, inventory=200,
        holiday=False, weekend=False, month=11, day_of_week=1, quarter=4,
        model=model, le=le,
    )
    base = BASE_PRICES["LAPTOP001"]
    assert base * 0.7 <= best["Price"] <= base * 1.3
    assert len(opt_df) == 50
