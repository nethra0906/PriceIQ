#!/bin/bash
set -e

if [ -f "data/demand_model.pkl" ] && [ -f "data/label_encoder.pkl" ] && [ -f "data/cleaned_sales_data.csv" ]; then
    echo "Existing pipeline artifacts found in data/ — skipping regeneration."
    echo "Delete data/demand_model.pkl to force a full rebuild."
else
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
fi

echo "Step 6: Launching dashboard..."
exec streamlit run dashboard/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
