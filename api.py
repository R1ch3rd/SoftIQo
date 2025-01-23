from fastapi import FastAPI, Form,HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import create_engine, MetaData, Table, insert, delete, select
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from fastapi.responses import HTMLResponse
from sklearn.preprocessing import LabelEncoder
import base64
import time
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import os

app = FastAPI()
load_dotenv()
origins = [
    # "https://softiqo-1.onrender.com/analysis",  # Replace with the frontend URL
    "https://softiqo-1.onrender.com",  # Your hosted backend URL if necessary
    # "https://softiqo-1.onrender.com/insert_record",
    # "https://softiqo-1.onrender.com/delete_record",
    # "https://softiqo-1.onrender.com/get_record"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connection_url = os.getenv("connection_url")
connection_string = connection_url #modify password

def connect_to_db():
    retries = 5
    delay = 2  # seconds

    for attempt in range(retries):
        try:
            engine = create_engine(connection_string)
            metadata = MetaData(schema="public")
            metadata.reflect(bind=engine)
            table_name = "sales_transactions"
            selected_table = metadata.tables[f"public.{table_name}"]
            print("Database connection established.")
            return engine, metadata, selected_table
        except Exception as e:
            print(f"Database connection attempt {attempt + 1} failed: {e}")
            time.sleep(delay)

    print("Failed to connect to the database after 5 attempts.")
    return None,None,None

engine, metadata, sales_transactions =connect_to_db()

# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serves the main frontend HTML page"""
    try:
        with open("front.html", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: Frontend file not found</h1>")
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading frontend: {str(e)}</h1>")

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify system status
    """
    try:
        # Test database connection
        with engine.connect() as connection:
            result = connection.execute("SELECT 1").fetchone()
            db_status = "healthy" if result[0] == 1 else "unhealthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "database": db_status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
@app.post("/insert_record")
async def insert_record(
    sku: str = Form(...),
    sale_channel: str = Form(...),
    transaction_datetime: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...)
):
    try:
        # Handle optional microseconds in the datetime format
        try:
            parsed_datetime = datetime.strptime(transaction_datetime, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            parsed_datetime = datetime.strptime(transaction_datetime, "%Y-%m-%d %H:%M:%S")

        record = {
            "sku": sku,
            "sale_channel": sale_channel,
            "transaction_datetime": parsed_datetime,
            "quantity": quantity,
            "price": price
        }

        # Validate sale channel
        valid_channels = ['Online', 'Store 1', 'Store 2', 'Marketplace']
        if record['sale_channel'] not in valid_channels:
            return JSONResponse(
                content={
                    "error": f"Invalid sale channel. Must be one of: {', '.join(valid_channels)}"
                },
                status_code=400
            )

        # Validate SKU format
        if not any(record['sku'].startswith(prefix) for prefix in ['ELEC', 'CLT', 'HOME']):
            return JSONResponse(
                content={
                    "error": "Invalid SKU format. Must start with ELEC, CLT, or HOME followed by 3 digits"
                },
                status_code=400
            )

        # Validate quantity and price
        if record['quantity'] <= 0:
            return JSONResponse(
                content={"error": "Quantity must be greater than 0"},
                status_code=400
            )
        if record['price'] <= 0:
            return JSONResponse(
                content={"error": "Price must be greater than 0"},
                status_code=400
            )

        with Session(engine) as session:
            query = insert(sales_transactions).values(**record)
            session.execute(query)
            session.commit()

        return JSONResponse(
            content={"message": "Record inserted successfully!"},
            status_code=200
        )
    except ValueError as e:
        return JSONResponse(
            content={"error": f"Invalid datetime format: {str(e)}"},
            status_code=400
        )
    except SQLAlchemyError as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
@app.post("/delete_record")
async def delete_record(
    transaction_id: int = Form(...)
):
    try:
        query = delete(sales_transactions).where(
            sales_transactions.c.transaction_id == transaction_id
        )
        
        with engine.begin() as connection:
            result = connection.execute(query)
        
        if result.rowcount == 0:
            return {
                "status": "failed",
                "message": f"Record with transaction_id {transaction_id} not found."
            }

        return {
            "status": "success",
            "message": "Record deleted successfully."
        }
    except SQLAlchemyError as e:
        return {
            "status": "failed",
            "error": str(e)
        }

@app.post("/get_record")
async def get_record(
    transaction_id: int = Form(...)
):
    try:
        query = select(sales_transactions).where(
            sales_transactions.c.transaction_id == transaction_id
        )
        
        with engine.connect() as connection:
            result = connection.execute(query).fetchone()
        
        if result is None:
            return {
                "status": "failed",
                "message": f"Record with transaction_id {transaction_id} not found."
            }

        record = dict(result._mapping)
        
        # Format datetime for JSON response
        record['transaction_datetime'] = record['transaction_datetime'].strftime("%Y-%m-%d %H:%M:%S")
        record['created_at'] = record['created_at'].strftime("%Y-%m-%d %H:%M:%S")

        return {
            "status": "success",
            "record": record
        }

    except SQLAlchemyError as e:
        return {
            "status": "failed",
            "error": str(e)
        }

# Additional utility endpoint to search by SKU and date range
@app.get("/search_records")
async def search_records(
    sku: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sale_channel: Optional[str] = None
):
    try:
        query = select(sales_transactions)
        
        # Add filters if parameters are provided
        if sku:
            query = query.where(sales_transactions.c.sku == sku)
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.where(sales_transactions.c.transaction_datetime >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.where(sales_transactions.c.transaction_datetime <= end_datetime)
        if sale_channel:
            query = query.where(sales_transactions.c.sale_channel == sale_channel)
        
        with engine.connect() as connection:
            results = connection.execute(query).fetchall()
            
        if not results:
            return {
                "status": "failed",
                "message": "No records found matching the criteria."
            }

        records = []
        for result in results:
            record = dict(result._mapping)
            record['transaction_datetime'] = record['transaction_datetime'].strftime("%Y-%m-%d %H:%M:%S")
            record['created_at'] = record['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            records.append(record)

        return {
            "status": "success",
            "records": records
        }

    except ValueError as e:
        return {
            "status": "failed",
            "error": f"Invalid date format: {str(e)}"
        }
    except SQLAlchemyError as e:
        return {
            "status": "failed",
            "error": str(e)
        }# from fastapi import FastAPI
# from fastapi.responses import HTMLResponse
# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
# import io
# import base64
# from datetime import datetime
# import numpy as np

@app.get("/analysis", response_class=HTMLResponse)
async def sales_analysis():
    # Read data from database
    query = "SELECT * FROM sales_transactions"
    df = pd.read_sql(query, engine)
    
    # Basic data preprocessing
    df['transaction_datetime'] = pd.to_datetime(df['transaction_datetime'])
    df['date'] = df['transaction_datetime'].dt.date
    df['hour'] = df['transaction_datetime'].dt.hour
    df['weekday'] = df['transaction_datetime'].dt.day_name()
    df['total_amount'] = df['quantity'] * df['price']
    
    # Generate plots
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            img { max-width: 800px; margin: 20px 0; }
            h2 { color: #333; }
            .stats-box { 
                background: #f5f5f5; 
                padding: 15px; 
                border-radius: 5px;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
    """
    
    # 1. Sales by Channel
    plt.figure(figsize=(12, 6))
    channel_sales = df.groupby('sale_channel')['total_amount'].sum().sort_values(ascending=False)
    channel_sales.plot(kind='bar', title='Total Sales by Channel')
    plt.xticks(rotation=45)
    plt.ylabel('Total Sales Amount')
    channel_sales_img = save_plot_to_base64()
    html_content += f'<h2>Sales by Channel</h2><img src="data:image/png;base64,{channel_sales_img}"><br>'
    
    # 2. Hourly Sales Distribution
    plt.figure(figsize=(12, 6))
    hourly_sales = df.groupby('hour')['total_amount'].sum()
    plt.plot(hourly_sales.index, hourly_sales.values)
    plt.title('Sales Distribution by Hour')
    plt.xlabel('Hour of Day')
    plt.ylabel('Total Sales Amount')
    hourly_sales_img = save_plot_to_base64()
    html_content += f'<h2>Sales Distribution by Hour</h2><img src="data:image/png;base64,{hourly_sales_img}"><br>'
    
    # 3. Top Products by Revenue
    plt.figure(figsize=(12, 6))
    top_products = df.groupby('sku')['total_amount'].sum().sort_values(ascending=False).head(10)
    top_products.plot(kind='bar', title='Top 10 Products by Revenue')
    plt.xticks(rotation=45)
    plt.ylabel('Total Revenue')
    top_products_img = save_plot_to_base64()
    html_content += f'<h2>Top 10 Products by Revenue</h2><img src="data:image/png;base64,{top_products_img}"><br>'
    
    # 4. Sales by Weekday
    plt.figure(figsize=(12, 6))
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_sales = df.groupby('weekday')['total_amount'].sum().reindex(weekday_order)
    weekday_sales.plot(kind='bar', title='Sales by Day of Week')
    plt.xticks(rotation=45)
    plt.ylabel('Total Sales Amount')
    weekday_sales_img = save_plot_to_base64()
    html_content += f'<h2>Sales by Day of Week</h2><img src="data:image/png;base64,{weekday_sales_img}"><br>'
    
    # 5. Key Statistics
    html_content += """
    <h2>Key Statistics</h2>
    <div class="stats-box">
    """
    total_sales = df['total_amount'].sum()
    total_transactions = len(df)
    avg_transaction = df['total_amount'].mean()
    
    stats_html = f"""
        <p><strong>Total Sales:</strong> ${total_sales:,.2f}</p>
        <p><strong>Total Transactions:</strong> {total_transactions:,}</p>
        <p><strong>Average Transaction Value:</strong> ${avg_transaction:.2f}</p>
        <p><strong>Most Popular Channel:</strong> {channel_sales.index[0]}</p>
        <p><strong>Best Selling SKU:</strong> {top_products.index[0]}</p>
    """
    html_content += stats_html + "</div>"
    
    # 6. Daily Sales Trend
    plt.figure(figsize=(12, 6))
    daily_sales = df.groupby('date')['total_amount'].sum()
    plt.plot(daily_sales.index, daily_sales.values)
    plt.title('Daily Sales Trend')
    plt.xticks(rotation=45)
    plt.ylabel('Total Sales Amount')
    daily_sales_img = save_plot_to_base64()
    html_content += f'<h2>Daily Sales Trend</h2><img src="data:image/png;base64,{daily_sales_img}"><br>'
    
    html_content += "</body></html>"
    return HTMLResponse(content=html_content)

def save_plot_to_base64():
    """Save the current plot to a base64 string."""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return img_base64