"""
Data storage module for the sales analytics project.
"""
import pandas as pd
from sqlalchemy import text
from typing import List, Optional
from src.utils.logger import logger
from src.database.db_connection import db
from src.utils.config import config

class DataStorage:
    """Handle data storage operations."""
    
    def __init__(self):
        """Initialize DataStorage with configuration."""
        self.tables = config.get('database.tables', {})
        self.batch_size = config.get('pipeline.batch_size', 10000)
        logger.info("DataStorage initialized")
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        logger.info("Creating database tables")
        
        # Sales table
        sales_table = """
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            order_id VARCHAR(50),
            order_date DATE,
            ship_date DATE,
            ship_mode VARCHAR(50),
            customer_id VARCHAR(50),
            customer_name VARCHAR(100),
            segment VARCHAR(50),
            country VARCHAR(50),
            city VARCHAR(100),
            state VARCHAR(50),
            region VARCHAR(50),
            product_id VARCHAR(50),
            category VARCHAR(50),
            sub_category VARCHAR(50),
            product_name VARCHAR(200),
            sales DECIMAL(10,2),
            quantity INTEGER,
            discount DECIMAL(5,2),
            profit DECIMAL(10,2),
            order_year INTEGER,
            order_month INTEGER,
            order_quarter INTEGER,
            profit_margin DECIMAL(5,2),
            shipping_days INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """.format(table_name=self.tables.get('sales', 'sales_data'))
        
        # Customers table
        customers_table = """
        CREATE TABLE IF NOT EXISTS {table_name} (
            customer_id VARCHAR(50) PRIMARY KEY,
            customer_name VARCHAR(100),
            segment VARCHAR(50),
            total_sales DECIMAL(10,2),
            total_profit DECIMAL(10,2),
            order_count INTEGER,
            avg_order_value DECIMAL(10,2),
            first_purchase DATE,
            last_purchase DATE,
            customer_segment VARCHAR(50),
            rfm_score VARCHAR(3),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """.format(table_name=self.tables.get('customers', 'customer_data'))
        
        # Products table
        products_table = """
        CREATE TABLE IF NOT EXISTS {table_name} (
            product_id VARCHAR(50) PRIMARY KEY,
            product_name VARCHAR(200),
            category VARCHAR(50),
            sub_category VARCHAR(50),
            total_sales DECIMAL(10,2),
            total_profit DECIMAL(10,2),
            quantity_sold INTEGER,
            order_count INTEGER,
            avg_price DECIMAL(10,2),
            profit_margin DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """.format(table_name=self.tables.get('products', 'product_data'))
        
        # Execute table creation
        with db.get_connection() as conn:
            conn.execute(text(sales_table))
            conn.execute(text(customers_table))
            conn.execute(text(products_table))
        
        logger.info("Database tables created successfully")
    
    def store_sales_data(self, df: pd.DataFrame):
        """
        Store sales data in database.
        
        Args:
            df: DataFrame with sales data
        """
        table_name = self.tables.get('sales', 'sales_data')
        logger.info(f"Storing {len(df)} rows in {table_name}")
        
        try:
            df_to_store = df.copy()

            # rename dataframe columns to match SQL schema
            df_to_store.columns = (
                df_to_store.columns
                .str.strip()
                .str.lower()
                .str.replace(" ", "_")
                .str.replace("-", "_")
            )

            # keep only columns that exist in the SQL table
            allowed_columns = [
                "order_id",
                "order_date",
                "ship_date",
                "ship_mode",
                "customer_id",
                "customer_name",
                "segment",
                "country",
                "city",
                "state",
                "region",
                "product_id",
                "category",
                "sub_category",
                "product_name",
                "sales",
                "quantity",
                "discount",
                "profit",
                "order_year",
                "order_month",
                "order_quarter",
                "profit_margin",
                "shipping_days"
            ]

            df_to_store = df_to_store[allowed_columns]

            # Convert date columns
            for col in ['order_date', 'ship_date']:
                if col in df_to_store.columns:
                    df_to_store[col] = pd.to_datetime(df_to_store[col])
            
            # Store in batches
            for i in range(0, len(df_to_store), self.batch_size):
                batch = df_to_store.iloc[i:i + self.batch_size]
                batch.to_sql(
                    table_name,
                    db.engine,
                    if_exists='append',
                    index=False
                )
                logger.info(f"Stored batch {i//self.batch_size + 1}")
            
            logger.info(f"Successfully stored {len(df_to_store)} rows in {table_name}")
            
        except Exception as e:
            logger.error(f"Error storing sales data: {str(e)}")
            raise
    
    def update_customer_data(self, df: pd.DataFrame):
        """
        Update customer data in database.
        
        Args:
            df: DataFrame with sales data
        """
        table_name = self.tables.get('customers', 'customer_data')
        logger.info(f"Updating customer data in {table_name}")
        
        try:
            # Aggregate customer data
            customer_data = df.groupby(['Customer ID', 'Customer Name', 'Segment']).agg({
                'Sales': ['sum', 'mean'],
                'Profit': 'sum',
                'Order ID': 'nunique',
                'Order Date': ['min', 'max']
            }).round(2)
            
            customer_data.columns = ['total_sales', 'avg_order_value', 
                                    'total_profit', 'order_count',
                                    'first_purchase', 'last_purchase']
            customer_data = customer_data.reset_index()
            
            # Add derived columns
            customer_data['customer_segment'] = pd.cut(
                customer_data['total_sales'],
                bins=[0, 1000, 5000, 10000, float('inf')],
                labels=['Low Value', 'Medium Value', 'High Value', 'VIP']
            )
            
            # Store in database
            customer_data.to_sql(
                table_name,
                db.engine,
                if_exists='replace',
                index=False
            )
            
            logger.info(f"Successfully updated {len(customer_data)} customers")
            
        except Exception as e:
            logger.error(f"Error updating customer data: {str(e)}")
            raise
    
    def update_product_data(self, df: pd.DataFrame):
        """
        Update product data in database.
        
        Args:
            df: DataFrame with sales data
        """
        table_name = self.tables.get('products', 'product_data')
        logger.info(f"Updating product data in {table_name}")
        
        try:
            # Aggregate product data
            product_data = df.groupby(['Product ID', 'Product Name', 'Category', 'Sub-Category']).agg({
                'Sales': ['sum', 'mean'],
                'Profit': ['sum', 'mean'],
                'Quantity': 'sum',
                'Order ID': 'nunique'
            }).round(2)
            
            product_data.columns = ['total_sales', 'avg_price',
                                   'total_profit', 'avg_profit',
                                   'quantity_sold', 'order_count']
            product_data = product_data.reset_index()
            
            # Add derived columns
            product_data['profit_margin'] = (product_data['total_profit'] / 
                                            product_data['total_sales'] * 100).round(2)
            
            # Store in database
            product_data.to_sql(
                table_name,
                db.engine,
                if_exists='replace',
                index=False
            )
            
            logger.info(f"Successfully updated {len(product_data)} products")
            
        except Exception as e:
            logger.error(f"Error updating product data: {str(e)}")
            raise
    
    def load_data_from_db(self, table_name: Optional[str] = None) -> pd.DataFrame:
        """
        Load data from database.
        
        Args:
            table_name: Name of table to load from
            
        Returns:
            DataFrame with loaded data
        """
        if table_name is None:
            table_name = self.tables.get('sales', 'sales_data')
        
        logger.info(f"Loading data from {table_name}")
        
        try:
            query = f"SELECT * FROM {table_name}"
            df = db.execute_query(query)
            logger.info(f"Loaded {len(df)} rows from {table_name}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data from database: {str(e)}")
            raise

# Create global data storage instance
storage = DataStorage()