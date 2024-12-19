from fastapi import FastAPI, Form,HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import create_engine, MetaData, Table, insert, delete
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


connection_string = "postgresql+psycopg2://postgres:password@localhost/SoftIQo" #modify password
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