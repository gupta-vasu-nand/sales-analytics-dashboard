"""
Profit analysis module for the sales analytics project.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from src.utils.logger import logger

class ProfitAnalyzer:
    """Handle profit analysis operations."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize ProfitAnalyzer with data.
        
        Args:
            df: DataFrame containing sales data
        """
        self.df = df
        logger.info("ProfitAnalyzer initialized")
    
    def analyze_profitability_drivers(self) -> Dict[str, any]:
        """
        Analyze key drivers of profitability.
        
        Returns:
            Dictionary with profitability driver analysis
        """
        logger.info("Analyzing profitability drivers")
        
        results = {}
        
        # Profit by category
        category_profit = self.df.groupby('Category').agg({
            'Profit': ['sum', 'mean'],
            'Sales': 'sum',
            'Quantity': 'sum',
            'Discount': 'mean'
        }).round(2)
        
        category_profit.columns = ['Total_Profit', 'Avg_Profit', 'Total_Sales', 
                                  'Total_Quantity', 'Avg_Discount']
        category_profit = category_profit.reset_index()
        category_profit['Profit_Margin'] = (category_profit['Total_Profit'] / category_profit['Total_Sales'] * 100).round(2)
        
        results['by_category'] = category_profit.sort_values('Profit_Margin', ascending=False)
        
        # Profit by region
        region_profit = self.df.groupby('Region').agg({
            'Profit': ['sum', 'mean'],
            'Sales': 'sum',
            'Quantity': 'sum'
        }).round(2)
        
        region_profit.columns = ['Total_Profit', 'Avg_Profit', 'Total_Sales', 'Total_Quantity']
        region_profit = region_profit.reset_index()
        region_profit['Profit_Margin'] = (region_profit['Total_Profit'] / region_profit['Total_Sales'] * 100).round(2)
        
        results['by_region'] = region_profit.sort_values('Profit_Margin', ascending=False)
        
        # Profit by segment
        segment_profit = self.df.groupby('Segment').agg({
            'Profit': ['sum', 'mean'],
            'Sales': 'sum',
            'Quantity': 'sum'
        }).round(2)
        
        segment_profit.columns = ['Total_Profit', 'Avg_Profit', 'Total_Sales', 'Total_Quantity']
        segment_profit = segment_profit.reset_index()
        segment_profit['Profit_Margin'] = (segment_profit['Total_Profit'] / segment_profit['Total_Sales'] * 100).round(2)
        
        results['by_segment'] = segment_profit.sort_values('Profit_Margin', ascending=False)
        
        logger.info("Profitability driver analysis completed")
        return results
    
    def analyze_discount_impact(self) -> Dict[str, any]:
        """
        Analyze the impact of discounts on profitability.
        
        Returns:
            Dictionary with discount impact analysis
        """
        logger.info("Analyzing discount impact on profitability")
        
        # Create discount brackets
        self.df['Discount_Bracket'] = pd.cut(
            self.df['Discount'],
            bins=[-0.001, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            labels=['0%', '1-10%', '11-20%', '21-30%', '31-40%', '41-50%', 
                   '51-60%', '61-70%', '71-80%', '81-90%', '91-100%']
        )
        
        # Analyze by discount bracket
        discount_analysis = self.df.groupby('Discount_Bracket').agg({
            'Profit': ['sum', 'mean', 'count'],
            'Sales': ['sum', 'mean'],
            'Quantity': 'sum'
        }).round(2)
        
        discount_analysis.columns = ['Total_Profit', 'Avg_Profit', 'Num_Transactions',
                                    'Total_Sales', 'Avg_Sales', 'Total_Quantity']
        discount_analysis = discount_analysis.reset_index()
        
        # Calculate metrics
        discount_analysis['Profit_Margin'] = (discount_analysis['Total_Profit'] / 
                                             discount_analysis['Total_Sales'] * 100).round(2)
        discount_analysis['Profit_per_Unit'] = (discount_analysis['Total_Profit'] / 
                                               discount_analysis['Total_Quantity']).round(2)
        
        # Correlation between discount and profit
        correlation = self.df['Discount'].corr(self.df['Profit'])
        
        results = {
            'discount_analysis': discount_analysis,
            'discount_profit_correlation': correlation,
            'optimal_discount': self._find_optimal_discount(discount_analysis)
        }
        
        logger.info(f"Discount-Profit correlation: {correlation:.3f}")
        return results
    
    def _find_optimal_discount(self, discount_analysis: pd.DataFrame) -> Dict:
        """
        Find optimal discount level for maximum profit.
        
        Args:
            discount_analysis: DataFrame with discount bracket analysis
            
        Returns:
            Dictionary with optimal discount information
        """
        # Find discount bracket with highest average profit
        max_profit_idx = discount_analysis['Avg_Profit'].idxmax()
        optimal = {
            'discount_bracket': discount_analysis.loc[max_profit_idx, 'Discount_Bracket'],
            'avg_profit': discount_analysis.loc[max_profit_idx, 'Avg_Profit'],
            'profit_margin': discount_analysis.loc[max_profit_idx, 'Profit_Margin']
        }
        
        return optimal
    
    def analyze_loss_making_products(self) -> pd.DataFrame:
        """
        Identify and analyze loss-making products.
        
        Returns:
            DataFrame with loss-making product analysis
        """
        logger.info("Analyzing loss-making products")
        
        # Identify loss-making products
        loss_products = self.df[self.df['Profit'] < 0].groupby(['Product ID', 'Product Name', 'Category']).agg({
            'Profit': ['sum', 'mean', 'count'],
            'Sales': ['sum', 'mean'],
            'Quantity': 'sum',
            'Discount': 'mean'
        }).round(2)
        
        loss_products.columns = ['Total_Loss', 'Avg_Loss', 'Num_Transactions',
                                'Total_Sales', 'Avg_Sales', 'Total_Quantity', 'Avg_Discount']
        loss_products = loss_products.reset_index()
        
        # Sort by total loss (most loss-making first)
        loss_products = loss_products.sort_values('Total_Loss', ascending=True)
        
        # Calculate loss ratio
        loss_products['Loss_Ratio'] = (loss_products['Total_Loss'].abs() / 
                                       loss_products['Total_Sales'] * 100).round(2)
        
        # Summary statistics
        total_loss = loss_products['Total_Loss'].sum()
        num_loss_products = len(loss_products)
        
        logger.info(f"Found {num_loss_products} loss-making products with total loss of ${total_loss:,.2f}")
        
        return loss_products
    
    def analyze_profit_trends(self, freq: str = 'M') -> pd.DataFrame:
        """
        Analyze profit trends over time.
        
        Args:
            freq: Frequency for resampling ('D', 'W', 'M', 'Q', 'Y')
            
        Returns:
            DataFrame with profit trends
        """
        logger.info(f"Analyzing profit trends with frequency: {freq}")
        
        # Ensure date column is datetime
        self.df['Order Date'] = pd.to_datetime(self.df['Order Date'])
        
        # Set date as index and resample
        profit_trends = self.df.set_index('Order Date').resample(freq).agg({
            'Profit': ['sum', 'mean', 'count'],
            'Sales': 'sum',
            'Quantity': 'sum'
        }).round(2)
        
        profit_trends.columns = ['Total_Profit', 'Avg_Profit', 'Num_Transactions',
                                'Total_Sales', 'Total_Quantity']
        profit_trends = profit_trends.reset_index()
        
        profit_trends['Profit_Margin'] = (profit_trends['Total_Profit'] / 
                                         profit_trends['Total_Sales'] * 100).round(2)
        profit_trends['Profit_per_Transaction'] = (profit_trends['Total_Profit'] / 
                                                  profit_trends['Num_Transactions']).round(2)
        
        # Add trend indicators
        profit_trends['Profit_Change'] = profit_trends['Total_Profit'].pct_change() * 100
        profit_trends['Profit_Change'] = profit_trends['Profit_Change'].round(2)
        
        logger.info(f"Generated profit trends with {len(profit_trends)} periods")
        return profit_trends
    
    def calculate_profitability_metrics(self) -> Dict[str, float]:
        """
        Calculate key profitability metrics.
        
        Returns:
            Dictionary with profitability metrics
        """
        logger.info("Calculating profitability metrics")
        
        metrics = {
            'gross_profit': self.df['Profit'].sum(),
            'gross_margin': (self.df['Profit'].sum() / self.df['Sales'].sum() * 100),
            'avg_transaction_profit': self.df['Profit'].mean(),
            'profit_per_unit': (self.df['Profit'].sum() / self.df['Quantity'].sum()),
            'profitable_transactions': (self.df['Profit'] > 0).sum(),
            'loss_making_transactions': (self.df['Profit'] < 0).sum(),
            'break_even_transactions': (self.df['Profit'] == 0).sum(),
            'profit_volatility': self.df['Profit'].std(),
            'profit_coefficient_variation': (self.df['Profit'].std() / self.df['Profit'].mean() * 100)
        }
        
        metrics['profitability_rate'] = (metrics['profitable_transactions'] / 
                                        len(self.df) * 100)
        
        # Log metrics
        for key, value in metrics.items():
            if isinstance(value, float):
                logger.info(f"{key}: {value:,.2f}")
            else:
                logger.info(f"{key}: {value}")
        
        return metrics