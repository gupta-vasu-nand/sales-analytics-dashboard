"""
Feature engineering module for the sales analytics project.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.utils.logger import logger
from src.utils.config import config

class FeatureEngineer:
    """Handle feature engineering operations."""
    
    def __init__(self):
        """Initialize FeatureEngineer with configuration."""
        self.feature_config = config.get('features', {})
        self.date_features = self.feature_config.get('date_features', [])
        self.derived_features = self.feature_config.get('derived_features', [])
        
        self.engineered_features = []
        logger.info("FeatureEngineer initialized")
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main feature engineering pipeline.
        
        Args:
            df: Cleaned DataFrame
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Starting feature engineering process")
        
        # Make a copy to avoid modifying original
        df_feat = df.copy()
        
        # Apply feature engineering steps
        df_feat = self._create_date_features(df_feat)
        df_feat = self._create_financial_features(df_feat)
        df_feat = self._create_customer_features(df_feat)
        df_feat = self._create_product_features(df_feat)
        df_feat = self._create_segmentation_features(df_feat)
        df_feat = self._create_time_based_features(df_feat)
        
        logger.info(f"Feature engineering completed. Added {len(self.engineered_features)} new features")
        logger.info(f"New features: {self.engineered_features}")
        
        return df_feat
    
    def _create_date_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create features from date columns.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with date features
        """
        if 'Order Date' not in df.columns:
            logger.warning("Order Date column not found, skipping date features")
            return df
        
        # Extract basic date components
        if 'year' in self.date_features:
            df['Order_Year'] = df['Order Date'].dt.year
            df['Ship_Year'] = df['Ship Date'].dt.year
            self.engineered_features.extend(['Order_Year', 'Ship_Year'])
        
        if 'month' in self.date_features:
            df['Order_Month'] = df['Order Date'].dt.month
            df['Order_Month_Name'] = df['Order Date'].dt.month_name()
            df['Ship_Month'] = df['Ship Date'].dt.month
            self.engineered_features.extend(['Order_Month', 'Order_Month_Name', 'Ship_Month'])
        
        if 'quarter' in self.date_features:
            df['Order_Quarter'] = df['Order Date'].dt.quarter
            df['Ship_Quarter'] = df['Ship Date'].dt.quarter
            self.engineered_features.extend(['Order_Quarter', 'Ship_Quarter'])
        
        if 'day_of_week' in self.date_features:
            df['Order_DayOfWeek'] = df['Order Date'].dt.dayofweek
            df['Order_DayName'] = df['Order Date'].dt.day_name()
            self.engineered_features.extend(['Order_DayOfWeek', 'Order_DayName'])
        
        if 'is_weekend' in self.date_features:
            df['Is_Weekend'] = df['Order Date'].dt.dayofweek.isin([5, 6]).astype(int)
            self.engineered_features.append('Is_Weekend')
        
        # Calculate shipping time
        if 'shipping_days' in self.derived_features:
            df['Shipping_Days'] = (df['Ship Date'] - df['Order Date']).dt.days
            df['Shipping_Days'] = df['Shipping_Days'].clip(lower=0)  # No negative shipping days
            self.engineered_features.append('Shipping_Days')
        
        logger.info("Created date-based features")
        return df
    
    def _create_financial_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create financial metrics.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with financial features
        """
        # Profit margin
        if 'profit_margin' in self.derived_features:
            df['Profit_Margin'] = (df['Profit'] / df['Sales'] * 100).round(2)
            df['Profit_Margin'] = df['Profit_Margin'].replace([np.inf, -np.inf], np.nan)
            df['Profit_Margin'] = df['Profit_Margin'].fillna(0)
            self.engineered_features.append('Profit_Margin')
        
        # Discount amount
        if 'discount_amount' in self.derived_features:
            df['Discount_Amount'] = (df['Sales'] * df['Discount'] / (1 - df['Discount'])).round(2)
            df['Discount_Amount'] = df['Discount_Amount'].replace([np.inf, -np.inf], 0)
            df['Discount_Amount'] = df['Discount_Amount'].fillna(0)
            self.engineered_features.append('Discount_Amount')
        
        # Average order value per product
        df['Avg_Price_Per_Unit'] = (df['Sales'] / df['Quantity'].replace(0, np.nan)).round(2)
        df['Avg_Price_Per_Unit'] = df['Avg_Price_Per_Unit'].fillna(0)
        self.engineered_features.append('Avg_Price_Per_Unit')
        
        # Profit per unit
        df['Profit_Per_Unit'] = (df['Profit'] / df['Quantity'].replace(0, np.nan)).round(2)
        df['Profit_Per_Unit'] = df['Profit_Per_Unit'].fillna(0)
        self.engineered_features.append('Profit_Per_Unit')
        
        logger.info("Created financial features")
        return df
    
    def _create_customer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create customer-based features.
        """

        customer_stats = df.groupby('Customer ID').agg(
            Customer_Total_Sales=('Sales', 'sum'),
            Customer_Avg_Sales=('Sales', 'mean'),
            Customer_Order_Count=('Order ID', 'nunique'),
            Customer_Total_Profit=('Profit', 'sum')
        ).round(2).reset_index()

        # Merge back to original dataframe
        df = df.merge(customer_stats, on='Customer ID', how='left')

        # Customer segment based on total sales
        df['Customer_Segment_Value'] = pd.cut(
            df['Customer_Total_Sales'],
            bins=[0, 1000, 5000, 10000, float('inf')],
            labels=['Low Value', 'Medium Value', 'High Value', 'VIP']
        )

        self.engineered_features.extend([
            'Customer_Total_Sales',
            'Customer_Avg_Sales',
            'Customer_Order_Count',
            'Customer_Total_Profit',
            'Customer_Segment_Value'
        ])

        logger.info("Created customer-based features")
        return df
    
    def _create_product_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create product-based features.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with product features
        """
        # Product performance metrics
        product_stats = df.groupby('Product ID').agg({
            'Sales': ['sum', 'mean', 'count'],
            'Profit': ['sum', 'mean'],
            'Quantity': 'sum'
        }).round(2)
        
        product_stats.columns = ['Product_Total_Sales', 'Product_Avg_Sales', 
                                'Product_Order_Count', 'Product_Total_Profit',
                                'Product_Avg_Profit', 'Product_Total_Quantity']
        product_stats = product_stats.reset_index()
        
        # Merge back
        df = df.merge(product_stats, on='Product ID', how='left')
        
        # Product profitability score
        df['Product_Profitability'] = pd.cut(
            df['Product_Avg_Profit'],
            bins=[-float('inf'), 0, 50, 100, float('inf')],
            labels=['Loss Making', 'Low Profit', 'Medium Profit', 'High Profit']
        )
        
        self.engineered_features.extend([
            'Product_Total_Sales', 'Product_Avg_Sales', 'Product_Order_Count',
            'Product_Total_Profit', 'Product_Avg_Profit', 'Product_Total_Quantity',
            'Product_Profitability'
        ])
        
        logger.info("Created product-based features")
        return df
    
    def _create_segmentation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create RFM (Recency, Frequency, Monetary) segmentation.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with RFM features
        """
        # Get the latest date in the dataset
        max_date = df['Order Date'].max()
        
        # Calculate RFM metrics per customer
        rfm = df.groupby('Customer ID').agg({
            'Order Date': lambda x: (max_date - x.max()).days,  # Recency
            'Order ID': 'count',  # Frequency
            'Sales': 'sum'  # Monetary
        }).round(2)
        
        rfm.columns = ['Recency', 'Frequency', 'Monetary']
        rfm = rfm.reset_index()
        
        # Create RFM scores (1-4)
        rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1])
        rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
        rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4])
        
        # Combine scores
        rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
        
        # Customer segments
        segment_map = {
            '111': 'Lost', '112': 'Lost', '113': 'Lost', '114': 'Lost',
            '121': 'Hibernating', '122': 'Hibernating', '123': 'At Risk', '124': 'At Risk',
            '131': 'About to Sleep', '132': 'About to Sleep', '133': 'Need Attention', '134': 'Need Attention',
            '141': 'Promising', '142': 'Promising', '143': 'New Customers', '144': 'New Customers',
            '211': 'Potential Loyalists', '212': 'Potential Loyalists', '213': 'Potential Loyalists', '214': 'Potential Loyalists',
            '221': 'Potential Loyalists', '222': 'Loyal Customers', '223': 'Loyal Customers', '224': 'Champions',
            '231': 'Loyal Customers', '232': 'Loyal Customers', '233': 'Champions', '234': 'Champions',
            '241': 'Champions', '242': 'Champions', '243': 'Champions', '244': 'Champions'
        }
        
        rfm['Customer_Segment'] = rfm['RFM_Score'].map(segment_map).fillna('Other')
        
        # Merge back
        df = df.merge(rfm[['Customer ID', 'Recency', 'Frequency', 'Monetary', 'RFM_Score', 'Customer_Segment']], 
                     on='Customer ID', how='left')
        
        self.engineered_features.extend(['Recency', 'Frequency', 'Monetary', 'RFM_Score', 'Customer_Segment'])
        
        logger.info("Created RFM segmentation features")
        return df
    
    def _create_time_based_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create time-based aggregations.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with time-based features
        """
        # Season (based on month)
        df['Season'] = df['Order_Month'].map({
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Fall', 10: 'Fall', 11: 'Fall'
        })
        self.engineered_features.append('Season')
        
        # Day part (based on order date - assuming business hours)
        # Since we don't have time, we'll create a placeholder
        df['Order_Hour'] = 12  # Default to noon
        df['Day_Part'] = 'Afternoon'  # Default
        self.engineered_features.extend(['Order_Hour', 'Day_Part'])
        
        logger.info("Created time-based features")
        return df