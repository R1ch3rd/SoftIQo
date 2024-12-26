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


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


connection_string = "postgresql+psycopg2://postgres:8643@localhost/SoftIQo" #modify password
engine = create_engine(connection_string)
metadata = MetaData(schema="public")
metadata.reflect(bind=engine)
table_name = "amazon_sale_report"
selected_table = metadata.tables[f"public.{table_name}"]

@app.post("/insert_record")
async def insert_record(
    index: int = Form(...),
    order_id: str = Form(...),
    date: str = Form(...),
    status: str = Form(...),
    fulfilment: str = Form(...),
    sales_channel: str = Form(...),
    ship_service_level: str = Form(...),
    style: str = Form(...),
    sku: str = Form(...),
    category: str = Form(...),
    currency: str = Form(...),
    amount: float = Form(...),
    ship_city: str = Form(...),
    ship_state: str = Form(...),
    ship_postal_code: int = Form(...),
    ship_country: str = Form(...),
    promotion_ids: str = Form(None),
    b2b: bool = Form(False),
    fulfilled_by: str = Form(...),
    unnamed: bool = Form(False)
):
    try:
        
        record = {
        "index": index,
        "Order ID": order_id,
        "Date": date,
        "Status": status,
        "Fulfilment": fulfilment,
        "Sales Channel ": sales_channel,
        "ship-service-level": ship_service_level,
        "Style": style,
        "SKU": sku,
        "Category": category,
        "currency": currency,
        "Amount": amount,
        "ship-city": ship_city,
        "ship-state": ship_state,
        "ship-postal-code": ship_postal_code,
        "ship-country": ship_country,
        "promotion-ids": promotion_ids,
        "B2B": b2b,
        "fulfilled-by": fulfilled_by,
        "Unnamed: 22": unnamed
    }

        with Session(engine) as session:
            query = insert(selected_table).values(**record)
            session.execute(query)
            session.commit()

        return JSONResponse(content={"message": "Record inserted successfully!"}, status_code=200)
    except SQLAlchemyError as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/delete_record")
async def delete_record(order_id: str = Form(...), sku: str = Form(...)):
    try:
        query = delete(selected_table).where(
            selected_table.c["Order ID"] == order_id,
            selected_table.c["SKU"] == sku
        )
        
        
        with engine.begin() as connection:
            result = connection.execute(query)
        
        
        if result.rowcount == 0:  
            return {"status": "failed", "message": "Record not found."}

        return {"status": "success", "message": "Record deleted successfully."}
    except SQLAlchemyError as e:
        return {"status": "failed", "error": str(e)}
@app.post("/get_record")
async def get_record(order_id: str = Form(...), sku: str = Form(...)):
    try:
        query = select(selected_table).where(
            selected_table.c["Order ID"] == order_id,
            selected_table.c["SKU"] == sku
        )
        
        
        with engine.connect() as connection:
            result = connection.execute(query).fetchone()
        
        
        if result is None:  
            return {"status": "failed", "message": "Record not found."}

        record = dict(result._mapping)  # Use _mapping for Row objects

        return {"status": "success", "record": record}

    except SQLAlchemyError as e:
        return {"status": "failed", "error": str(e)}
    
# @app.get("/analysis", response_class=HTMLResponse)
# async def analysis():
#     query = "SELECT * FROM amazon_sale_report"
#     df = pd.read_sql(query, engine)
#     df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')

#     # Cleaning the data
#     df = df.fillna({'promotion_ids': 'None'})
#     df = df.dropna()
#     df = df.drop_duplicates()
#     if 'index' in df.columns:
#         df = df.drop(['index'], axis=1)
#     if 'Amount' in df.columns:
#         df['Amount'] = df['Amount'].astype(float)
#     df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

#     # Create sales by category plot
#     sales_by_category = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
#     sales_by_category_plot = io.BytesIO()
#     sales_by_category.plot(kind='bar', figsize=(10, 6), title='Sales by Category').get_figure().savefig(sales_by_category_plot, format='png')
#     sales_by_category_plot.seek(0)

#     # Create amount distribution plot
#     amount_distribution_plot = io.BytesIO()
#     sns.histplot(df['Amount'], bins=30, kde=True).get_figure().savefig(amount_distribution_plot, format='png')
#     amount_distribution_plot.seek(0)

#     # Create orders over time plot
#     orders_over_time = df.groupby('Date').size()
#     orders_over_time_plot = io.BytesIO()
#     orders_over_time.plot(figsize=(10, 6), title='Orders Over Time').get_figure().savefig(orders_over_time_plot, format='png')
#     orders_over_time_plot.seek(0)

#     # Correlation matrix plot
#     for col in df.select_dtypes(include=['object']).columns:
#         df[col] = pd.Categorical(df[col]).codes
#     correlation_matrix = df.corr()
#     correlation_matrix_plot = io.BytesIO()
#     sns.heatmap(correlation_matrix, annot=False, cmap='coolwarm', fmt=".2f").get_figure().savefig(correlation_matrix_plot, format='png')
#     correlation_matrix_plot.seek(0)

#     # HTML content with images
#     html_content = f"""
#     <!DOCTYPE html>
#     <html lang="en">
#     <head>
#         <meta charset="UTF-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#         <title>Analysis</title>
#     </head>
#     <body>
#         <h1>Data Analysis</h1>
#         <h2>Sales by Category</h2>
#         <img src="data:image/png;base64,{sales_by_category_plot.getvalue().decode('latin1')}" alt="Sales by Category">
#         <h2>Distribution of Order Amounts</h2>
#         <img src="data:image/png;base64,{amount_distribution_plot.getvalue().decode('latin1')}" alt="Amount Distribution">
#         <h2>Orders Over Time</h2>
#         <img src="data:image/png;base64,{orders_over_time_plot.getvalue().decode('latin1')}" alt="Orders Over Time">
#         <h2>Correlation Matrix</h2>
#         <img src="data:image/png;base64,{correlation_matrix_plot.getvalue().decode('latin1')}" alt="Correlation Matrix">
#     </body>
#     </html>
#     """
#     return HTMLResponse(content=html_content)