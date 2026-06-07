#!/bin/bash

echo "Step 1: Generating data..."
python src/data_generator.py

echo "Step 2: Cleaning data..."
python src/data_cleaning.py

echo "Step 3: Price elasticity analysis..."
python src/price_elasticity.py

echo "Step 4: Training demand model..."
python src/demand_forecasting.py

echo "Step 5: Running optimization..."
python src/optimization.py

echo "Step 6: Launching dashboard..."
streamlit run dashboard/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true