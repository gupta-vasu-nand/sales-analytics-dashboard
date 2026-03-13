# Sales Analytics Dashboard

A production-grade Sales Analytics Dashboard built using Python, Streamlit, PostgreSQL, and advanced data analysis techniques. The project demonstrates a complete analytics workflow including data ingestion, data cleaning, feature engineering, exploratory data analysis, database integration, and interactive business intelligence dashboards.

This project simulates a real-world analytics platform used by business teams to monitor revenue performance, understand customer behavior, and evaluate product profitability.

---

# Project Overview

This repository implements a complete data analytics system consisting of:

• Automated data pipeline (ETL workflow)
• Feature engineering and customer segmentation
• SQL database storage and retrieval
• Analytical modules for business insights
• Interactive dashboard for decision making

The system processes raw transactional sales data and converts it into structured insights through automated analytics pipelines.

---

# System Architecture

```
Raw Data (CSV)
      │
      ▼
Data Pipeline (ETL)
      │
      ▼
Data Cleaning & Feature Engineering
      │
      ▼
Database Storage (PostgreSQL / SQLite)
      │
      ▼
Analytics Modules
      │
      ▼
Interactive Dashboard (Streamlit)
```

The architecture separates responsibilities into modular layers to ensure scalability and maintainability.

---

# Dataset

This project uses the Superstore Sales Dataset, a commonly used retail analytics dataset.

Dataset Statistics

Total Orders: 9,994
Customers: 793
Products: 1,862
Categories: 3
Regions: 4
Time Period: 2014 – 2017

---

# Dataset Fields

Order Information

• Order ID
• Order Date
• Ship Date
• Ship Mode

Customer Information

• Customer ID
• Customer Name
• Segment

Location

• Country
• City
• State
• Postal Code
• Region

Product Information

• Product ID
• Category
• Sub-Category
• Product Name

Sales Metrics

• Sales
• Quantity
• Discount
• Profit

---

# Key Features

## Data Pipeline

• Automated data ingestion from CSV files
• Data validation and integrity checks
• Missing value handling
• Outlier detection and capping
• Structured feature engineering pipeline

## Feature Engineering

The pipeline generates several analytical features including:

• Profit Margin
• Shipping Duration
• Seasonal Sales Indicators
• Customer Lifetime Metrics
• Product Performance Metrics

Customer analytics features include:

• RFM Segmentation (Recency, Frequency, Monetary)
• Customer Value Segments
• Customer Purchase Behavior Metrics

## Sales Analysis

The analytics modules provide:

• Time-series revenue analysis
• Regional performance comparison
• Category and sub-category performance
• Product profitability evaluation
• Sales vs profit correlation analysis

## Machine Learning

Customer clustering is implemented using:

K-Means Clustering

Used for customer segmentation based on behavioral metrics.

---

# Dashboard

The interactive dashboard allows users to explore business metrics visually.

Key capabilities include:

• Revenue and profit KPIs
• Sales trend visualization
• Regional performance analysis
• Customer segmentation insights
• Top-performing product analysis
• Interactive filtering by category, region, and time period

---

# Dashboard Preview

## Main Dashboard Overview

![Dashboard Overview](assets/images/dashboard_overview.png)

---

## Monthly Sales Trends

![Sales Trends](assets/images/sales_trend.png)

---

## Customer Segmentation

![Customer Segmentation](assets/images/customer_segmentation.png)

---

## Product Performance Analysis

![Product Performance](assets/images/product_performance.png)

---

# Technology Stack

Programming Language

Python

Data Processing

Pandas
NumPy

Visualization

Plotly
Matplotlib
Seaborn

Machine Learning

Scikit-Learn

Dashboard

Streamlit

Database

PostgreSQL
SQLite

Data Engineering

SQLAlchemy
YAML Configuration
Modular ETL Pipeline

---

# Project Structure

```
sales-analytics-dashboard
│
├── dashboard
│   └── app.py
│
├── src
│   ├── data
│   │   ├── load_data.py
│   │   ├── clean_data.py
│   │   └── feature_engineering.py
│   │
│   ├── analysis
│   │   ├── sales_analysis.py
│   │   ├── customer_analysis.py
│   │   └── product_analysis.py
│   │
│   ├── database
│   │   ├── db_connection.py
│   │   └── store_data.py
│   │
│   └── utils
│       ├── logger.py
│       └── config.py
│
├── data
│   ├── raw
│   └── processed
│
├── config.yaml
├── requirements.txt
└── README.md
```

---

# Installation

Prerequisites

Python 3.9 or higher
pip package manager
Git

---

## Clone Repository

```
git clone https://github.com/gupta-vasu-nand/sales-analytics-dashboard.git
cd sales-analytics-dashboard
```

---

## Create Virtual Environment

```
python -m venv venv
```

Activate environment

Windows

```
venv\Scripts\activate
```

Mac/Linux

```
source venv/bin/activate
```

---

## Install Dependencies

```
pip install -r requirements.txt
```

---

# Running the Data Pipeline

Execute the ETL pipeline:

```
python -m src.pipeline.run_pipeline
```

This step will:

1. Load the raw dataset
2. Clean the data
3. Engineer analytical features
4. Store processed data in the database

---

# Running the Dashboard

Start the Streamlit dashboard:

```
python -m streamlit run dashboard/app.py
```

The dashboard will be available at:

```
http://localhost:8501
```

---

# Business Insights Generated

The analytics system can answer key business questions such as:

• Which products generate the highest revenue?
• Which regions contribute most to sales?
• Which customers are most valuable?
• What are the seasonal sales trends?
• Which products have the highest profit margins?

---

# Future Improvements

Planned enhancements include:

• Sales forecasting using time-series models
• Customer churn prediction
• Real-time data pipeline using Airflow
• Cloud deployment (AWS / GCP)
• Advanced recommendation systems

---

# Author

Vasu Nand Gupta

GitHub
https://github.com/gupta-vasu-nand

---

# License

This project is licensed under the MIT License.
