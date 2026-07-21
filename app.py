import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(page_title="Retail Sales Intelligence App", layout="wide")

st.title("Retail Sales Intelligence App")

# --- Sidebar File Uploads ---
st.sidebar.header("Data Configuration")
uploaded_sales = st.sidebar.file_uploader("Upload 'retail_weekly_sales.xlsx'", type=["xlsx"])
uploaded_master = st.sidebar.file_uploader("Upload 'store_master.xlsx'", type=["xlsx"])

# --- Main Processing Logic ---
if uploaded_sales and uploaded_master:
    # Load Data
    df_sales = pd.read_excel(uploaded_sales)
    df_master = pd.read_excel(uploaded_master)

    # Perform Merge on 'StoreID'
    # Ensure column names match; assuming input files have 'StoreID'
    # df = pd.merge(df_sales, df_master, on="storeid", how="left")
    df = pd.merge(
    df_sales,
    df_master,
    on="store_id",
    how="left",
    suffixes=("", "_master")
    )
    st.write(df.dtypes)

    numeric_columns = [
    "footfall",
    "transactions",
    "units_sold",
    "gross_sales",
    "discount_amount",
    "net_sales",
    "sales_target",
    "inventory_on_hand",
    "stockouts",
    "returns_amount",
    "customer_rating",
    "marketing_spend"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Target_Achievement"] = (
        df["net_sales"] / df["sales_target"]
    ) * 100

    df["ATV"] = (
        df["net_sales"] / df["transactions"]
    )

    df["Return_Rate"] = (
        df["returns_amount"] / df["net_sales"]
    ) * 100

    df["Discount_Rate"] = (
        df["discount_amount"] / df["gross_sales"]
    ) * 100
    # --- Sidebar Filters ---
    st.sidebar.header("Dashboard Filters")
    
    # Generate filter lists based on available data
    weeks = st.sidebar.multiselect(
    "Select Week",
    options=df["week_start_date"].unique(),
    default=df["week_start_date"].unique()
    )

    regions = st.sidebar.multiselect(
    "Select Region",
    options=df["region"].unique(),
    default=df["region"].unique()
    )

    stores = st.sidebar.multiselect(
        "Select Store",
        options=df["store_name"].unique(),
        default=df["store_name"].unique()
    )

    cities = st.sidebar.multiselect(
        "Select City",
        options=df["city"].unique(),
        default=df["city"].unique()
    )

    formats = st.sidebar.multiselect(
        "Select Store Format",
        options=df["store_format"].unique(),
        default=df["store_format"].unique()
    )

    categories = st.sidebar.multiselect(
    "Select Product product_category",
    options=df["product_category"].unique(),
    default=df["product_category"].unique()
    )

    # Apply Filters
    mask = (
        (df["week_start_date"].isin(weeks)) &
        (df['region'].isin(regions)) &
        (df['store_name'].isin(stores)) &
        (df['city'].isin(cities)) &
        (df['store_format'].isin(formats)) &
        (df["product_category"].isin(categories))
    )
    df_filtered = df[mask].copy()

    # --- KPI Cards ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Net Sales", f"₹{df_filtered['net_sales'].sum():,.2f}")
    with col2:
        st.metric("Target Achievement %", f"{df_filtered['Target_Achievement'].mean():.2f}%")
    with col3:
        st.metric("Avg Transaction Value (ATV)", f"₹{df_filtered['ATV'].mean():.2f}")
    with col4:
        st.metric("Avg Return Rate", f"{df_filtered['Return_Rate'].mean():.2f}%")

    # --- Visualizations ---
    st.subheader("Performance Visualizations")
    row1_c1, row1_c2 = st.columns(2)
    row2_c1, row2_c2 = st.columns(2)

    # 1. Weekly Trends (Line Chart)
    with row1_c1:
        fig_trend = px.line(df_filtered.groupby('week_start_date')['net_sales'].sum().reset_index(), 
                            x='week_start_date', y='net_sales', title="Weekly Net Sales Trend")
        st.plotly_chart(fig_trend, use_container_width=True)

    # 2. Sales by Region (Bar Chart)
    with row1_c2:
        fig_region = px.bar(df_filtered.groupby('region')['net_sales'].sum().reset_index(), 
                            x='region', y='net_sales', title="Net Sales by Region")
        st.plotly_chart(fig_region, use_container_width=True)

    # 3. product_category Performance (Treemap)
    with row2_c1:
        fig_cat = px.treemap(df_filtered, path=['product_category'], values='net_sales', 
                             title="product_category Performance (Net Sales)")
        st.plotly_chart(fig_cat, use_container_width=True)

    # 4. Top Stores Leaderboard
    with row2_c2:
        top_stores = df_filtered.groupby('store_name')['net_sales'].sum().nlargest(10).reset_index()
        fig_leader = px.bar(top_stores, x='net_sales', y='store_name', orientation='h', 
                            title="Top 10 Performing Stores")
        fig_leader.update_yaxes(categoryorder='total ascending')
        st.plotly_chart(fig_leader, use_container_width=True)

    # --- Business Insights Section ---
    st.subheader("Business Insights")
    
    # Logic: Regions missing targets (Achievement < 100%)
    region_perf = df_filtered.groupby('region')['Target_Achievement'].mean().reset_index()
    missed_targets = region_perf[region_perf['Target_Achievement'] < 100]
    
    # Logic: High Return Categories (Return Rate > 5%)
    cat_returns = df_filtered.groupby('product_category')['Return_Rate'].mean().reset_index()
    high_returns = cat_returns[cat_returns['Return_Rate'] > 5]

    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.warning("Regions Below Target")
        if not missed_targets.empty:
            st.write(missed_targets)
        else:
            st.success("All regions are achieving targets.")
            
    with col_ins2:
        st.error("Categories with High Return Rate (>5%)")
        if not high_returns.empty:
            st.write(high_returns)
        else:
            st.success("No categories currently exceeding return thresholds.")

    # --- Export Functionality ---
    st.subheader("Export Data")
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name='filtered_retail_data.csv',
        mime='text/csv',
    )

else:
    st.info("Please upload both 'retail_weekly_sales.xlsx' and 'store_master.xlsx' to begin the analysis.")
