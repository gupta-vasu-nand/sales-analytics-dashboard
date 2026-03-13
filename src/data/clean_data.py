"""
Data cleaning module for the sales analytics project.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.utils.logger import logger

class DataCleaner:
    """Handle data cleaning operations."""
    
    def __init__(self):
        """Initialize DataCleaner."""
        self.cleaning_stats = {
            'initial_rows': 0,
            'final_rows': 0,
            'removed_duplicates': 0,
            'filled_nulls': 0,
            'removed_outliers': 0,
            'corrected_data_types': 0
        }
        logger.info("DataCleaner initialized")
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main cleaning pipeline.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        logger.info("Starting data cleaning process")
        self.cleaning_stats['initial_rows'] = len(df)
        
        # Make a copy to avoid modifying original
        df_clean = df.copy()
        
        # Apply cleaning steps
        df_clean = self._remove_duplicates(df_clean)
        df_clean = self._handle_missing_values(df_clean)
        df_clean = self._correct_data_types(df_clean)
        df_clean = self._handle_outliers(df_clean)
        df_clean = self._standardize_categories(df_clean)
        df_clean = self._clean_text_fields(df_clean)
        
        self.cleaning_stats['final_rows'] = len(df_clean)
        self._log_cleaning_stats()
        
        logger.info(f"Data cleaning completed. Rows: {len(df_clean)}")
        return df_clean
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate rows.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame without duplicates
        """
        initial_count = len(df)
        df = df.drop_duplicates()
        removed = initial_count - len(df)
        self.cleaning_stats['removed_duplicates'] = removed
        
        if removed > 0:
            logger.info(f"Removed {removed} duplicate rows")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in the dataset.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with handled missing values
        """
        # Check for missing values
        missing_before = df.isnull().sum().sum()
        
        # Handle numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().any():
                # Fill with median for numeric columns
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                self.cleaning_stats['filled_nulls'] += df[col].isnull().sum()
        
        # Handle categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].isnull().any():
                # Fill with mode for categorical columns
                mode_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
                df[col].fillna(mode_val, inplace=True)
                self.cleaning_stats['filled_nulls'] += df[col].isnull().sum()
        
        missing_after = df.isnull().sum().sum()
        logger.info(f"Handled missing values: {missing_before} -> {missing_after}")
        
        return df
    
    def _correct_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Correct data types for columns.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with corrected data types
        """
        corrections = 0
        
        # Date columns
        date_columns = ['Order Date', 'Ship Date']
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], format='%d/%m/%Y')
                    corrections += 1
                except:
                    try:
                        df[col] = pd.to_datetime(df[col])
                        corrections += 1
                    except Exception as e:
                        logger.warning(f"Could not convert {col} to datetime: {str(e)}")
        
        # Numeric columns
        numeric_columns = ['Sales', 'Quantity', 'Discount', 'Profit']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    corrections += 1
                except Exception as e:
                    logger.warning(f"Could not convert {col} to numeric: {str(e)}")
        
        # Categorical columns
        categorical_columns = ['Segment', 'Category', 'Sub-Category', 'Region']
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype('category')
                corrections += 1
        
        self.cleaning_stats['corrected_data_types'] = corrections
        logger.info(f"Corrected data types for {corrections} columns")
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle outliers in numeric columns using IQR clipping.
        """
        outliers_removed = 0

        columns_to_check = ['Sales', 'Profit', 'Quantity', 'Discount']

        for col in columns_to_check:
            if col in df.columns:

                # ensure numeric column is float to avoid dtype conflicts
                df[col] = df[col].astype(float)

                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1

                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                # count outliers
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                outliers_removed += len(outliers)

                # clip values instead of direct assignment
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)

        self.cleaning_stats['removed_outliers'] = outliers_removed

        if outliers_removed > 0:
            logger.info(f"Capped {outliers_removed} outliers")

        return df
    
    def _standardize_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize categorical values.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with standardized categories
        """
        # Standardize Region names
        if 'Region' in df.columns:
            df['Region'] = df['Region'].str.strip().str.title()
        
        # Standardize Segment
        if 'Segment' in df.columns:
            segment_mapping = {
                'consumer': 'Consumer',
                'corporate': 'Corporate',
                'home office': 'Home Office'
            }
            df['Segment'] = df['Segment'].str.lower().map(segment_mapping).fillna(df['Segment'])
        
        # Standardize Category
        if 'Category' in df.columns:
            df['Category'] = df['Category'].str.strip().str.title()
        
        # Standardize Sub-Category
        if 'Sub-Category' in df.columns:
            df['Sub-Category'] = df['Sub-Category'].str.strip().str.title()
        
        return df
    
    def _clean_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean text fields (remove extra spaces, standardize).
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with cleaned text fields
        """
        text_columns = ['Customer Name', 'Product Name', 'City', 'State', 'Country']
        
        for col in text_columns:
            if col in df.columns:
                # Remove extra spaces and strip
                df[col] = df[col].str.replace(r'\s+', ' ', regex=True).str.strip()
                # Title case for names
                if col in ['Customer Name', 'City', 'State', 'Country']:
                    df[col] = df[col].str.title()
        
        logger.info("Cleaned text fields")
        return df
    
    def _log_cleaning_stats(self) -> None:
        """Log cleaning statistics."""
        logger.info("=== Cleaning Statistics ===")
        logger.info(f"Initial rows: {self.cleaning_stats['initial_rows']}")
        logger.info(f"Final rows: {self.cleaning_stats['final_rows']}")
        logger.info(f"Removed duplicates: {self.cleaning_stats['removed_duplicates']}")
        logger.info(f"Filled nulls: {self.cleaning_stats['filled_nulls']}")
        logger.info(f"Handled outliers: {self.cleaning_stats['removed_outliers']}")
        logger.info(f"Corrected data types: {self.cleaning_stats['corrected_data_types']}")