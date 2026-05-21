import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
import pickle
from src.demand_forecasting import predict_demand 

BASE_PRICES = {
    'LAPTOP001': 75000,
    'PHONE001':  25000,
    'HEAD001':   5000,
    'WATCH001':  15000,
}
COST_RATIO = 0.6

def compute_profit(price, demand, product_id):
    cost = BASE_PRICES[product_id] * COST_RATIO
    return (price - cost) * demand

def optimize_price(product_id, competitor_price, inventory,
                   holiday, weekend, month, day_of_week, quarter,
                   discount=0.0, model=None, le=None):

    base = BASE_PRICES[product_id]
    prices = np.linspace(base * 0.7, base * 1.3, 50)

    results = []
    for p in prices:
        demand = predict_demand(
            price=p, competitor_price=competitor_price,
            discount=discount, inventory=inventory,
            holiday=holiday, weekend=weekend,
            month=month, day_of_week=day_of_week,
            quarter=quarter, product_id=product_id,
            model=model, le=le
        )
        revenue = p * demand
        profit = compute_profit(p, demand, product_id)
        results.append({
            'Price': round(p, 2),
            'Predicted_Demand': demand,
            'Revenue': round(revenue, 2),
            'Profit': round(profit, 2),
        })

    df = pd.DataFrame(results)
    best = df.loc[df['Profit'].idxmax()]

    print(f"\n🏆 Optimal Pricing for {product_id}")
    print(f"   Optimal Price    : ₹{best['Price']:,.2f}")
    print(f"   Predicted Demand : {best['Predicted_Demand']} units")
    print(f"   Expected Revenue : ₹{best['Revenue']:,.2f}")
    print(f"   Expected Profit  : ₹{best['Profit']:,.2f}")

    return best, df

def optimize_all_products(month=11, holiday=False, weekend=False, day_of_week=1, quarter=4):
    with open('data/demand_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('data/label_encoder.pkl', 'rb') as f:
        le = pickle.load(f)

    comp_prices = {
        'LAPTOP001': 74000, 'PHONE001': 24500,
        'HEAD001':   4800,  'WATCH001': 14500,
    }
    inventories = {
        'LAPTOP001': 120, 'PHONE001': 200,
        'HEAD001':   500, 'WATCH001': 180,
    }

    recommendations = {}
    for pid in BASE_PRICES:
        best, df = optimize_price(
            product_id=pid,
            competitor_price=comp_prices[pid],
            inventory=inventories[pid],
            holiday=holiday, weekend=weekend,
            month=month, day_of_week=day_of_week,
            quarter=quarter, model=model, le=le
        )
        recommendations[pid] = best

    return recommendations

if __name__ == '__main__':
    recs = optimize_all_products()