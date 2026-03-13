"""
Dashboard components module for the sales analytics project.
"""
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from src.utils.logger import logger
from src.visualization.charts import ChartGenerator

class DashboardComponents:
    """Manage dashboard components and interactions."""
    
    def __init__(self):
        """Initialize DashboardComponents."""
        self.chart_gen = ChartGenerator()
        logger.info("DashboardComponents initialized")
    
    def create_sidebar_filters(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Create sidebar filters for dashboard.
        
        Args:
            df: DataFrame with data
            
        Returns:
            Dictionary with filter values
        """
        logger.info("Creating sidebar filters")
        
        filters = {}
        
        with st.sidebar:
            st.header("Filters")
            
            # Date range filter
            st.subheader("Date Range")
            min_date = pd.to_datetime(df['Order Date']).min()
            max_date = pd.to_datetime(df['Order Date']).max()
            
            date_range = st.date_input(
                "Select Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                filters['start_date'], filters['end_date'] = date_range
            else:
                filters['start_date'] = min_date
                filters['end_date'] = max_date
            
            # Region filter
            st.subheader("Region")
            regions = ['All'] + sorted(df['Region'].unique().tolist())
            filters['region'] = st.selectbox("Select Region", regions)
            
            # Category filter
            st.subheader("Category")
            categories = ['All'] + sorted(df['Category'].unique().tolist())
            filters['category'] = st.selectbox("Select Category", categories)
            
            # Segment filter
            st.subheader("Customer Segment")
            segments = ['All'] + sorted(df['Segment'].unique().tolist())
            filters['segment'] = st.selectbox("Select Customer Segment", segments)
            
            # Additional filters
            with st.expander("Advanced Filters"):
                # Profitability filter
                profit_options = ['All', 'Profitable Only', 'Loss Making Only']
                filters['profitability'] = st.selectbox("Profitability", profit_options)
                
                # Minimum sales filter
                min_sales = float(df['Sales'].min())
                max_sales = float(df['Sales'].max())
                filters['min_sales'] = st.slider(
                    "Minimum Sales ($)",
                    min_value=min_sales,
                    max_value=max_sales,
                    value=min_sales
                )
                
                # Discount range
                min_discount = float(df['Discount'].min() * 100)
                max_discount = float(df['Discount'].max() * 100)
                filters['discount_range'] = st.slider(
                    "Discount Range (%)",
                    min_value=min_discount,
                    max_value=max_discount,
                    value=(min_discount, max_discount)
                )
            
            # Reset filters button
            if st.button("Reset Filters"):
                filters = {
                    'start_date': min_date,
                    'end_date': max_date,
                    'region': 'All',
                    'category': 'All',
                    'segment': 'All',
                    'profitability': 'All',
                    'min_sales': min_sales,
                    'discount_range': (min_discount, max_discount)
                }
                st.rerun()
        
        return filters
    
    def apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply filters to dataframe.
        
        Args:
            df: Original DataFrame
            filters: Dictionary of filters
            
        Returns:
            Filtered DataFrame
        """
        logger.info("Applying filters to data")
        
        filtered_df = df.copy()
        
        # Apply date filter
        if 'start_date' in filters and 'end_date' in filters:
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df['Order Date']).dt.date >= filters['start_date']) &
                (pd.to_datetime(filtered_df['Order Date']).dt.date <= filters['end_date'])
            ]
        
        # Apply region filter
        if filters.get('region') and filters['region'] != 'All':
            filtered_df = filtered_df[filtered_df['Region'] == filters['region']]
        
        # Apply category filter
        if filters.get('category') and filters['category'] != 'All':
            filtered_df = filtered_df[filtered_df['Category'] == filters['category']]
        
        # Apply segment filter
        if filters.get('segment') and filters['segment'] != 'All':
            filtered_df = filtered_df[filtered_df['Segment'] == filters['segment']]
        
        # Apply profitability filter
        if filters.get('profitability') == 'Profitable Only':
            filtered_df = filtered_df[filtered_df['Profit'] > 0]
        elif filters.get('profitability') == 'Loss Making Only':
            filtered_df = filtered_df[filtered_df['Profit'] < 0]
        
        # Apply minimum sales filter
        if 'min_sales' in filters:
            filtered_df = filtered_df[filtered_df['Sales'] >= filters['min_sales']]
        
        # Apply discount range filter
        if 'discount_range' in filters:
            min_discount, max_discount = filters['discount_range']
            filtered_df = filtered_df[
                (filtered_df['Discount'] * 100 >= min_discount) &
                (filtered_df['Discount'] * 100 <= max_discount)
            ]
        
        logger.info(f"Filters applied. Rows: {len(df)} -> {len(filtered_df)}")
        return filtered_df
    
    def create_kpi_row(self, kpis: Dict[str, float]):
        """
        Create KPI row in Streamlit.
        
        Args:
            kpis: Dictionary of KPIs
        """
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Revenue",
                value=f"${kpis.get('total_revenue', 0):,.0f}",
                delta=f"{kpis.get('revenue_growth', 0):.1f}%"
            )
        
        with col2:
            st.metric(
                label="Total Profit",
                value=f"${kpis.get('total_profit', 0):,.0f}",
                delta=f"{kpis.get('profit_growth', 0):.1f}%"
            )
        
        with col3:
            st.metric(
                label="Profit Margin",
                value=f"{kpis.get('avg_profit_margin', 0):.1f}%",
                delta=f"{kpis.get('margin_change', 0):.1f}pp"
            )
        
        with col4:
            st.metric(
                label="Total Orders",
                value=f"{kpis.get('total_orders', 0):,.0f}",
                delta=f"{kpis.get('orders_growth', 0):.1f}%"
            )
    
    def create_dashboard_tabs(self):
        """Create dashboard tabs."""
        tabs = st.tabs([
            "Overview",
            "Sales Analysis",
            "Profit Analysis",
            "Customer Analysis",
            "Product Analysis",
            "Data Explorer"
        ])
        
        return tabs
    
    def create_data_explorer(self, df: pd.DataFrame):
        """
        Create data explorer tab.
        
        Args:
            df: DataFrame to explore
        """
        st.subheader("Data Explorer")
        
        # Data summary
        with st.expander("Data Summary", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Dataset Shape**")
                st.write(f"Rows: {df.shape[0]:,}")
                st.write(f"Columns: {df.shape[1]:,}")
            
            with col2:
                st.write("**Date Range**")
                st.write(f"From: {df['Order Date'].min()}")
                st.write(f"To: {df['Order Date'].max()}")
            
            with col3:
                st.write("**Unique Values**")
                st.write(f"Customers: {df['Customer ID'].nunique():,}")
                st.write(f"Products: {df['Product ID'].nunique():,}")
        
        # Column selection
        all_columns = df.columns.tolist()
        default_columns = ['Order Date', 'Customer Name', 'Product Name', 
                          'Category', 'Sales', 'Profit', 'Region']
        
        selected_columns = st.multiselect(
            "Select columns to display",
            options=all_columns,
            default=[col for col in default_columns if col in all_columns]
        )
        
        if selected_columns:
            # Row limit
            row_limit = st.slider("Number of rows to display", 10, 1000, 100)
            
            # Display data
            st.dataframe(
                df[selected_columns].head(row_limit),
                use_container_width=True,
                height=400
            )
            
            # Download button
            csv = df[selected_columns].to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="sales_data_export.csv",
                mime="text/csv"
            )
    
    def create_export_options(self, figs: Dict[str, go.Figure]):
        """
        Create export options for charts.
        
        Args:
            figs: Dictionary of figures to export
        """
        with st.expander("Export Options", expanded=False):
            st.write("Download charts as HTML files")
            
            cols = st.columns(3)
            for i, (name, fig) in enumerate(figs.items()):
                with cols[i % 3]:
                    if fig:
                        # Create HTML download
                        html_str = fig.to_html(include_plotlyjs='cdn')
                        st.download_button(
                            label=f"Download {name}",
                            data=html_str,
                            file_name=f"{name.lower().replace(' ', '_')}.html",
                            mime="text/html",
                            key=f"download_{name}"
                        )
    
    def show_insights_panel(self, insights: Dict[str, Any]):
        """
        Show insights panel.
        
        Args:
            insights: Dictionary of insights
        """
        with st.sidebar.expander("📊 Key Insights", expanded=False):
            for category, insight_list in insights.items():
                st.write(f"**{category}**")
                for insight in insight_list:
                    st.write(f"• {insight}")
                st.write("---")