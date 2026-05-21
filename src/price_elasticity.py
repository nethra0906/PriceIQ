import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def compute_elasticity(df, product_id):
    """Compute price elasticity of demand for one product."""
    prod = df[df['Product_ID'] == product_id].copy()
    prod = prod.sort_values('Date')


    prod = prod[prod['Units_Sold'] > 0]
    log_price = np.log(prod['Actual_Price'])
    log_demand = np.log(prod['Units_Sold'])


    from numpy.polynomial import polynomial as P
    coeffs = np.polyfit(log_price, log_demand, 1)
    elasticity = coeffs[0]   # slope = elasticity

    print(f"\nProduct: {product_id}")
    print(f"   Price Elasticity: {elasticity:.3f}")
    if elasticity < -1:
        print("   → Elastic demand (price-sensitive customers)")
    elif elasticity > -1:
        print("   → Inelastic demand (customers are less price-sensitive)")

    return elasticity

def plot_demand_curve(df, product_id):
    prod = df[df['Product_ID'] == product_id].copy()
    prod['Price_Bin'] = pd.cut(prod['Actual_Price'], bins=10)
    avg = prod.groupby('Price_Bin', observed=True)['Units_Sold'].mean().reset_index()
    avg['Price_Mid'] = avg['Price_Bin'].apply(lambda x: x.mid)

    plt.figure(figsize=(8, 5))
    plt.plot(avg['Price_Mid'], avg['Units_Sold'], marker='o', color='steelblue', linewidth=2)
    plt.xlabel('Price (₹)')
    plt.ylabel('Average Units Sold')
    plt.title(f'Demand Curve — {product_id}')
    plt.grid(alpha=0.3)
    os.makedirs('data', exist_ok=True)
    plt.savefig(f'data/demand_curve_{product_id}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f" Demand curve saved.")

def analyze_all_products(filepath='data/cleaned_sales_data.csv'):
    df = pd.read_csv(filepath, parse_dates=['Date'])
    elasticities = {}
    for pid in df['Product_ID'].unique():
        e = compute_elasticity(df, pid)
        plot_demand_curve(df, pid)
        elasticities[pid] = e
    return elasticities

if __name__ == '__main__':
    analyze_all_products()