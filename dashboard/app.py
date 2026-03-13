"""
Main dashboard application for sales analytics.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.logger import logger
from src.utils.config import config
from src.data.load_data import DataLoader
from src.analysis.sales_analysis import SalesAnalyzer
from src.analysis.customer_analysis import CustomerAnalyzer
from src.analysis.profit_analysis import ProfitAnalyzer
from src.visualization.charts import ChartGenerator
from src.visualization.dashboard_components import DashboardComponents

# Page configuration
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="₹₹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    """Initialize dashboard components."""
    return {
        'loader': DataLoader(),
        'chart_gen': ChartGenerator(),
        'components': DashboardComponents()
    }

components = init_components()

# Load data
@st.cache_data(ttl=3600)
def load_data():
    """Load and cache data."""
    try:
        df = components['loader'].load_processed_data()
        logger.info(f"Loaded {len(df)} rows for dashboard")
        return df
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        st.error("Failed to load data. Please check the data source.")
        return None

# Main dashboard
def main():
    """Main dashboard function."""
    
    # Title
    st.title("Sales Analytics Dashboard")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading data..."):
        df = load_data()
    
    if df is None:
        st.stop()
    
    # Create sidebar filters
    filters = components['components'].create_sidebar_filters(df)
    
    # Apply filters
    filtered_df = components['components'].apply_filters(df, filters)
    
    if len(filtered_df) == 0:
        st.warning("No data matches the selected filters. Please adjust your filters.")
        st.stop()
    
    # Initialize analyzers
    sales_analyzer = SalesAnalyzer(filtered_df)
    customer_analyzer = CustomerAnalyzer(filtered_df)
    profit_analyzer = ProfitAnalyzer(filtered_df)
    
    # Calculate KPIs
    kpis = sales_analyzer.calculate_kpis()
    
    # Display KPI row
    components['components'].create_kpi_row(kpis)
    
    # Create tabs
    tabs = components['components'].create_dashboard_tabs()
    
    # Tab 1: Overview
    with tabs[0]:
        st.header("Dashboard Overview")
        
        # Sales trend chart
        st.subheader("Sales Trends")
        sales_trends = sales_analyzer.analyze_sales_trends(freq='M')
        fig_trend = components['chart_gen'].create_sales_trend_chart(
            filtered_df,
            title="Monthly Sales Trends"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Regional and category analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Sales by Region")
            fig_region = components['chart_gen'].create_regional_sales_chart(filtered_df)
            st.plotly_chart(fig_region, use_container_width=True)
        
        with col2:
            st.subheader("Sales by Category")
            fig_category = components['chart_gen'].create_category_sales_chart(filtered_df)
            st.plotly_chart(fig_category, use_container_width=True)
        
        # Key insights
        with st.expander("Key Insights", expanded=False):
            st.write(f"• Total Revenue: **${kpis['total_revenue']:,.0f}**")
            st.write(f"• Total Profit: **${kpis['total_profit']:,.0f}**")
            st.write(f"• Profit Margin: **{kpis['avg_profit_margin']:.1f}%**")
            st.write(f"• Total Orders: **{kpis['total_orders']:,}**")
            st.write(f"• Average Order Value: **${kpis['avg_order_value']:.2f}**")
    
    # Tab 2: Sales Analysis
    with tabs[1]:
        st.header("Sales Analysis")
        
        # Sales trends with different frequencies
        freq = st.selectbox("Select Time Frequency", ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly'])
        freq_map = {'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M', 'Quarterly': 'Q', 'Yearly': 'Y'}
        
        trends = sales_analyzer.analyze_sales_trends(freq=freq_map[freq])
        st.dataframe(trends, use_container_width=True)
        
        # Top products
        col1, col2 = st.columns(2)
        
        with col1:
            metric = st.selectbox("Rank by", ['Sales', 'Profit', 'Quantity'])
            n = st.slider("Number of products", 5, 20, 10)
            top_products = sales_analyzer.get_top_products(n=n, metric=metric)
            
            fig_top = components['chart_gen'].create_top_products_chart(
                filtered_df, n=n, metric=metric
            )
            st.plotly_chart(fig_top, use_container_width=True)
        
        with col2:
            st.subheader("Product Performance")
            st.dataframe(top_products, use_container_width=True)
    
    # Tab 3: Profit Analysis
    with tabs[2]:
        st.header("Profit Analysis")
        
        # Profit drivers
        profit_drivers = profit_analyzer.analyze_profitability_drivers()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Profit by Category")
            st.dataframe(profit_drivers['by_category'], use_container_width=True)
        
        with col2:
            st.subheader("Profit by Region")
            st.dataframe(profit_drivers['by_region'], use_container_width=True)
        
        # Discount impact
        st.subheader("Discount Impact Analysis")
        discount_impact = profit_analyzer.analyze_discount_impact()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Optimal Discount",
                discount_impact['optimal_discount']['discount_bracket'],
                f"{discount_impact['optimal_discount']['profit_margin']:.1f}% margin"
            )
        
        with col2:
            st.metric(
                "Discount-Profit Correlation",
                f"{discount_impact['discount_profit_correlation']:.3f}"
            )
        
        # Loss-making products
        st.subheader("Loss-Making Products")
        loss_products = profit_analyzer.analyze_loss_making_products()
        st.dataframe(loss_products.head(20), use_container_width=True)
        
        # Profit vs Sales scatter
        st.subheader("Profit vs Sales Analysis")
        fig_scatter = components['chart_gen'].create_profit_sales_scatter(filtered_df)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Tab 4: Customer Analysis
    with tabs[3]:
        st.header("Customer Analysis")
        
        # Customer segmentation
        st.subheader("Customer Segmentation")
        
        n_clusters = st.slider("Number of segments", 3, 6, 4)
        customer_segments = customer_analyzer.segment_customers(n_clusters=n_clusters)
        
        fig_segments = components['chart_gen'].create_customer_segmentation_chart(customer_segments)
        st.plotly_chart(fig_segments, use_container_width=True)
        
        # Customer lifetime value
        st.subheader("Customer Lifetime Value")
        clv_data = customer_analyzer.analyze_customer_lifetime_value()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average CLV", f"${clv_data['CLV'].mean():,.0f}")
        
        with col2:
            st.metric("Max CLV", f"${clv_data['CLV'].max():,.0f}")
        
        with col3:
            st.metric("Min CLV", f"${clv_data['CLV'].min():,.0f}")
        
        # High-value customers
        st.subheader("Top Customers")
        high_value = customer_analyzer.identify_high_value_customers(top_n=20)
        st.dataframe(high_value, use_container_width=True)
    
    # Tab 5: Product Analysis
    with tabs[4]:
        st.header("Product Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Category performance
            category_perf = sales_analyzer.analyze_category_performance()
            st.subheader("Category Performance")
            st.dataframe(category_perf['category'], use_container_width=True)
        
        with col2:
            st.subheader("Sub-Category Performance")
            st.dataframe(category_perf['subcategory'].head(20), use_container_width=True)
        
        # Product heatmap
        st.subheader("Product Performance Matrix")
        
        # Create pivot table for heatmap
        product_pivot = pd.pivot_table(
            filtered_df,
            values='Sales',
            index='Category',
            columns='Sub-Category',
            aggfunc='sum',
            fill_value=0
        )
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=product_pivot.values,
            x=product_pivot.columns,
            y=product_pivot.index,
            colorscale='Viridis',
            text=product_pivot.values.round(0),
            texttemplate='$%{text:,.0f}',
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig_heatmap.update_layout(
            title="Sales Heatmap by Category and Sub-Category",
            height=500,
            xaxis_title="Sub-Category",
            yaxis_title="Category"
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Tab 6: Data Explorer
    with tabs[5]:
        st.header("Data Explorer")
        components['components'].create_data_explorer(filtered_df)
    
    # Export options
    figs = {
        'Sales Trends': fig_trend,
        'Regional Sales': fig_region,
        'Category Sales': fig_category,
        'Profit vs Sales': fig_scatter,
        'Customer Segments': fig_segments,
        'Product Heatmap': fig_heatmap
    }
    components['components'].create_export_options(figs)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Sales Analytics Dashboard | Data last updated: {}</p>
        </div>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()