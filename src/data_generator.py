import pandas as pd
import numpy as np
from faker import Faker
import random
import os

fake = Faker()
np.random.seed(42)
random.seed(42)

PRODUCTS = {
    'LAPTOP001': {'name': 'Laptop Pro', 'base_price': 75000, 'category': 'Laptops'},
    'PHONE001':  {'name': 'SmartPhone X', 'base_price': 25000, 'category': 'Phones'},
    'HEAD001':   {'name': 'Headphones Z', 'base_price': 5000,  'category': 'Headphones'},
    'WATCH001':  {'name': 'SmartWatch S', 'base_price': 15000, 'category': 'SmartWatches'},
}

FESTIVALS = {
    (1, 26): 'Republic Day',
    (8, 15): 'Independence Day',
    (10, 2): 'Gandhi Jayanti',
    (11, 1): 'Diwali',
    (12, 25): 'Christmas',
    (1, 1):  'New Year',
}

def is_festival(date):
    return (date.month, date.day) in FESTIVALS

def generate_demand(base_price, current_price, competitor_price, inventory,
                    is_holiday, is_weekend, month, discount):
    # Price elasticity effect
    price_ratio = current_price / base_price
    elasticity = -1.8
    demand = 100 * (price_ratio ** elasticity)

    # Competitor effect
    comp_gap = (current_price - competitor_price) / competitor_price
    demand *= (1 - 0.5 * comp_gap)

    # Seasonal effect
    seasonal_boost = {11: 1.5, 12: 1.4, 10: 1.2, 1: 1.1}.get(month, 1.0)
    demand *= seasonal_boost

    # Holiday / weekend effect
    if is_holiday: demand *= 1.3
    if is_weekend: demand *= 1.15

    # Discount effect
    if discount > 0: demand *= (1 + discount * 2)

    # Inventory constraint
    demand = min(demand, inventory)

    # Add noise
    demand *= np.random.uniform(0.85, 1.15)
    return max(0, int(demand))

def generate_dataset(days=730):
    records = []
    start_date = pd.Timestamp('2023-01-01')

    for product_id, product_info in PRODUCTS.items():
        inventory = random.randint(300, 500)
        base_price = product_info['base_price']

        for i in range(days):
            date = start_date + pd.Timedelta(days=i)

            current_price = base_price * np.random.uniform(0.85, 1.15)
            competitor_price = base_price * np.random.uniform(0.80, 1.20)
            discount = round(random.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20]), 2)
            actual_price = current_price * (1 - discount)
            holiday = is_festival(date)
            weekend = date.dayofweek >= 5
            month = date.month

            units_sold = generate_demand(
                base_price, actual_price, competitor_price,
                inventory, holiday, weekend, month, discount
            )

            inventory = max(0, inventory - units_sold)
            if inventory < 50:
                inventory = random.randint(200, 400)

            records.append({
                'Date': date,
                'Product_ID': product_id,
                'Product_Name': product_info['name'],
                'Category': product_info['category'],
                'Base_Price': base_price,
                'Current_Price': round(current_price, 2),
                'Discount': discount,
                'Actual_Price': round(actual_price, 2),
                'Competitor_Price': round(competitor_price, 2),
                'Units_Sold': units_sold,
                'Inventory': inventory,
                'Holiday_Flag': int(holiday),
                'Weekend_Flag': int(weekend),
                'Month': month,
                'Day_of_Week': date.dayofweek,
                'Quarter': date.quarter,
                'Revenue': round(actual_price * units_sold, 2),
            })

    df = pd.DataFrame(records)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/sales_data.csv', index=False)
    print(f"✅ Dataset generated: {len(df)} rows")
    print(df.head())
    return df

if __name__ == '__main__':
    generate_dataset()