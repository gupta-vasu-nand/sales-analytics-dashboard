"""
Database connection module for the sales analytics project.
"""
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any
from src.utils.logger import logger
from src.utils.config import config

class DatabaseConnection:
    """Manage database connections and operations."""
    
    def __init__(self):
        """Initialize DatabaseConnection with configuration."""
        self.db_url = config.get_database_url()
        self.engine = None
        self._connect()
        logger.info(f"DatabaseConnection initialized with URL: {self.db_url}")
    
    def _connect(self):
        """Establish database connection."""
        try:
            self.engine = create_engine(
                self.db_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self) -> Generator:
        """
        Get database connection using context manager.
        
        Yields:
            Database connection
        """
        connection = self.engine.connect()
        try:
            yield connection
            connection.commit()
        except Exception as e:
            connection.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            connection.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            DataFrame with query results
        """
        try:
            with self.get_connection() as conn:
                result = pd.read_sql(text(query), conn, params=params)
            logger.info(f"Query executed successfully, returned {len(result)} rows")
            return result
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists in database.
        
        Args:
            table_name: Name of table to check
            
        Returns:
            True if table exists
        """
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a table.
        
        Args:
            table_name: Name of table
            
        Returns:
            Dictionary with table information
        """
        inspector = inspect(self.engine)
        
        info = {
            'columns': inspector.get_columns(table_name),
            'primary_keys': inspector.get_pk_constraint(table_name),
            'foreign_keys': inspector.get_foreign_keys(table_name),
            'indexes': inspector.get_indexes(table_name)
        }
        
        return info
    
    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")

# Create global database connection instance
db = DatabaseConnection()