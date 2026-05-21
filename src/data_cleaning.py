import pandas as pd
import numpy as np
from scipy import stats

def load_and_clean(filepath='data/sales_data.csv'):
    df = pd.read_csv(filepath, parse_dates=['Date'])
    print(f"📦 Raw data shape: {df.shape}")

    # ── Missing values ──────────────────────────────────────────────
    print("\n🔍 Missing values:\n", df.isnull().sum())
    df.dropna(inplace=True)

    # ── Outlier removal using Z-score ───────────────────────────────
    numeric_cols = ['Units_Sold', 'Current_Price', 'Competitor_Price', 'Revenue']
    for col in numeric_cols:
        z_scores = np.abs(stats.zscore(df[col]))
        before = len(df)
        df = df[z_scores < 3]
        print(f"  Removed {before - len(df)} outliers from {col}")

    # ── Feature engineering ─────────────────────────────────────────
    df['Price_Gap'] = df['Actual_Price'] - df['Competitor_Price']
    df['Price_Gap_Pct'] = df['Price_Gap'] / df['Competitor_Price']
    df['Inventory_Level'] = pd.cut(
        df['Inventory'],
        bins=[0, 50, 150, 300, np.inf],
        labels=['Critical', 'Low', 'Medium', 'High']
    )
    df['Season'] = df['Month'].map({
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Autumn', 10: 'Autumn', 11: 'Autumn'
    })
    df['Is_Discounted'] = (df['Discount'] > 0).astype(int)
    df['Price_to_Base_Ratio'] = df['Actual_Price'] / df['Base_Price']

    print(f"\n✅ Clean data shape: {df.shape}")
    df.to_csv('data/cleaned_sales_data.csv', index=False)
    print("💾 Saved → data/cleaned_sales_data.csv")
    return df

if __name__ == '__main__':
    df = load_and_clean()
    print("\n📊 Summary:\n", df.describe())