"""
Configuration management for the sales analytics project.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv
from src.utils.logger import logger

class ConfigManager:
    """Manage configuration for the sales analytics project."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._load_environment()
        logger.info(f"Configuration loaded from {config_path}")
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load YAML configuration file.
        
        Returns:
            Dictionary containing configuration
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists() and not config_file.is_absolute():
                # Fallback to project root if not found in current directory
                config_file = Path(__file__).resolve().parents[2] / self.config_path
                
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return self._get_default_config()
    
    def _load_environment(self):
        """Load environment variables from .env file."""
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
            logger.info("Environment variables loaded from .env")
        else:
            logger.warning(".env file not found, using system environment variables")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'data': {
                'raw_path': 'data/raw/superstore_sales.csv',
                'processed_path': 'data/processed/cleaned_sales.csv',
                'database_path': 'data/sales_analytics.db'
            },
            'database': {
                'type': 'sqlite',
                'name': 'sales_analytics',
                'tables': {
                    'sales': 'sales_data',
                    'customers': 'customer_data',
                    'products': 'product_data'
                }
            },
            'pipeline': {
                'batch_size': 10000,
                'validate_data': True,
                'backup_raw': True
            },
            'analysis': {
                'date_column': 'Order Date',
                'sales_column': 'Sales',
                'profit_column': 'Profit',
                'customer_column': 'Customer ID'
            },
            'dashboard': {
                'title': 'Sales Analytics Dashboard',
                'theme': 'light',
                'refresh_rate': 3600
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/sales_analytics.log'
            },
            'features': {
                'date_features': ['year', 'month', 'quarter', 'day_of_week', 'is_weekend'],
                'derived_features': ['profit_margin', 'discount_amount', 'shipping_days']
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Dot-notation key (e.g., 'database.type')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
                
        return value
    
    def get_database_url(self) -> str:
        """
        Get database URL from configuration and environment.
        
        Returns:
            Database connection URL
        """
        db_type = self.get('database.type', 'sqlite')
        
        if db_type == 'sqlite':
            db_path = self.get('data.database_path', 'data/sales_analytics.db')
            return f"sqlite:///{db_path}"
        
        elif db_type == 'postgresql':
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '3333')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD', 'root')
            name = self.get('database.name', 'sales_analytics')
            
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

# Create global config instance
config = ConfigManager()