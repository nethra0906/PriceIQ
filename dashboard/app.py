import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pickle
from datetime import date

from src.demand_forecasting import predict_demand
from src.optimization import optimize_price, BASE_PRICES, COST_RATIO

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dynamic Pricing Engine",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f, #2d6a9f);
        border-radius: 12px; padding: 20px; color: white;
        text-align: center; margin: 4px;
    }
    .metric-card h2 { font-size: 2rem; margin: 0; }
    .metric-card p  { font-size: 0.85rem; opacity: 0.8; margin: 0; }
    .alert-box {
        background: #fff3cd; border-left: 4px solid #ffc107;
        padding: 12px 16px; border-radius: 6px; margin: 8px 0;
    }
    .success-box {
        background: #d4edda; border-left: 4px solid #28a745;
        padding: 12px 16px; border-radius: 6px; margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Load model ────────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    with open('data/demand_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('data/label_encoder.pkl', 'rb') as f:
        le = pickle.load(f)
    return model, le

@st.cache_data
def load_data():
    return pd.read_csv('data/cleaned_sales_data.csv', parse_dates=['Date'])

try:
    model, le = load_model()
    df = load_data()
    model_loaded = True
except:
    model_loaded = False
    st.error("⚠️ Train the model first: `python src/demand_forecasting.py`")

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/price-tag.png", width=60)
st.sidebar.title("⚙️ Pricing Controls")

product_map = {
    'LAPTOP001': 'Laptop Pro (₹75K)',
    'PHONE001':  'SmartPhone X (₹25K)',
    'HEAD001':   'Headphones Z (₹5K)',
    'WATCH001':  'SmartWatch S (₹15K)',
}
selected_pid = st.sidebar.selectbox(
    "Select Product",
    list(product_map.keys()),
    format_func=lambda x: product_map[x]
)

base = BASE_PRICES[selected_pid]
today = date.today()

st.sidebar.markdown("---")
st.sidebar.subheader("Market Conditions")
competitor_price = st.sidebar.number_input(
    "Competitor Price (₹)", min_value=int(base * 0.5), max_value=int(base * 1.5),
    value=int(base * 0.97), step=100
)
inventory = st.sidebar.slider("Current Inventory", 10, 500, 150)
discount = st.sidebar.slider("Discount (%)", 0, 30, 0) / 100
is_holiday = st.sidebar.checkbox("🎉 Festival / Holiday")
is_weekend = today.weekday() >= 5

st.sidebar.markdown("---")
month = st.sidebar.slider("Month", 1, 12, today.month)
quarter = (month - 1) // 3 + 1

# ── Main ──────────────────────────────────────────────────────────────────────
st.title("💹 Dynamic Pricing Engine")
st.markdown("*Real-time price optimization for maximum profit*")

if model_loaded:

    # Run optimization
    best, opt_df = optimize_price(
        product_id=selected_pid,
        competitor_price=competitor_price,
        inventory=inventory,
        holiday=is_holiday,
        weekend=is_weekend,
        month=month,
        day_of_week=today.weekday(),
        quarter=quarter,
        discount=discount,
        model=model, le=le
    )

    # Current price demand
    current_demand = predict_demand(
        price=base, competitor_price=competitor_price,
        discount=discount, inventory=inventory,
        holiday=is_holiday, weekend=is_weekend,
        month=month, day_of_week=today.weekday(),
        quarter=quarter, product_id=selected_pid,
        model=model, le=le
    )
    current_revenue = base * (1 - discount) * current_demand
    optimal_revenue = best['Revenue']
    revenue_uplift = ((optimal_revenue - current_revenue) / max(current_revenue, 1)) * 100
    price_gap = base * (1 - discount) - competitor_price

    # ── KPI Row ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🎯 Optimal Price", f"₹{best['Price']:,.0f}",
                  delta=f"{((best['Price'] - base)/base*100):+.1f}% vs base")
    with c2:
        st.metric("📦 Predicted Demand", f"{int(best['Predicted_Demand'])} units",
          delta=f"{int(best['Predicted_Demand']) - int(current_demand):+d} vs current")
    with c3:
        st.metric("💰 Expected Revenue", f"₹{best['Revenue']:,.0f}",
                  delta=f"{revenue_uplift:+.1f}% uplift")
    with c4:
        st.metric("📊 Expected Profit", f"₹{best['Profit']:,.0f}")

    st.markdown("---")

    # ── Alerts ────────────────────────────────────────────────────────────────
    if inventory < 50:
        st.markdown('<div class="alert-box">⚠️ <b>Low Inventory Alert:</b> Only '
                    f'{inventory} units left. Consider raising price to manage demand.</div>',
                    unsafe_allow_html=True)
    if price_gap > base * 0.05:
        st.markdown('<div class="alert-box">⚠️ <b>Competitor Undercut Alert:</b> '
                    f'Your price is ₹{abs(price_gap):,.0f} above competitor.</div>',
                    unsafe_allow_html=True)
    if revenue_uplift > 5:
        st.markdown(f'<div class="success-box">✅ <b>Optimization Opportunity:</b> '
                    f'Switching to optimal price could increase revenue by {revenue_uplift:.1f}%</div>',
                    unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Price vs Revenue Curve")
        fig = px.line(opt_df, x='Price', y='Revenue',
                      title='Revenue at Different Price Points',
                      color_discrete_sequence=['#2d6a9f'])
        fig.add_vline(x=best['Price'], line_dash='dash', line_color='green',
                      annotation_text=f"Optimal ₹{best['Price']:,.0f}")
        fig.add_vline(x=base * (1 - discount), line_dash='dot', line_color='red',
                      annotation_text="Current")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📉 Demand Curve")
        fig2 = px.line(opt_df, x='Price', y='Predicted_Demand',
                       title='Demand at Different Price Points',
                       color_discrete_sequence=['#e05c2e'])
        fig2.add_vline(x=best['Price'], line_dash='dash', line_color='green',
                       annotation_text="Optimal")
        fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

    # ── Profit Surface ────────────────────────────────────────────────────────
    st.subheader("💡 Revenue vs Profit Comparison")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=opt_df['Price'], y=opt_df['Revenue'],
                              name='Revenue', fill='tozeroy',
                              line=dict(color='steelblue')))
    fig3.add_trace(go.Scatter(x=opt_df['Price'], y=opt_df['Profit'],
                              name='Profit', fill='tozeroy',
                              line=dict(color='green')))
    fig3.add_vline(x=best['Price'], line_dash='dash', line_color='red',
                   annotation_text=f"Best: ₹{best['Price']:,.0f}")
    fig3.update_layout(
        title='Revenue & Profit across Price Range',
        xaxis_title='Price (₹)', yaxis_title='Amount (₹)',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h')
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Historical Trends ─────────────────────────────────────────────────────
    st.subheader(f"📆 Historical Sales — {product_map[selected_pid]}")
    hist = df[df['Product_ID'] == selected_pid].copy()
    hist_monthly = hist.set_index('Date').resample('ME').agg({
        'Units_Sold': 'sum',
        'Revenue': 'sum',
        'Actual_Price': 'mean'
    }).reset_index()

    col3, col4 = st.columns(2)
    with col3:
        fig4 = px.bar(hist_monthly, x='Date', y='Units_Sold',
                      title='Monthly Units Sold',
                      color_discrete_sequence=['#3498db'])
        fig4.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig4, use_container_width=True)

    with col4:
        fig5 = px.line(hist_monthly, x='Date', y='Revenue',
                       title='Monthly Revenue (₹)',
                       color_discrete_sequence=['#2ecc71'])
        fig5.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig5, use_container_width=True)

    # ── Competitor Table ──────────────────────────────────────────────────────
    st.subheader("🏪 Competitor Analysis")
    comp_data = {
        'Metric': ['Your Price', 'Competitor Price', 'Price Gap', 'Gap %', 'Recommendation'],
        'Value': [
            f"₹{base * (1 - discount):,.0f}",
            f"₹{competitor_price:,.0f}",
            f"₹{price_gap:+,.0f}",
            f"{(price_gap / competitor_price * 100):+.1f}%",
            "✅ Competitive" if abs(price_gap / competitor_price) < 0.05 else
            ("⬇️ Lower your price" if price_gap > 0 else "⬆️ Room to increase")
        ]
    }
    st.table(pd.DataFrame(comp_data))

    # ── Raw optimization table ────────────────────────────────────────────────
    with st.expander("🔢 Full Optimization Table"):
        st.dataframe(opt_df.style.highlight_max(subset=['Profit'], color='lightgreen'),
                     use_container_width=True)