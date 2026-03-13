"""
Chart generation module for the sales analytics project.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any
from src.utils.logger import logger

class ChartGenerator:
    """Generate charts for sales analytics."""
    
    def __init__(self, theme: str = 'plotly_white'):
        """
        Initialize ChartGenerator.
        
        Args:
            theme: Plotly theme to use
        """
        self.theme = theme
        self.color_palette = px.colors.qualitative.Set2
        logger.info(f"ChartGenerator initialized with theme: {theme}")
    
    def create_sales_trend_chart(self, df: pd.DataFrame, 
                                 date_col: str = 'Order Date',
                                 sales_col: str = 'Sales',
                                 title: str = 'Sales Trends Over Time') -> go.Figure:
        """
        Create sales trend chart.
        
        Args:
            df: DataFrame with sales data
            date_col: Date column name
            sales_col: Sales column name
            title: Chart title
            
        Returns:
            Plotly figure
        """
        logger.info("Creating sales trend chart")
        
        # Ensure date is datetime
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # Aggregate by date
        daily_sales = df.groupby(date_col)[sales_col].sum().reset_index()
        
        # Create figure
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Daily Sales', '7-Day Moving Average'),
            vertical_spacing=0.15
        )
        
        # Add daily sales
        fig.add_trace(
            go.Scatter(
                x=daily_sales[date_col],
                y=daily_sales[sales_col],
                mode='lines',
                name='Daily Sales',
                line=dict(color=self.color_palette[0], width=1),
                opacity=0.7
            ),
            row=1, col=1
        )
        
        # Add moving average
        daily_sales['MA7'] = daily_sales[sales_col].rolling(window=7).mean()
        fig.add_trace(
            go.Scatter(
                x=daily_sales[date_col],
                y=daily_sales['MA7'],
                mode='lines',
                name='7-Day MA',
                line=dict(color='red', width=2)
            ),
            row=1, col=1
        )
        
        # Add monthly aggregates
        monthly_sales = df.set_index(date_col).resample('M')[sales_col].sum().reset_index()
        fig.add_trace(
            go.Bar(
                x=monthly_sales[date_col],
                y=monthly_sales[sales_col],
                name='Monthly Sales',
                marker_color=self.color_palette[1]
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            height=800,
            showlegend=True,
            template=self.theme,
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_xaxes(title_text="Month", row=2, col=1)
        fig.update_yaxes(title_text="Sales ($)", row=1, col=1)
        fig.update_yaxes(title_text="Sales ($)", row=2, col=1)
        
        return fig
    
    def create_regional_sales_chart(self, df: pd.DataFrame,
                                   region_col: str = 'Region',
                                   sales_col: str = 'Sales',
                                   title: str = 'Sales by Region') -> go.Figure:
        """
        Create regional sales chart.
        
        Args:
            df: DataFrame with sales data
            region_col: Region column name
            sales_col: Sales column name
            title: Chart title
            
        Returns:
            Plotly figure
        """
        logger.info("Creating regional sales chart")
        
        # Aggregate by region
        regional = df.groupby(region_col).agg({
            sales_col: ['sum', 'mean', 'count']
        }).round(2)
        
        regional.columns = ['Total_Sales', 'Avg_Sales', 'Num_Orders']
        regional = regional.reset_index().sort_values('Total_Sales', ascending=True)
        
        # Create figure with subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Total Sales by Region', 'Average Order Value by Region'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}]]
        )
        
        # Total sales bar chart
        fig.add_trace(
            go.Bar(
                y=regional[region_col],
                x=regional['Total_Sales'],
                orientation='h',
                name='Total Sales',
                marker_color=self.color_palette[0],
                text=regional['Total_Sales'].apply(lambda x: f'${x:,.0f}'),
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # Average sales bar chart
        fig.add_trace(
            go.Bar(
                y=regional[region_col],
                x=regional['Avg_Sales'],
                orientation='h',
                name='Avg Order Value',
                marker_color=self.color_palette[1],
                text=regional['Avg_Sales'].apply(lambda x: f'${x:,.0f}'),
                textposition='outside'
            ),
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            height=500,
            showlegend=False,
            template=self.theme,
            hovermode='y unified'
        )
        
        fig.update_xaxes(title_text="Total Sales ($)", row=1, col=1)
        fig.update_xaxes(title_text="Average Order Value ($)", row=1, col=2)
        
        return fig
    
    def create_category_sales_chart(self, df: pd.DataFrame,
                                   category_col: str = 'Category',
                                   subcategory_col: str = 'Sub-Category',
                                   sales_col: str = 'Sales',
                                   title: str = 'Sales by Category') -> go.Figure:
        """
        Create category sales chart.
        
        Args:
            df: DataFrame with sales data
            category_col: Category column name
            subcategory_col: Sub-category column name
            sales_col: Sales column name
            title: Chart title
            
        Returns:
            Plotly figure
        """
        logger.info("Creating category sales chart")
        
        # Aggregate by category
        category_sales = df.groupby(category_col)[sales_col].sum().sort_values(ascending=False)
        
        # Aggregate by subcategory
        subcategory_sales = df.groupby([category_col, subcategory_col])[sales_col].sum().reset_index()
        subcategory_sales = subcategory_sales.sort_values(sales_col, ascending=False)
        
        # Create figure with subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Sales by Category', 'Top 10 Sub-Categories'),
            specs=[[{'type': 'pie'}, {'type': 'bar'}]]
        )
        
        # Category pie chart
        fig.add_trace(
            go.Pie(
                labels=category_sales.index,
                values=category_sales.values,
                name='Categories',
                marker_colors=self.color_palette,
                textinfo='label+percent',
                insidetextorientation='radial'
            ),
            row=1, col=1
        )
        
        # Top 10 subcategories
        top_sub = subcategory_sales.head(10)
        fig.add_trace(
            go.Bar(
                x=top_sub[subcategory_col],
                y=top_sub[sales_col],
                name='Sub-Categories',
                marker_color=self.color_palette,
                text=top_sub[sales_col].apply(lambda x: f'${x:,.0f}'),
                textposition='outside'
            ),
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            height=500,
            showlegend=False,
            template=self.theme
        )
        
        fig.update_xaxes(title_text="Sub-Category", row=1, col=2, tickangle=45)
        fig.update_yaxes(title_text="Sales ($)", row=1, col=2)
        
        return fig
    
    def create_top_products_chart(self, df: pd.DataFrame,
                                 n: int = 10,
                                 metric: str = 'Sales',
                                 title: str = 'Top 10 Products') -> go.Figure:
        """
        Create top products chart.
        
        Args:
            df: DataFrame with sales data
            n: Number of top products
            metric: Metric to rank by
            title: Chart title
            
        Returns:
            Plotly figure
        """
        logger.info(f"Creating top {n} products chart by {metric}")
        
        # Aggregate by product
        product_metrics = df.groupby(['Product Name', 'Category']).agg({
            'Sales': 'sum',
            'Profit': 'sum',
            'Quantity': 'sum'
        }).round(2).reset_index()
        
        # Sort and get top n
        top_products = product_metrics.nlargest(n, metric)
        
        # Create figure
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(f'Top {n} by {metric}', f'{metric} by Category'),
            specs=[[{'type': 'bar'}, {'type': 'pie'}]]
        )
        
        # Top products bar chart
        colors = [self.color_palette[i % len(self.color_palette)] 
                 for i in range(len(top_products))]
        
        fig.add_trace(
            go.Bar(
                y=top_products['Product Name'],
                x=top_products[metric],
                orientation='h',
                name='Products',
                marker_color=colors,
                text=top_products[metric].apply(lambda x: f'${x:,.0f}'),
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # Category distribution pie chart
        category_dist = top_products.groupby('Category')[metric].sum()
        fig.add_trace(
            go.Pie(
                labels=category_dist.index,
                values=category_dist.values,
                name='Category Distribution',
                marker_colors=self.color_palette
            ),
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            height=600,
            showlegend=False,
            template=self.theme
        )
        
        fig.update_xaxes(title_text=metric, row=1, col=1)
        fig.update_yaxes(title_text="Product", row=1, col=1)
        
        return fig
    
    def create_profit_sales_scatter(self, df: pd.DataFrame,
                                   sales_col: str = 'Sales',
                                   profit_col: str = 'Profit',
                                   color_col: str = 'Category',
                                   title: str = 'Profit vs Sales Analysis') -> go.Figure:
        """
        Create profit vs sales scatter plot.
        
        Args:
            df: DataFrame with sales data
            sales_col: Sales column name
            profit_col: Profit column name
            color_col: Column for color coding
            title: Chart title
            
        Returns:
            Plotly figure
        """
        logger.info("Creating profit vs sales scatter plot")
        
        # Add quadrant lines
        avg_sales = df[sales_col].mean()
        avg_profit = df[profit_col].mean()
        
        # Create scatter plot
        fig = px.scatter(
            df,
            x=sales_col,
            y=profit_col,
            color=color_col,
            size='Quantity',
            hover_data=['Product Name', 'Category', 'Sub-Category'],
            title=title,
            labels={sales_col: 'Sales ($)', profit_col: 'Profit ($)', 'Quantity': 'Quantity'},
            color_discrete_sequence=self.color_palette
        )
        
        # Add quadrant lines
        fig.add_hline(y=avg_profit, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=avg_sales, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Add quadrant annotations
        fig.add_annotation(
            x=df[sales_col].max() * 0.8,
            y=df[profit_col].max() * 0.8,
            text="High Sales, High Profit",
            showarrow=False,
            font=dict(color="green")
        )
        
        fig.add_annotation(
            x=df[sales_col].min() * 1.2,
            y=df[profit_col].max() * 0.8,
            text="Low Sales, High Profit",
            showarrow=False,
            font=dict(color="blue")
        )
        
        fig.add_annotation(
            x=df[sales_col].max() * 0.8,
            y=df[profit_col].min() * 1.2,
            text="High Sales, Low Profit",
            showarrow=False,
            font=dict(color="orange")
        )
        
        fig.add_annotation(
            x=df[sales_col].min() * 1.2,
            y=df[profit_col].min() * 1.2,
            text="Low Sales, Low Profit",
            showarrow=False,
            font=dict(color="red")
        )
        
        # Update layout
        fig.update_layout(
            height=600,
            template=self.theme,
            hovermode='closest'
        )
        
        return fig
    
    def create_customer_segmentation_chart(self, df: pd.DataFrame,
                                         segment_col: str = 'Segment_Name',
                                         value_col: str = 'Total_Sales',
                                         title: str = 'Customer Segmentation Analysis') -> go.Figure:
        """
        Create customer segmentation chart.
        
        Args:
            df: DataFrame with customer data
            segment_col: Segment column name
            value_col: Value column name
            title: Chart title
            
        Returns:
            Plotly figure
        """
        logger.info("Creating customer segmentation chart")
        
        # Aggregate by segment
        segment_analysis = df.groupby(segment_col).agg({
            value_col: ['sum', 'mean', 'count'],
            'Total_Profit': ['sum', 'mean'],
            'Frequency': 'mean'
        }).round(2)
        
        segment_analysis.columns = ['Total_Value', 'Avg_Value', 'Customer_Count',
                                   'Total_Profit', 'Avg_Profit', 'Avg_Frequency']
        segment_analysis = segment_analysis.reset_index()
        
        # Create figure with multiple subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Customer Distribution', 'Value by Segment',
                          'Profit by Segment', 'Purchase Frequency'),
            specs=[[{'type': 'pie'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'bar'}]]
        )
        
        # Customer distribution pie chart
        fig.add_trace(
            go.Pie(
                labels=segment_analysis[segment_col],
                values=segment_analysis['Customer_Count'],
                name='Customer Distribution',
                marker_colors=self.color_palette,
                textinfo='label+percent'
            ),
            row=1, col=1
        )
        
        # Value by segment
        fig.add_trace(
            go.Bar(
                x=segment_analysis[segment_col],
                y=segment_analysis['Total_Value'],
                name='Total Value',
                marker_color=self.color_palette[0],
                text=segment_analysis['Total_Value'].apply(lambda x: f'${x:,.0f}'),
                textposition='outside'
            ),
            row=1, col=2
        )
        
        # Profit by segment
        fig.add_trace(
            go.Bar(
                x=segment_analysis[segment_col],
                y=segment_analysis['Total_Profit'],
                name='Total Profit',
                marker_color=self.color_palette[1],
                text=segment_analysis['Total_Profit'].apply(lambda x: f'${x:,.0f}'),
                textposition='outside'
            ),
            row=2, col=1
        )
        
        # Frequency by segment
        fig.add_trace(
            go.Bar(
                x=segment_analysis[segment_col],
                y=segment_analysis['Avg_Frequency'],
                name='Avg Frequency',
                marker_color=self.color_palette[2],
                text=segment_analysis['Avg_Frequency'].round(1),
                textposition='outside'
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            height=800,
            showlegend=False,
            template=self.theme
        )
        
        fig.update_xaxes(title_text="Segment", row=1, col=2, tickangle=45)
        fig.update_xaxes(title_text="Segment", row=2, col=1, tickangle=45)
        fig.update_xaxes(title_text="Segment", row=2, col=2, tickangle=45)
        fig.update_yaxes(title_text="Total Value ($)", row=1, col=2)
        fig.update_yaxes(title_text="Total Profit ($)", row=2, col=1)
        fig.update_yaxes(title_text="Frequency", row=2, col=2)
        
        return fig
    
    def create_dashboard_kpi_cards(self, kpis: Dict[str, float]) -> List[go.Figure]:
        """
        Create KPI cards for dashboard.
        
        Args:
            kpis: Dictionary of KPIs
            
        Returns:
            List of Plotly figures for KPI cards
        """
        logger.info("Creating KPI cards")
        
        cards = []
        kpi_configs = [
            {'key': 'total_revenue', 'title': 'Total Revenue', 'prefix': '$', 'format': ',.0f'},
            {'key': 'total_profit', 'title': 'Total Profit', 'prefix': '$', 'format': ',.0f'},
            {'key': 'avg_profit_margin', 'title': 'Profit Margin', 'suffix': '%', 'format': '.1f'},
            {'key': 'total_orders', 'title': 'Total Orders', 'format': ',.0f'}
        ]
        
        for config in kpi_configs:
            key = config['key']
            if key in kpis:
                value = kpis[key]
                
                # Create gauge or indicator
                if 'margin' in key:
                    # Gauge chart for percentages
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=value,
                        title={'text': config['title']},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "gray"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                else:
                    # Number card for absolute values
                    formatted_value = f"{config.get('prefix', '')}{value:{config.get('format', ',.0f')}}{config.get('suffix', '')}"
                    fig = go.Figure(go.Indicator(
                        mode="number",
                        value=value,
                        number={'prefix': config.get('prefix', ''), 
                               'suffix': config.get('suffix', ''),
                               'font': {'size': 50}},
                        title={'text': config['title'], 'font': {'size': 20}},
                        domain={'x': [0, 1], 'y': [0, 1]}
                    ))
                
                fig.update_layout(
                    height=200,
                    margin=dict(l=20, r=20, t=50, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font={'color': "darkblue", 'family': "Arial"}
                )
                
                cards.append(fig)
        
        return cards