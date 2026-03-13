"""
Data loading module for the sales analytics project.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Union
from src.utils.logger import logger
from src.utils.config import config

class DataLoader:
    """Handle data loading operations."""
    
    def __init__(self):
        """Initialize DataLoader with configuration."""
        self.raw_path = Path(config.get('data.raw_path', 'data/raw/superstore_sales.csv'))
        self.processed_path = Path(config.get('data.processed_path', 'data/processed/cleaned_sales.csv'))
        self.batch_size = config.get('pipeline.batch_size', 10000)
        self.validate_data = config.get('pipeline.validate_data', True)
        
        project_root = Path(__file__).resolve().parents[2]
        if not self.raw_path.is_absolute() and not self.raw_path.exists():
            self.raw_path = project_root / self.raw_path
        if not self.processed_path.is_absolute() and not self.processed_path.exists():
            self.processed_path = project_root / self.processed_path
            
        # Create directories if they don't exist
        self.raw_path.parent.mkdir(parents=True, exist_ok=True)
        self.processed_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DataLoader initialized with raw path: {self.raw_path}")
    
    def load_raw_data(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load raw data from CSV file.
        
        Args:
            file_path: Optional custom file path
            
        Returns:
            DataFrame containing raw data
            
        Raises:
            FileNotFoundError: If data file doesn't exist
        """ 
        path = Path(file_path) if file_path else self.raw_path
        
        if not path.exists():
            error_msg = f"Data file not found: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            logger.info(f"Loading raw data from {path}")
            
            # Load data in chunks for large files
            if path.stat().st_size > 100 * 1024 * 1024:  # > 100MB
                chunks = []
                for chunk in pd.read_csv(path, chunksize=self.batch_size):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
                logger.info(f"Loaded {len(df)} rows in chunks")
            else:
                df = pd.read_csv(path, encoding='latin1')
                logger.info(f"Loaded {len(df)} rows from {path}")
            
            # Validate data if configured
            if self.validate_data:
                self._validate_raw_data(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def _validate_raw_data(self, df: pd.DataFrame) -> None:
        """
        Validate raw data structure and content.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If validation fails
        """
        logger.info("Validating raw data structure")
        
        # Check minimum rows
        if len(df) < 10:
            raise ValueError(f"Dataset too small: {len(df)} rows")
        
        # Check required columns
        required_columns = ['Order ID', 'Order Date', 'Ship Date', 'Customer ID', 
                           'Customer Name', 'Segment', 'Country', 'City', 'State',
                           'Region', 'Product ID', 'Category', 'Sub-Category',
                           'Product Name', 'Sales', 'Quantity', 'Discount', 'Profit']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Check for data types
        logger.info(f"Data types: {df.dtypes.to_dict()}")
        
        # Check for null values
        null_counts = df.isnull().sum()
        if null_counts.any():
            logger.warning(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
    
    def save_processed_data(self, df: pd.DataFrame, file_path: Optional[str] = None) -> None:
        """
        Save processed data to CSV.
        
        Args:
            df: DataFrame to save
            file_path: Optional custom file path
        """
        path = Path(file_path) if file_path else self.processed_path
        
        try:
            logger.info(f"Saving processed data to {path}")
            df.to_csv(path, index=False)
            logger.info(f"Saved {len(df)} rows to {path}")
            
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            raise
    
    def load_processed_data(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load processed data from CSV.
        
        Args:
            file_path: Optional custom file path
            
        Returns:
            DataFrame containing processed data
        """
        path = Path(file_path) if file_path else self.processed_path
        
        if not path.exists():
            logger.warning(f"Processed data not found at {path}, loading raw data instead")
            return self.load_raw_data()
        
        try:
            logger.info(f"Loading processed data from {path}")
            df = pd.read_csv(path, parse_dates=['Order Date', 'Ship Date'])
            logger.info(f"Loaded {len(df)} rows from {path}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading processed data: {str(e)}")
            raise