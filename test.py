import pandas as pd
from fastapi import FastAPI, Form
from sqlalchemy import create_engine, MetaData, Table
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
import io
from fastapi.responses import HTMLResponse

connection_string = "postgresql+psycopg2://postgres:8643@localhost/SoftIQo"
engine = create_engine(connection_string)
query = "SELECT * FROM amazon_sale_report"
df = pd.read_sql(query, engine)

# print(df.head())         
# print(df.info())         
# print(df.describe())
# print(df.nunique())

df = df.fillna({'promotion_ids': 'None'})
df = df.dropna()
df = df.drop_duplicates()
df = df.drop(['index'], axis = 1)
df['Amount'] = df['Amount'].astype(float)
print(df.isnull().sum())

sales_by_category = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
sales_by_category.plot(kind='bar', figsize=(10, 6), title='Sales by Category')
plt.show()
sns.histplot(df['Amount'], bins=30, kde=True)
plt.title('Distribution of Order Amounts')
plt.show()
df['Date'] = pd.to_datetime(df['Date'])
orders_over_time = df.groupby('Date').size()
orders_over_time.plot(figsize=(10, 6), title='Orders Over Time')
plt.show()

top_products = df.groupby('SKU')['Amount'].sum().sort_values(ascending=False).head(10)
print(top_products)

print(df.dtypes)

numeric_df = df.select_dtypes(include=['float64', 'int64'])
print(numeric_df.columns)

# %%
# pip install -U scikit-learn scipy
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

# Compute the correlation matrix
correlation_matrix = df.corr()

# Plot the correlation matrix
plt.figure(figsize=(12, 10))
sns.heatmap(correlation_matrix, annot=False, cmap='coolwarm', fmt=".2f")
plt.title('Correlation Matrix')
plt.show()