"""
Main pipeline module for the sales analytics project.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from src.utils.logger import logger
from src.utils.config import config
from src.data.load_data import DataLoader
from src.data.clean_data import DataCleaner
from src.data.feature_engineering import FeatureEngineer
from src.database.store_data import storage

class SalesPipeline:
    """Main pipeline for sales data processing."""
    
    def __init__(self):
        """Initialize pipeline components."""
        self.loader = DataLoader()
        self.cleaner = DataCleaner()
        self.feature_engineer = FeatureEngineer()
        self.pipeline_config = config.get('pipeline', {})
        logger.info("SalesPipeline initialized")
    
    def run_full_pipeline(self, raw_data_path: Optional[str] = None) -> pd.DataFrame:
        """
        Run full data pipeline.
        
        Args:
            raw_data_path: Optional path to raw data file
            
        Returns:
            Processed DataFrame
        """
        logger.info("Starting full data pipeline")
        start_time = datetime.now()
        
        try:
            # Step 1: Load data
            logger.info("Step 1: Loading raw data")
            raw_df = self.loader.load_raw_data(raw_data_path)
            
            # Step 2: Create backup if configured
            if self.pipeline_config.get('backup_raw', True):
                self._backup_raw_data(raw_df)
            
            # Step 3: Clean data
            logger.info("Step 2: Cleaning data")
            cleaned_df = self.cleaner.clean(raw_df)
            
            # Step 4: Feature engineering
            logger.info("Step 3: Engineering features")
            processed_df = self.feature_engineer.engineer_features(cleaned_df)
            
            # Step 5: Save processed data
            logger.info("Step 4: Saving processed data")
            self.loader.save_processed_data(processed_df)
            
            # Step 6: Store in database
            logger.info("Step 5: Storing in database")
            self._store_in_database(processed_df)
            
            # Calculate pipeline duration
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
            
            # Log pipeline statistics
            self._log_pipeline_stats(raw_df, processed_df)
            
            return processed_df
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise
    
    def _backup_raw_data(self, df: pd.DataFrame):
        """
        Create backup of raw data.
        
        Args:
            df: Raw DataFrame
        """
        backup_dir = Path("data/raw/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"raw_backup_{timestamp}.csv"
        
        df.to_csv(backup_path, index=False)
        logger.info(f"Raw data backed up to {backup_path}")
    
    def _store_in_database(self, df: pd.DataFrame):
        """
        Store processed data in database.
        
        Args:
            df: Processed DataFrame
        """
        # Create tables if they don't exist
        storage.create_tables()
        
        # Store data
        storage.store_sales_data(df)
        storage.update_customer_data(df)
        storage.update_product_data(df)
        
        logger.info("Data stored in database successfully")
    
    def _log_pipeline_stats(self, raw_df: pd.DataFrame, processed_df: pd.DataFrame):
        """
        Log pipeline statistics.
        
        Args:
            raw_df: Raw DataFrame
            processed_df: Processed DataFrame
        """
        logger.info("=== Pipeline Statistics ===")
        logger.info(f"Raw data rows: {len(raw_df)}")
        logger.info(f"Raw data columns: {len(raw_df.columns)}")
        logger.info(f"Processed data rows: {len(processed_df)}")
        logger.info(f"Processed data columns: {len(processed_df.columns)}")
        logger.info(f"New features added: {len(processed_df.columns) - len(raw_df.columns)}")
        
        # Memory usage
        raw_memory = raw_df.memory_usage(deep=True).sum() / 1024 / 1024
        processed_memory = processed_df.memory_usage(deep=True).sum() / 1024 / 1024
        logger.info(f"Raw data memory: {raw_memory:.2f} MB")
        logger.info(f"Processed data memory: {processed_memory:.2f} MB")
    
    def run_incremental_update(self, new_data_path: str) -> pd.DataFrame:
        """
        Run incremental update with new data.
        
        Args:
            new_data_path: Path to new data file
            
        Returns:
            Updated DataFrame
        """
        logger.info("Starting incremental update")
        
        # Load existing processed data
        existing_df = self.loader.load_processed_data()
        
        # Load and process new data
        new_raw_df = self.loader.load_raw_data(new_data_path)
        new_cleaned_df = self.cleaner.clean(new_raw_df)
        new_processed_df = self.feature_engineer.engineer_features(new_cleaned_df)
        
        # Combine with existing data
        combined_df = pd.concat([existing_df, new_processed_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['Order ID'], keep='last')
        
        # Save updated data
        self.loader.save_processed_data(combined_df)
        
        # Update database
        self._store_in_database(combined_df)
        
        logger.info(f"Incremental update completed. Total rows: {len(combined_df)}")
        return combined_df
    
    def validate_pipeline(self) -> Dict[str, Any]:
        """
        Validate pipeline components.
        
        Returns:
            Dictionary with validation results
        """
        logger.info("Validating pipeline components")
        
        validation_results = {
            'data_loader': False,
            'data_cleaner': False,
            'feature_engineer': False,
            'database': False,
            'overall': False
        }
        
        try:
            # Test data loader
            test_df = self.loader.load_raw_data()
            validation_results['data_loader'] = len(test_df) > 0
            
            # Test data cleaner
            test_cleaned = self.cleaner.clean(test_df.head(100))
            validation_results['data_cleaner'] = len(test_cleaned) > 0
            
            # Test feature engineer
            test_featured = self.feature_engineer.engineer_features(test_cleaned)
            validation_results['feature_engineer'] = len(test_featured.columns) > len(test_cleaned.columns)
            
            # Test database connection
            storage.create_tables()
            validation_results['database'] = True
            
            # Overall validation
            validation_results['overall'] = all([
                validation_results['data_loader'],
                validation_results['data_cleaner'],
                validation_results['feature_engineer'],
                validation_results['database']
            ])
            
        except Exception as e:
            logger.error(f"Pipeline validation failed: {str(e)}")
        
        logger.info(f"Pipeline validation results: {validation_results}")
        return validation_results

# Create global pipeline instance
pipeline = SalesPipeline()

if __name__ == "__main__":
    # Run pipeline when script is executed directly
    logger.info("Running pipeline as standalone script")
    processed_df = pipeline.run_full_pipeline()
    logger.info("Pipeline execution completed")