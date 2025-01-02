CREATE TABLE amazon_sale_report (
    index SERIAL PRIMARY KEY,
    "Order ID" VARCHAR(50),
    "Date" VARCHAR(50),
    "Status" VARCHAR(50),
    "Fulfillment" VARCHAR(50),
    "Sales Channel " VARCHAR(50),
    "ship-service-level" VARCHAR(50),
    "Style" VARCHAR(50),
    "SKU" VARCHAR(50),
    "Category" VARCHAR(50),
    "Size" VARCHAR(50),
    "ASIN" VARCHAR(50),
    "Courier Status" VARCHAR(50),
    "Qty" INT,
    "currency" VARCHAR(50),
    "Amount" FLOAT4,
    "ship-city" VARCHAR(50),
    "ship-state" VARCHAR(50),
    "ship-postal-code" FLOAT4,
    "ship-country" VARCHAR(50),
    "promotion-ids" VARCHAR(4096),
    "B2B" BOOLEAN,
    "fulfilled-by" VARCHAR(50),
    "Unnamed: 22" BOOLEAN
);

COPY amazon_sale_report
FROM '/data/import.csv'
DELIMITER ','
CSV HEADER;