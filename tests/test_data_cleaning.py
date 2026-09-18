import pandas as pd

from src.data_cleaning import load_and_clean


def _make_raw_csv(path):
    rows = []
    for i in range(50):
        rows.append({
            "Date": pd.Timestamp("2023-01-01") + pd.Timedelta(days=i),
            "Product_ID": "LAPTOP001",
            "Product_Name": "Laptop Pro",
            "Category": "Laptops",
            "Base_Price": 75000,
            "Current_Price": 75000 + i * 10,
            "Discount": 0.0,
            "Actual_Price": 75000 + i * 10,
            "Competitor_Price": 74000,
            "Units_Sold": 20 + (i % 5),
            "Inventory": 300 - i,
            "Holiday_Flag": 0,
            "Weekend_Flag": int(i % 7 >= 5),
            "Month": 1,
            "Day_of_Week": i % 7,
            "Quarter": 1,
            "Revenue": (75000 + i * 10) * (20 + (i % 5)),
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)


def test_load_and_clean_adds_derived_columns(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw_path = tmp_path / "raw.csv"
    _make_raw_csv(raw_path)

    df = load_and_clean(filepath=str(raw_path))

    for col in ["Price_Gap", "Price_Gap_Pct", "Inventory_Level", "Season",
                "Is_Discounted", "Price_to_Base_Ratio"]:
        assert col in df.columns

    assert df.isnull().sum().sum() == 0
    assert (tmp_path / "data" / "cleaned_sales_data.csv").exists()
