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
st.sidebar.caption("Configure asset operational bounds and market inputs.")

product_map = {
    'LAPTOP001': 'Laptop Pro (₹75K)',
    'PHONE001':  'SmartPhone X (₹25K)',
    'HEAD001':   'Headphones Z (₹5K)',
    'WATCH001':  'SmartWatch S (₹15K)',
}

selected_pid = st.sidebar.selectbox(
    "Target Product Focus",
    list(product_map.keys()),
    format_func=lambda x: product_map[x]
)

base = BASE_PRICES[selected_pid]
today = date.today()

st.sidebar.markdown("---")
st.sidebar.subheader("Market Signals")

competitor_price = st.sidebar.number_input(
    "Competitor Price Index (₹)", 
    min_value=int(base * 0.5), 
    max_value=int(base * 1.5),
    value=int(base * 0.97), 
    step=100
)

inventory = st.sidebar.slider("On-Hand Channel Inventory", 10, 500, 150)
discount = st.sidebar.slider("Applied Markdown Program (%)", 0, 30, 0) / 100
is_holiday = st.sidebar.checkbox("High-Traffic Festival / Holiday")
is_weekend = today.weekday() >= 5

st.sidebar.markdown("---")
st.sidebar.subheader("Temporal Overrides")
month = st.sidebar.slider("Simulated Target Month", 1, 12, today.month)
quarter = (month - 1) // 3 + 1


st.title("PriceIQ")
st.caption("Automated marginal price discovery optimizing yield velocity and financial margin horizons simultaneously.")
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
            label="Optimal Target Price",
            value=f"₹{best['Price']:,.0f}",
            delta=f"{price_delta_pct:+.1f}% vs base strategy",
            delta_color="normal"
        )
    with m_col2:
        st.metric(
            label="Velocity / Run-Rate",
            value=f"{int(best['Predicted_Demand']):,} units",
            delta=f"{demand_delta_abs:+,} units vs status-quo",
            delta_color="normal"
        )
    with m_col3:
        st.metric(
            label="Projected Gross Revenue",
            value=f"₹{best['Revenue']:,.0f}",
            delta=f"{revenue_uplift:+.1f}% gross margin shift",
            delta_color="normal"
        )
    with m_col4:
        st.metric(
            label="Model Net Contribution",
            value=f"₹{best['Profit']:,.0f}",
            delta="Bound Maintained",
            delta_color="off"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    
    if inventory < 50 or price_gap > (base * 0.05) or revenue_uplift > 5:
        with st.container():
            if inventory < 50:
                st.warning(f"**Critical Depletion Alert:** Channel inventory holding at `{inventory}` units. Price curve engine suggests expanding margin premiums to protect inventory runway.")
            if price_gap > (base * 0.05):
                st.error(f"**Competitor Index Displacement:** Current target price sits **₹{abs(price_gap):,.0f}** above known competitive landscape. Volume elasticity disruption risks are actively present.")
            if revenue_uplift > 5:
                st.success(f"**Revenue Optimization Capture:** Adjusting strategic dispatch limits to algorithmic targets offers a projected **{revenue_uplift:.1f}%** structural lift.")

   
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Yield Optimization Geometry")
        fig = px.line(
            opt_df, x='Price', y='Revenue',
            title='Revenue Response Optimization Surface',
            color_discrete_sequence=['#1E3A8A']
        )
        fig.add_vline(x=best['Price'], line_dash='dash', line_color='#10B981',
                      annotation_text=f"Optimal Target (₹{best['Price']:,.0f})", annotation_position="top left")
        fig.add_vline(x=base * (1 - discount), line_dash='dot', line_color='#EF4444',
                      annotation_text="Current Setup", annotation_position="bottom left")
        fig.update_layout(
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Price Vector (₹)"),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Gross Revenue Potential (₹)")
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col2:
        st.subheader("Elastic Demand Signature")
        fig2 = px.line(
            opt_df, x='Price', y='Predicted_Demand',
            title='Velocity Sensitivity Profile',
            color_discrete_sequence=['#F59E0B']
        )
        fig2.add_vline(x=best['Price'], line_dash='dash', line_color='#10B981', annotation_text="Target Optimization Focus")
        fig2.update_layout(
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Price Vector (₹)"),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Predicted Velocity (Units)")
        )
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

   
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Net Component Yield Analysis")
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=opt_df['Price'], y=opt_df['Revenue'],
                              name='Gross Revenue Base', fill='tozeroy',
                              line=dict(color='#3B82F6', width=2.5)))
    fig3.add_trace(go.Scatter(x=opt_df['Price'], y=opt_df['Profit'],
                              name='Net Contribution Margin', fill='tozeroy',
                              line=dict(color='#10B981', width=2.5)))
    fig3.add_vline(x=best['Price'], line_dash='dash', line_color='#EF4444',
                   annotation_text=f"Max Profit Yield: ₹{best['Price']:,.0f}", annotation_position="top right")
    fig3.update_layout(
        title='Marginal Spread Evaluation Across Price Domain Spectrum',
        xaxis_title='Price Configuration Range (₹)', yaxis_title='Financial Metric Magnitude (₹)',
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    
    st.markdown("---")
    st.subheader(f"Base Run-Rate Tracking Context — {product_map[selected_pid]}")
    
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
            title='Historical Volumetric Movement Trace',
            color_discrete_sequence=['#94A3B8']
        )
        fig4.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False, title="Timeline Month"),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Units Velocity Dispatched")
        )
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

    with col4:
        fig5 = px.line(
            hist_monthly, x='Date', y='Revenue',
            title='Historical Revenue Realization Trajectory',
            color_discrete_sequence=['#0F172A']
        )
        fig5.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False, title="Timeline Month"),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Gross Capital Value Ingested (₹)")
        )
        st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar': False})

    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Competitor Parity Positioning")
    
    comp_matrix = pd.DataFrame({
        'Strategic Evaluation Dimension': [
            'Internal Actualized Price', 
            'External Target Index', 
            'Variance Spread Delta', 
            'Percentage Displacement Gap', 
            'Algorithmic Direct Action'
        ],
        'System Value Output Status': [
            f"₹{base * (1 - discount):,.0f}",
            f"₹{competitor_price:,.0f}",
            f"₹{price_gap:+,.0f}",
            f"{(price_gap / competitor_price * 100):+.1f}%",
            "Parity Threshold Maintained" if abs(price_gap / competitor_price) < 0.05 else
            ("High-Side Variance: Compress Strategy Price" if price_gap > 0 else "🔵 Low-Side Variance: Capture Leftover Spread")
        ]
    })
    
    st.dataframe(
        comp_matrix,
        column_config={
            "Strategic Evaluation Dimension": st.column_config.TextColumn("Strategic Evaluation Dimension"),
            "System Value Output Status": st.column_config.TextColumn("System Value Output Status")
        },
        hide_index=True,
        use_container_width=True
    )

    
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Audit Trail: Simulation Data Range Vectors"):
        st.caption("Raw price elastic search optimization space mapped via predictive engine scores.")
        st.dataframe(
            opt_df.style.highlight_max(subset=['Profit'], color='rgba(16, 185, 129, 0.2)'),
            use_container_width=True
        )