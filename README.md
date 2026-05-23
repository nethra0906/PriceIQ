# PriceIQ - Dynamic Pricing Engine

> AI-powered real-time price optimization engine for e-commerce retail analytics.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?style=flat&logo=streamlit)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange?style=flat)

---

## What is PriceIQ?

PriceIQ is a dynamic pricing engine that simulates what companies like Amazon, Uber, and Flipkart do every day - automatically adjusting product prices based on demand, inventory, competitor pricing, and seasonal trends to maximize revenue and profit.

---

## Features

- **Demand Forecasting** - XGBoost model predicts units sold at any price point
- **Price Elasticity Analysis** - Measures how sensitive demand is to price changes
- **Optimization Engine** - Grid search across price range to find max-profit price
- **Competitor Intelligence** - Tracks price gap and triggers undercut alerts
- **Inventory Risk Alerts** - Warns when stock is critically low
- **Interactive Dashboard** - Built with Streamlit + Plotly for real-time insights

---

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.10+ |
| ML Model | XGBoost, Scikit-learn |
| Forecasting | Prophet |
| Optimization | Scipy, NumPy Grid Search |
| Dashboard | Streamlit, Plotly |
| Data | Pandas, Faker (synthetic) |

---


## Quickstart

**1. Clone the repo**
```bash
git clone https://github.com/yourusername/PriceIQ.git
cd PriceIQ
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the pipeline**
```bash
python src/data_generator.py
python src/data_cleaning.py
python src/price_elasticity.py
python src/demand_forecasting.py
python src/optimization.py
```

**5. Launch dashboard**
```bash
streamlit run dashboard/app.py
```

---

## Dashboard Preview

> Real-time optimal price, demand curve, revenue vs profit chart, competitor analysis, and inventory alerts — all in one view.

---

## Model Performance

| Metric | Value |
|---|---|
| Algorithm | XGBoost Regressor |
| MAE | ~3–5 units |
| R² Score | ~0.85+ |
| Training Data | 2 years × 4 products |

---

## Future Improvements

- [ ] Reinforcement Learning pricing agent (Q-Learning / DQN)
- [ ] LLM-powered insight layer explaining price changes
- [ ] Real-time competitor price scraping
- [ ] REST API with FastAPI for integration
- [ ] Docker containerization


