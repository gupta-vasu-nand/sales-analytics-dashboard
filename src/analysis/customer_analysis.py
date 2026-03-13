"""
Customer analysis module for the sales analytics project.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from src.utils.logger import logger

class CustomerAnalyzer:
    """Handle customer analysis operations."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize CustomerAnalyzer with data.
        
        Args:
            df: DataFrame containing sales data
        """
        self.df = df
        self.customer_metrics = None
        logger.info("CustomerAnalyzer initialized")
    
    def segment_customers(self, n_clusters: int = 4) -> pd.DataFrame:
        """
        Segment customers using clustering.
        
        Args:
            n_clusters: Number of customer segments
            
        Returns:
            DataFrame with customer segments
        """
        logger.info(f"Segmenting customers into {n_clusters} clusters")
        
        # Prepare customer-level features
        customer_features = self.df.groupby('Customer ID').agg({
            'Sales': ['sum', 'mean', 'count'],
            'Profit': ['sum', 'mean'],
            'Quantity': 'sum',
            'Discount': 'mean',
            'Order Date': lambda x: (pd.Timestamp.now() - pd.to_datetime(x).max()).days
        }).round(2)
        
        customer_features.columns = ['Total_Sales', 'Avg_Sales', 'Frequency',
                                    'Total_Profit', 'Avg_Profit', 'Total_Quantity',
                                    'Avg_Discount', 'Recency']
        customer_features = customer_features.reset_index()
        
        # Add customer name and segment
        customer_info = self.df[['Customer ID', 'Customer Name', 'Segment']].drop_duplicates('Customer ID')
        customer_features = customer_features.merge(customer_info, on='Customer ID', how='left')
        
        # Select features for clustering
        features_for_clustering = ['Total_Sales', 'Frequency', 'Avg_Profit', 'Recency']
        X = customer_features[features_for_clustering].fillna(0)
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        customer_features['Cluster'] = kmeans.fit_predict(X_scaled)
        
        # Name clusters based on characteristics
        cluster_names = self._name_clusters(customer_features, kmeans.cluster_centers_, features_for_clustering)
        customer_features['Segment_Name'] = customer_features['Cluster'].map(cluster_names)
        
        # Add RFM segmentation if available
        if 'Recency' in customer_features.columns and 'Frequency' in customer_features.columns:
            customer_features = self._add_rfm_segmentation(customer_features)
        
        self.customer_metrics = customer_features
        
        logger.info(f"Created {n_clusters} customer segments")
        logger.info(f"Segment distribution: {customer_features['Segment_Name'].value_counts().to_dict()}")
        
        return customer_features
    
    def _name_clusters(self, df: pd.DataFrame, centers: np.ndarray, features: List[str]) -> Dict:
        """
        Name clusters based on their characteristics.
        
        Args:
            df: DataFrame with cluster assignments
            centers: Cluster centers
            features: Feature names
            
        Returns:
            Dictionary mapping cluster numbers to names
        """
        cluster_names = {}
        
        for i, center in enumerate(centers):
            cluster_data = df[df['Cluster'] == i]
            
            avg_sales = cluster_data['Total_Sales'].mean()
            avg_freq = cluster_data['Frequency'].mean()
            avg_recency = cluster_data['Recency'].mean()
            
            if avg_sales > df['Total_Sales'].quantile(0.75) and avg_freq > df['Frequency'].quantile(0.75):
                name = "VIP Customers"
            elif avg_sales > df['Total_Sales'].median() and avg_recency < df['Recency'].median():
                name = "Loyal Customers"
            elif avg_freq > df['Frequency'].median() and avg_recency < df['Recency'].median():
                name = "Frequent Buyers"
            elif avg_recency > df['Recency'].quantile(0.75):
                name = "Churned Customers"
            elif avg_sales < df['Total_Sales'].quantile(0.25):
                name = "Low Value Customers"
            else:
                name = "Regular Customers"
            
            cluster_names[i] = name
        
        return cluster_names
    
    def _add_rfm_segmentation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add RFM (Recency, Frequency, Monetary) segmentation.
        
        Args:
            df: DataFrame with customer metrics
            
        Returns:
            DataFrame with RFM segments
        """
        # Create RFM scores (1-4)
        df['R_Score'] = pd.qcut(df['Recency'], 4, labels=[4, 3, 2, 1])
        df['F_Score'] = pd.qcut(df['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
        df['M_Score'] = pd.qcut(df['Total_Sales'], 4, labels=[1, 2, 3, 4])
        
        # Combine scores
        df['RFM_Score'] = df['R_Score'].astype(str) + df['F_Score'].astype(str) + df['M_Score'].astype(str)
        
        # RFM segments
        rfm_segments = {
            '111': 'Best Customers', '112': 'Loyal Customers', '113': 'Potential Loyalists',
            '121': 'New Customers', '122': 'Promising', '123': 'Need Attention',
            '131': 'About to Sleep', '132': 'At Risk', '133': 'Cannot Lose Them',
            '141': 'Hibernating', '142': 'Lost'
        }
        
        df['RFM_Segment'] = df['RFM_Score'].map(rfm_segments).fillna('Other')
        
        return df
    
    def analyze_customer_lifetime_value(self) -> pd.DataFrame:
        """
        Calculate Customer Lifetime Value (CLV) metrics.
        
        Returns:
            DataFrame with CLV metrics
        """
        logger.info("Calculating Customer Lifetime Value metrics")
        
        if self.customer_metrics is None:
            self.customer_metrics = self.segment_customers()
        
        # Calculate CLV components
        df_clv = self.customer_metrics.copy()
        
        # Average purchase value
        df_clv['Avg_Purchase_Value'] = df_clv['Total_Sales'] / df_clv['Frequency']
        
        # Average purchase frequency rate
        df_clv['Purchase_Freq_Rate'] = df_clv['Frequency'] / df_clv['Recency'].clip(lower=1) * 30  # per month
        
        # Customer value
        df_clv['Customer_Value'] = df_clv['Avg_Purchase_Value'] * df_clv['Purchase_Freq_Rate']
        
        # Average customer lifespan (simplified - using recency as proxy)
        df_clv['Avg_Lifespan'] = df_clv['Recency'] / 30  # in months
        
        # CLV
        df_clv['CLV'] = df_clv['Customer_Value'] * df_clv['Avg_Lifespan']
        
        # Profit-based CLV
        df_clv['Avg_Profit_Per_Purchase'] = df_clv['Total_Profit'] / df_clv['Frequency']
        df_clv['CLV_Profit'] = df_clv['Avg_Profit_Per_Purchase'] * df_clv['Purchase_Freq_Rate'] * df_clv['Avg_Lifespan']
        
        logger.info(f"Calculated CLV for {len(df_clv)} customers")
        logger.info(f"Average CLV: ${df_clv['CLV'].mean():,.2f}")
        
        return df_clv
    
    def analyze_customer_behavior(self) -> Dict[str, any]:
        """
        Analyze customer behavior patterns.
        
        Returns:
            Dictionary with behavior analysis results
        """
        logger.info("Analyzing customer behavior")
        
        if self.customer_metrics is None:
            self.customer_metrics = self.segment_customers()
        
        results = {}
        
        # Purchase patterns by segment
        results['segment_patterns'] = self.customer_metrics.groupby('Segment_Name').agg({
            'Total_Sales': ['mean', 'sum'],
            'Frequency': 'mean',
            'Avg_Sales': 'mean',
            'Total_Profit': ['mean', 'sum'],
            'Recency': 'mean'
        }).round(2)
        
        # Category preferences by segment
        category_preferences = self.df.merge(
            self.customer_metrics[['Customer ID', 'Segment_Name']], 
            on='Customer ID', how='left'
        ).groupby(['Segment_Name', 'Category']).agg({
            'Sales': 'sum',
            'Quantity': 'sum'
        }).round(2)
        
        results['category_preferences'] = category_preferences
        
        # Seasonal behavior
        seasonal = self.df.copy()
        seasonal['Month'] = pd.to_datetime(seasonal['Order Date']).dt.month
        seasonal = seasonal.merge(
            self.customer_metrics[['Customer ID', 'Segment_Name']], 
            on='Customer ID', how='left'
        ).groupby(['Segment_Name', 'Month']).agg({
            'Sales': 'sum',
            'Quantity': 'sum'
        }).round(2)
        
        results['seasonal_patterns'] = seasonal
        
        logger.info("Customer behavior analysis completed")
        return results
    
    def identify_high_value_customers(self, top_n: int = 100) -> pd.DataFrame:
        """
        Identify high-value customers based on multiple metrics.
        
        Args:
            top_n: Number of top customers to identify
            
        Returns:
            DataFrame with high-value customers
        """
        logger.info(f"Identifying top {top_n} high-value customers")
        
        if self.customer_metrics is None:
            self.customer_metrics = self.segment_customers()
        
        # Create composite score
        metrics = ['Total_Sales', 'Total_Profit', 'Frequency', 'Avg_Sales']
        
        # Normalize metrics
        for metric in metrics:
            col_name = f'{metric}_norm'
            max_val = self.customer_metrics[metric].max()
            if max_val > 0:
                self.customer_metrics[col_name] = self.customer_metrics[metric] / max_val
            else:
                self.customer_metrics[col_name] = 0
        
        # Calculate composite score
        self.customer_metrics['Value_Score'] = (
            self.customer_metrics['Total_Sales_norm'] * 0.3 +
            self.customer_metrics['Total_Profit_norm'] * 0.3 +
            self.customer_metrics['Frequency_norm'] * 0.2 +
            self.customer_metrics['Avg_Sales_norm'] * 0.2
        )
        
        # Get top customers
        high_value = self.customer_metrics.nlargest(top_n, 'Value_Score')[
            ['Customer ID', 'Customer Name', 'Segment', 'Total_Sales', 'Total_Profit', 
             'Frequency', 'Segment_Name', 'Value_Score']
        ]
        
        logger.info(f"Identified {len(high_value)} high-value customers")
        
        return high_value