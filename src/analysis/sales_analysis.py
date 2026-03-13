"""
Sales analysis module for the sales analytics project.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from src.utils.logger import logger
from src.utils.config import config

class SalesAnalyzer:
    """Handle sales analysis operations."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize SalesAnalyzer with data.
        
        Args:
            df: DataFrame containing sales data
        """
        self.df = df
        self.date_col = config.get('analysis.date_column', 'Order Date')
        self.sales_col = config.get('analysis.sales_column', 'Sales')
        self.profit_col = config.get('analysis.profit_column', 'Profit')
        
        logger.info("SalesAnalyzer initialized")
    
    def calculate_kpis(self) -> Dict[str, float]:
        """
        Calculate key performance indicators.
        
        Returns:
            Dictionary of KPIs
        """
        logger.info("Calculating KPIs")
        
        kpis = {
            'total_revenue': self.df[self.sales_col].sum(),
            'total_profit': self.df[self.profit_col].sum(),
            'total_orders': self.df['Order ID'].nunique(),
            'total_customers': self.df['Customer ID'].nunique(),
            'total_products': self.df['Product ID'].nunique(),
            'avg_order_value': self.df[self.sales_col].mean(),
            'avg_profit_margin': (self.df[self.profit_col].sum() / self.df[self.sales_col].sum() * 100),
            'total_quantity': self.df['Quantity'].sum(),
            'avg_discount': self.df['Discount'].mean() * 100
        }
        
        # Log KPIs
        for key, value in kpis.items():
            logger.info(f"{key}: {value:,.2f}")
        
        return kpis
    
    def analyze_sales_trends(self, freq: str = 'M') -> pd.DataFrame:
        """
        Analyze sales trends over time.
        
        Args:
            freq: Frequency for resampling ('D', 'W', 'M', 'Q', 'Y')
            
        Returns:
            DataFrame with sales trends
        """
        logger.info(f"Analyzing sales trends with frequency: {freq}")
        
        # Ensure date column is datetime
        self.df[self.date_col] = pd.to_datetime(self.df[self.date_col])
        
        # Set date as index and resample
        trends = self.df.set_index(self.date_col).resample(freq).agg({
            self.sales_col: 'sum',
            self.profit_col: 'sum',
            'Quantity': 'sum',
            'Order ID': 'nunique',
            'Discount': 'mean'
        }).round(2)
        
        trends.columns = ['Sales', 'Profit', 'Quantity', 'Orders', 'Avg_Discount']
        trends['Profit_Margin'] = (trends['Profit'] / trends['Sales'] * 100).round(2)
        
        logger.info(f"Generated trends with {len(trends)} periods")
        return trends
    
    def analyze_regional_sales(self) -> pd.DataFrame:
        """
        Analyze sales by region.
        
        Returns:
            DataFrame with regional sales analysis
        """
        logger.info("Analyzing regional sales")
        
        regional = self.df.groupby('Region').agg({
            self.sales_col: ['sum', 'mean', 'count'],
            self.profit_col: ['sum', 'mean'],
            'Quantity': 'sum',
            'Customer ID': 'nunique',
            'Order ID': 'nunique'
        }).round(2)
        
        regional.columns = ['Total_Sales', 'Avg_Sales', 'Num_Transactions',
                           'Total_Profit', 'Avg_Profit', 'Total_Quantity',
                           'Unique_Customers', 'Unique_Orders']
        regional = regional.reset_index()
        
        regional['Profit_Margin'] = (regional['Total_Profit'] / regional['Total_Sales'] * 100).round(2)
        regional['Sales_per_Customer'] = (regional['Total_Sales'] / regional['Unique_Customers']).round(2)
        
        # Sort by total sales
        regional = regional.sort_values('Total_Sales', ascending=False)
        
        logger.info(f"Analyzed {len(regional)} regions")
        return regional
    
    def analyze_category_performance(self) -> Dict[str, pd.DataFrame]:
        """
        Analyze performance by category and sub-category.
        
        Returns:
            Dictionary with category and sub-category analysis
        """
        logger.info("Analyzing category performance")
        
        results = {}
        
        # Category level analysis
        category = self.df.groupby('Category').agg({
            self.sales_col: ['sum', 'mean', 'count'],
            self.profit_col: ['sum', 'mean'],
            'Quantity': 'sum'
        }).round(2)
        
        category.columns = ['Total_Sales', 'Avg_Sales', 'Num_Transactions',
                           'Total_Profit', 'Avg_Profit', 'Total_Quantity']
        category = category.reset_index()
        category['Profit_Margin'] = (category['Total_Profit'] / category['Total_Sales'] * 100).round(2)
        category = category.sort_values('Total_Sales', ascending=False)
        
        results['category'] = category
        
        # Sub-category level analysis
        subcategory = self.df.groupby(['Category', 'Sub-Category']).agg({
            self.sales_col: ['sum', 'mean', 'count'],
            self.profit_col: ['sum', 'mean'],
            'Quantity': 'sum'
        }).round(2)
        
        subcategory.columns = ['Total_Sales', 'Avg_Sales', 'Num_Transactions',
                              'Total_Profit', 'Avg_Profit', 'Total_Quantity']
        subcategory = subcategory.reset_index()
        subcategory['Profit_Margin'] = (subcategory['Total_Profit'] / subcategory['Total_Sales'] * 100).round(2)
        subcategory = subcategory.sort_values('Total_Sales', ascending=False)
        
        results['subcategory'] = subcategory
        
        logger.info(f"Analyzed {len(category)} categories and {len(subcategory)} sub-categories")
        return results
    
    def get_top_products(self, n: int = 10, metric: str = 'Sales') -> pd.DataFrame:
        """
        Get top performing products.
        
        Args:
            n: Number of top products to return
            metric: Metric to rank by ('Sales', 'Profit', 'Quantity')
            
        Returns:
            DataFrame with top products
        """
        logger.info(f"Getting top {n} products by {metric}")
        
        top_products = self.df.groupby(['Product ID', 'Product Name', 'Category', 'Sub-Category']).agg({
            self.sales_col: 'sum',
            self.profit_col: 'sum',
            'Quantity': 'sum',
            'Order ID': 'nunique'
        }).round(2)
        
        top_products.columns = ['Total_Sales', 'Total_Profit', 'Total_Quantity', 'Num_Orders']
        top_products = top_products.reset_index()
        
        top_products['Profit_Margin'] = (top_products['Total_Profit'] / top_products['Total_Sales'] * 100).round(2)
        top_products['Avg_Order_Value'] = (top_products['Total_Sales'] / top_products['Num_Orders']).round(2)
        
        # Sort by specified metric
        metric_map = {
            'Sales': 'Total_Sales',
            'Profit': 'Total_Profit',
            'Quantity': 'Total_Quantity'
        }
        
        sort_col = metric_map.get(metric, 'Total_Sales')
        top_products = top_products.sort_values(sort_col, ascending=False).head(n)
        
        logger.info(f"Retrieved top {len(top_products)} products")
        return top_products
    
    def analyze_profit_sales_relationship(self) -> Dict[str, any]:
        """
        Analyze relationship between profit and sales.
        
        Returns:
            Dictionary with correlation and statistics
        """
        logger.info("Analyzing profit-sales relationship")
        
        # Calculate correlation
        correlation = self.df[[self.sales_col, self.profit_col]].corr().iloc[0, 1]
        
        # Profitability segments
        self.df['Profitability_Segment'] = pd.cut(
            self.df[self.profit_col],
            bins=[-float('inf'), 0, 50, 200, float('inf')],
            labels=['Loss', 'Low Profit', 'Medium Profit', 'High Profit']
        )
        
        segment_counts = self.df['Profitability_Segment'].value_counts()
        
        # Statistics by profitability segment
        segment_stats = self.df.groupby('Profitability_Segment').agg({
            self.sales_col: ['mean', 'count'],
            self.profit_col: 'mean',
            'Discount': 'mean'
        }).round(2)
        
        results = {
            'correlation': correlation,
            'segment_counts': segment_counts.to_dict(),
            'segment_stats': segment_stats
        }
        
        logger.info(f"Profit-Sales correlation: {correlation:.3f}")
        return results