"""
Tests for data pipeline components.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.load_data import DataLoader
from src.data.clean_data import DataCleaner
from src.data.feature_engineering import FeatureEngineer
from src.pipeline.run_pipeline import SalesPipeline

class TestDataLoader:
    """Test DataLoader class."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame({
            'Order ID': ['ORD-1', 'ORD-2'],
            'Order Date': ['01/01/2023', '02/01/2023'],
            'Ship Date': ['03/01/2023', '04/01/2023'],
            'Customer ID': ['CUST-1', 'CUST-2'],
            'Customer Name': ['John Doe', 'Jane Smith'],
            'Segment': ['Consumer', 'Corporate'],
            'Country': ['United States', 'United States'],
            'City': ['New York', 'Los Angeles'],
            'State': ['New York', 'California'],
            'Region': ['East', 'West'],
            'Product ID': ['PROD-1', 'PROD-2'],
            'Category': ['Furniture', 'Technology'],
            'Sub-Category': ['Chairs', 'Phones'],
            'Product Name': ['Office Chair', 'Smartphone'],
            'Sales': [1000.00, 2000.00],
            'Quantity': [2, 1],
            'Discount': [0.1, 0.0],
            'Profit': [200.00, 400.00]
        })
    
    def test_load_raw_data(self, sample_data, tmp_path):
        """Test loading raw data."""
        # Save sample data to temp file
        file_path = tmp_path / "test_data.csv"
        sample_data.to_csv(file_path, index=False)
        
        loader = DataLoader()
        df = loader.load_raw_data(file_path)
        
        assert len(df) == 2
        assert all(col in df.columns for col in sample_data.columns)
    
    def test_save_processed_data(self, sample_data, tmp_path):
        """Test saving processed data."""
        loader = DataLoader()
        file_path = tmp_path / "processed_data.csv"
        
        loader.save_processed_data(sample_data, file_path)
        assert file_path.exists()
        
        # Load and verify
        loaded_df = pd.read_csv(file_path)
        assert len(loaded_df) == len(sample_data)

class TestDataCleaner:
    """Test DataCleaner class."""
    
    @pytest.fixture
    def dirty_data(self):
        """Create dirty data for testing."""
        return pd.DataFrame({
            'Order ID': ['ORD-1', 'ORD-1', 'ORD-2'],  # Duplicate
            'Order Date': ['01/01/2023', '01/01/2023', 'invalid_date'],
            'Ship Date': ['03/01/2023', '03/01/2023', None],
            'Sales': [1000, 1000, 'invalid'],
            'Profit': [200, 200, None],
            'Quantity': [2, 2, -5],  # Negative quantity
            'Discount': [0.1, 0.1, 1.5],  # Invalid discount
            'Customer Name': ['John  Doe', 'John  Doe', None],
            'Region': ['East', 'East', 'east']
        })
    
    def test_clean_data(self, dirty_data):
        """Test data cleaning functionality."""
        cleaner = DataCleaner()
        cleaned_df = cleaner.clean(dirty_data)
        
        # Check duplicates removed
        assert len(cleaned_df) < len(dirty_data)
        
        # Check missing values handled
        assert cleaned_df.isnull().sum().sum() == 0
        
        # Check data types
        assert pd.api.types.is_numeric_dtype(cleaned_df['Sales'])
        assert pd.api.types.is_numeric_dtype(cleaned_df['Quantity'])
        
        # Check outlier handling
        assert cleaned_df['Quantity'].min() >= 0
        assert cleaned_df['Discount'].max() <= 1.0
    
    def test_remove_duplicates(self):
        """Test duplicate removal."""
        cleaner = DataCleaner()
        df = pd.DataFrame({
            'id': [1, 1, 2, 3],
            'value': ['a', 'a', 'b', 'c']
        })
        
        cleaned_df = cleaner._remove_duplicates(df)
        assert len(cleaned_df) == 3
        assert cleaner.cleaning_stats['removed_duplicates'] == 1

class TestFeatureEngineer:
    """Test FeatureEngineer class."""
    
    @pytest.fixture
    def clean_data(self):
        """Create clean data for testing."""
        return pd.DataFrame({
            'Order ID': ['ORD-1', 'ORD-2', 'ORD-3'],
            'Order Date': pd.to_datetime(['2023-01-01', '2023-02-15', '2023-03-20']),
            'Ship Date': pd.to_datetime(['2023-01-05', '2023-02-20', '2023-03-25']),
            'Customer ID': ['CUST-1', 'CUST-1', 'CUST-2'],
            'Product ID': ['PROD-1', 'PROD-2', 'PROD-1'],
            'Sales': [1000, 2000, 1500],
            'Profit': [200, 400, 300],
            'Quantity': [2, 1, 3],
            'Discount': [0.1, 0.0, 0.15],
            'Category': ['Furniture', 'Technology', 'Furniture'],
            'Sub-Category': ['Chairs', 'Phones', 'Tables'],
            'Region': ['East', 'West', 'East'],
            'Segment': ['Consumer', 'Corporate', 'Consumer']
        })
    
    def test_create_date_features(self, clean_data):
        """Test date feature creation."""
        engineer = FeatureEngineer()
        df = engineer._create_date_features(clean_data)
        
        assert 'Order_Year' in df.columns
        assert 'Order_Month' in df.columns
        assert 'Order_Quarter' in df.columns
        assert 'Shipping_Days' in df.columns
        assert df['Shipping_Days'].iloc[0] == 4
    
    def test_create_financial_features(self, clean_data):
        """Test financial feature creation."""
        engineer = FeatureEngineer()
        df = engineer._create_financial_features(clean_data)
        
        assert 'Profit_Margin' in df.columns
        assert 'Discount_Amount' in df.columns
        assert 'Avg_Price_Per_Unit' in df.columns
        
        # Check calculations
        assert df['Profit_Margin'].iloc[0] == 20.0  # (200/1000)*100
        assert df['Discount_Amount'].iloc[0] == pytest.approx(111.11, 0.1)
    
    def test_engineer_features(self, clean_data):
        """Test full feature engineering pipeline."""
        engineer = FeatureEngineer()
        df = engineer.engineer_features(clean_data)
        
        # Check that new features were added
        assert len(df.columns) > len(clean_data.columns)
        assert len(engineer.engineered_features) > 0
        
        # Check specific features
        assert 'Customer_Total_Sales' in df.columns
        assert 'Product_Total_Sales' in df.columns
        assert 'Customer_Segment' in df.columns

class TestSalesPipeline:
    """Test SalesPipeline class."""
    
    @pytest.fixture
    def sample_pipeline(self):
        """Create pipeline instance for testing."""
        return SalesPipeline()
    
    def test_validate_pipeline(self, sample_pipeline):
        """Test pipeline validation."""
        results = sample_pipeline.validate_pipeline()
        
        assert isinstance(results, dict)
        assert 'data_loader' in results
        assert 'data_cleaner' in results
        assert 'feature_engineer' in results
        assert 'database' in results
        assert 'overall' in results

if __name__ == "__main__":
    pytest.main([__file__, "-v"])