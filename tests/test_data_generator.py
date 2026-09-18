import pandas as pd

from src.data_generator import generate_demand, generate_dataset


def test_generate_demand_decreases_with_price():
    kwargs = dict(
        base_price=1000, competitor_price=1000, inventory=1000,
        is_holiday=False, is_weekend=False, month=6, discount=0,
    )
    low_price_demand = generate_demand(current_price=800, **kwargs)
    high_price_demand = generate_demand(current_price=1200, **kwargs)
    assert low_price_demand > high_price_demand


def test_generate_demand_capped_by_inventory():
    demand = generate_demand(
        base_price=1000, current_price=500, competitor_price=1000,
        inventory=5, is_holiday=True, is_weekend=True, month=11, discount=0.2,
    )
    assert 0 <= demand <= 5


def test_generate_dataset_shape_and_columns(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    df = generate_dataset(days=10)

    assert len(df) == 10 * 4  # 4 products
    assert (tmp_path / "data" / "sales_data.csv").exists()
    for col in ["Date", "Product_ID", "Units_Sold", "Revenue", "Inventory"]:
        assert col in df.columns
    assert (df["Units_Sold"] >= 0).all()
    assert (df["Inventory"] >= 0).all()
