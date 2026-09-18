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


st.set_page_config(
    page_title="PriceIQ",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
   
    .block-container { padding-top: 1.5rem; max-width: 96%; }
    
   
    div[data-testid="stMetric"] {
        background-color: var(--background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
    }
    

    div[data-testid="stPlotlyChart"] {
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.02);
    }
</style>
""", unsafe_allow_html=True)


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
except Exception:
    model_loaded = False
    st.error("System Error: ML Model binaries or clean historical targets missing. Please run `python src/demand_forecasting.py` to compile optimization artifacts.")

st.sidebar.title("Pricing Controls")
st.sidebar.caption("Adjust market conditions to simulate a pricing scenario.")

product_map = {
    'LAPTOP001': 'Laptop Pro (₹75K)',
    'PHONE001':  'SmartPhone X (₹25K)',
    'HEAD001':   'Headphones Z (₹5K)',
    'WATCH001':  'SmartWatch S (₹15K)',
}

selected_pid = st.sidebar.selectbox(
    "Product",
    list(product_map.keys()),
    format_func=lambda x: product_map[x]
)

base = BASE_PRICES[selected_pid]
today = date.today()

st.sidebar.markdown("---")
st.sidebar.subheader("Market Signals")

competitor_price = st.sidebar.number_input(
    "Competitor Price (₹)",
    min_value=int(base * 0.5),
    max_value=int(base * 1.5),
    value=int(base * 0.97),
    step=100
)

inventory = st.sidebar.slider("Inventory On Hand", 10, 500, 150)
discount = st.sidebar.slider("Discount (%)", 0, 30, 0) / 100
is_holiday = st.sidebar.checkbox("Holiday / Festival Period")
is_weekend = today.weekday() >= 5

st.sidebar.markdown("---")
st.sidebar.subheader("Time Period")
month = st.sidebar.slider("Month", 1, 12, today.month)
quarter = (month - 1) // 3 + 1


st.title("PriceIQ")
st.caption("Finds the price that maximizes profit, based on demand forecasts and current market conditions.")
st.markdown("---")

if model_loaded:

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


    price_delta_pct = ((best['Price'] - base) / base * 100)
    demand_delta_abs = int(best['Predicted_Demand']) - int(current_demand)

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    with m_col1:
        st.metric(
            label="Optimal Price",
            value=f"₹{best['Price']:,.0f}",
            delta=f"{price_delta_pct:+.1f}% vs list price",
            delta_color="normal"
        )
    with m_col2:
        st.metric(
            label="Predicted Demand",
            value=f"{int(best['Predicted_Demand']):,} units",
            delta=f"{demand_delta_abs:+,} units vs current price",
            delta_color="normal"
        )
    with m_col3:
        st.metric(
            label="Projected Revenue",
            value=f"₹{best['Revenue']:,.0f}",
            delta=f"{revenue_uplift:+.1f}% vs current price",
            delta_color="normal"
        )
    with m_col4:
        st.metric(
            label="Projected Profit",
            value=f"₹{best['Profit']:,.0f}",
            delta="at optimal price",
            delta_color="off"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    
    if inventory < 50 or price_gap > (base * 0.05) or revenue_uplift > 5:
        with st.container():
            if inventory < 50:
                st.warning(f"**Low Inventory Alert:** Only `{inventory}` units on hand. Consider raising price to slow demand and protect remaining stock.")
            if price_gap > (base * 0.05):
                st.error(f"**Priced Above Competitor:** Current price is **₹{abs(price_gap):,.0f}** above the competitor's price, which risks losing price-sensitive customers.")
            if revenue_uplift > 5:
                st.success(f"**Revenue Opportunity:** Moving to the optimal price could lift revenue by **{revenue_uplift:.1f}%**.")

   
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Revenue by Price")
        fig = px.line(
            opt_df, x='Price', y='Revenue',
            title='Revenue vs Price',
            color_discrete_sequence=['#1E3A8A']
        )
        fig.add_vline(x=best['Price'], line_dash='dash', line_color='#10B981',
                      annotation_text=f"Optimal Price (₹{best['Price']:,.0f})", annotation_position="top left")
        fig.add_vline(x=base * (1 - discount), line_dash='dot', line_color='#EF4444',
                      annotation_text="Current Price", annotation_position="bottom left")
        fig.update_layout(
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Price (₹)"),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Revenue (₹)")
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col2:
        st.subheader("Demand by Price")
        fig2 = px.line(
            opt_df, x='Price', y='Predicted_Demand',
            title='Predicted Demand vs Price',
            color_discrete_sequence=['#F59E0B']
        )
        fig2.add_vline(x=best['Price'], line_dash='dash', line_color='#10B981', annotation_text="Optimal Price")
        fig2.update_layout(
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Price (₹)"),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Predicted Demand (Units)")
        )
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

   
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Revenue vs Profit by Price")

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=opt_df['Price'], y=opt_df['Revenue'],
                              name='Revenue', fill='tozeroy',
                              line=dict(color='#3B82F6', width=2.5)))
    fig3.add_trace(go.Scatter(x=opt_df['Price'], y=opt_df['Profit'],
                              name='Profit', fill='tozeroy',
                              line=dict(color='#10B981', width=2.5)))
    fig3.add_vline(x=best['Price'], line_dash='dash', line_color='#EF4444',
                   annotation_text=f"Max Profit Price: ₹{best['Price']:,.0f}", annotation_position="top right")
    fig3.update_layout(
        title='Revenue and Profit Across Price Range',
        xaxis_title='Price (₹)', yaxis_title='Amount (₹)',
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    
    st.markdown("---")
    st.subheader(f"Historical Performance — {product_map[selected_pid]}")
    
    hist = df[df['Product_ID'] == selected_pid].copy()
    hist_monthly = hist.set_index('Date').resample('ME').agg({
        'Units_Sold': 'sum',
        'Revenue': 'sum',
        'Actual_Price': 'mean'
    }).reset_index()

    col3, col4 = st.columns(2)
    with col3:
        fig4 = px.bar(
            hist_monthly, x='Date', y='Units_Sold',
            title='Monthly Units Sold',
            color_discrete_sequence=['#94A3B8']
        )
        fig4.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False, title="Month"),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Units Sold")
        )
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

    with col4:
        fig5 = px.line(
            hist_monthly, x='Date', y='Revenue',
            title='Monthly Revenue',
            color_discrete_sequence=['#0F172A']
        )
        fig5.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False, title="Month"),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Revenue (₹)")
        )
        st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar': False})

    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Competitor Comparison")

    comp_matrix = pd.DataFrame({
        'Metric': [
            'Our Price',
            'Competitor Price',
            'Price Difference',
            'Difference (%)',
            'Recommendation'
        ],
        'Value': [
            f"₹{base * (1 - discount):,.0f}",
            f"₹{competitor_price:,.0f}",
            f"₹{price_gap:+,.0f}",
            f"{(price_gap / competitor_price * 100):+.1f}%",
            "Priced at parity" if abs(price_gap / competitor_price) < 0.05 else
            ("Priced above competitor — consider lowering" if price_gap > 0 else "Priced below competitor — room to raise")
        ]
    })

    st.dataframe(
        comp_matrix,
        column_config={
            "Metric": st.column_config.TextColumn("Metric"),
            "Value": st.column_config.TextColumn("Value")
        },
        hide_index=True,
        use_container_width=True
    )


    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Full Price Simulation Data"):
        st.caption("All simulated prices with predicted demand, revenue, and profit.")
        st.dataframe(
            opt_df.style.highlight_max(subset=['Profit'], color='rgba(16, 185, 129, 0.2)'),
            use_container_width=True
        )