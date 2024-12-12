# Automated Data pipeline to insert and delete records from a database

## About the Repository

This repository contains a FastAPI backend and an HTML frontend for managing an Amazon sale report database. Users can:

1. Insert records into the database with all required fields.
2. Delete records from the database based on `Order ID` and `SKU`.

The repository demonstrates the use of FastAPI for building RESTful APIs and a simple HTML form interface for interacting with the database.

---

## Getting Started

Follow these steps to set up the project on your local system.

### Prerequisites

1. **Python**: Ensure Python 3.8 or higher is installed.
2. **PostgreSQL**: A PostgreSQL database must be set up and running.
3. **Virtual Environment**: It is recommended to use a virtual environment to manage dependencies.

---

### Steps to Run the Project

#### 1. Clone the Repository

```bash
git clone <repository_url>
cd <repository_name>
```

#### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Set Up the Database

1. Create a PostgreSQL database.
2. Update the database connection string in the `main.py` file:

```python
connection_string = "postgresql+psycopg2://<username>:<password>@<host>/<database_name>"
```

3. Ensure the database schema and table (`amazon_sale_report`) exist with appropriate columns.

#### 5. Run the Backend

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Access the API documentation at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### 6. Serve the HTML Frontend

Open the `index.html` file in any modern browser or use a simple HTTP server:

```bash
python -m http.server
```

Then, navigate to `http://127.0.0.1:8000` in your browser.

---

### Features

#### **Insert Record**
- Allows inserting a record with all 24 columns.
- Input validation is handled by FastAPI.

#### **Delete Record**
- Deletes records based on `Order ID` and `SKU`.
- Provides meaningful feedback if the record is not found.
