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

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


connection_string = "postgresql+psycopg2://postgres:pass@localhost/SoftIQo" #modify password
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
    
@app.get("/analysis", response_class=HTMLResponse)
async def analysis():
    query = "SELECT * FROM amazon_sale_report"
    df = pd.read_sql(query, engine)
    df = df.fillna({'promotion_ids': 'None'})
    df = df.dropna()
    df = df.drop_duplicates()
    df = df.drop(['index'], axis=1, errors='ignore')
    df['Amount'] = df['Amount'].astype(float)
    
    # Generate plots
    html_content = "<html><body>"

    # Sales by Category
    sales_by_category = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
    plt.figure(figsize=(10, 6))
    sales_by_category.plot(kind='bar', title='Sales by Category')
    sales_by_category_img = save_plot_to_base64()
    html_content += f'<h2>Sales by Category</h2><img src="data:image/png;base64,{sales_by_category_img}"><br>'
    
    # Distribution of Order Amounts
    plt.figure(figsize=(10, 6))
    sns.histplot(df['Amount'], bins=30, kde=True)
    plt.title('Distribution of Order Amounts')
    dist_img = save_plot_to_base64()
    html_content += f'<h2>Distribution of Order Amounts</h2><img src="data:image/png;base64,{dist_img}"><br>'
    
    # Orders Over Time
    df['Date'] = pd.to_datetime(df['Date'])
    orders_over_time = df.groupby('Date').size()
    plt.figure(figsize=(10, 6))
    orders_over_time.plot(title='Orders Over Time')
    orders_over_time_img = save_plot_to_base64()
    html_content += f'<h2>Orders Over Time</h2><img src="data:image/png;base64,{orders_over_time_img}"><br>'
    
    # Top Products
    top_products = df.groupby('SKU')['Amount'].sum().sort_values(ascending=False).head(10)
    html_content += f'<h2>Top 10 Products by Amount</h2><pre>{top_products.to_string()}</pre><br>'
    
    # Handle boolean columns
    boolean_columns = ['B2B', 'Unnamed: 22']
    for col in boolean_columns:
        if col in df.columns:
            df[col] = df[col].astype(int)

    # Handle categorical columns with label encoding
    categorical_columns = df.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        df[col] = df[col].fillna('Unknown')  # Fill missing values
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])

    # Handle missing numerical values
    numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numerical_columns:
        df[col] = df[col].fillna(0)  # Replace NaNs with 0

    # Correlation Matrix
    correlation_matrix = df.corr()
    plt.figure(figsize=(12, 10))
    sns.heatmap(correlation_matrix, annot=False, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Matrix')
    correlation_img = save_plot_to_base64()
    html_content += f'<h2>Correlation Matrix</h2><img src="data:image/png;base64,{correlation_img}"><br>'
    
    html_content += "</body></html>"
    return HTMLResponse(content=html_content)


def save_plot_to_base64():
    """Save the current plot to a base64 string."""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return img_base64