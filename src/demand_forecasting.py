import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor
import pickle, os

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

FEATURES = [
    'Actual_Price', 'Competitor_Price', 'Discount',
    'Inventory', 'Holiday_Flag', 'Weekend_Flag',
    'Month', 'Day_of_Week', 'Quarter',
    'Price_Gap', 'Price_Gap_Pct', 'Price_to_Base_Ratio',
    'Is_Discounted', 'Product_ID_enc'
]

def train_model(filepath='data/cleaned_sales_data.csv'):
    df = pd.read_csv(filepath, parse_dates=['Date'])


    le = LabelEncoder()
    df['Product_ID_enc'] = le.fit_transform(df['Product_ID'])

    X = df[FEATURES]
    y = df['Units_Sold']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )

    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"\nModel Trained!")
    print(f"   MAE  : {mae:.2f} units")
    print(f"   R²   : {r2:.4f}")

   
    importances = pd.Series(model.feature_importances_, index=FEATURES)
    print(f"\nTop Features:\n{importances.sort_values(ascending=False).head(8)}")

    os.makedirs('data', exist_ok=True)
    with open('data/demand_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('data/label_encoder.pkl', 'wb') as f:
        pickle.dump(le, f)

    print("\nModel saved → data/demand_model.pkl")
    return model, le

def predict_demand(price, competitor_price, discount, inventory,
                   holiday, weekend, month, day_of_week, quarter,
                   product_id, model=None, le=None):
    if model is None:
        with open('data/demand_model.pkl', 'rb') as f:
            model = pickle.load(f)
    if le is None:
        with open('data/label_encoder.pkl', 'rb') as f:
            le = pickle.load(f)

    actual_price = price * (1 - discount)
    price_gap = actual_price - competitor_price
    price_gap_pct = price_gap / competitor_price

   
    base_prices = {'LAPTOP001': 75000, 'PHONE001': 25000,
                   'HEAD001': 5000, 'WATCH001': 15000}
    base_price = base_prices.get(product_id, price)
    price_to_base = actual_price / base_price

    pid_enc = le.transform([product_id])[0]

    features = pd.DataFrame([{
        'Actual_Price': actual_price,
        'Competitor_Price': competitor_price,
        'Discount': discount,
        'Inventory': inventory,
        'Holiday_Flag': int(holiday),
        'Weekend_Flag': int(weekend),
        'Month': month,
        'Day_of_Week': day_of_week,
        'Quarter': quarter,
        'Price_Gap': price_gap,
        'Price_Gap_Pct': price_gap_pct,
        'Price_to_Base_Ratio': price_to_base,
        'Is_Discounted': int(discount > 0),
        'Product_ID_enc': pid_enc,
    }])

    pred = model.predict(features)[0]
    return max(0, int(pred))

if __name__ == '__main__':
    model, le = train_model()
    
    demand = predict_demand(
        price=75000, competitor_price=73000, discount=0.0,
        inventory=200, holiday=False, weekend=False,
        month=11, day_of_week=1, quarter=4,
        product_id='LAPTOP001', model=model, le=le
    )
    print(f"\nPredicted Demand (test): {demand} units")