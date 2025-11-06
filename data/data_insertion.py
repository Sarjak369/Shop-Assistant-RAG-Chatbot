import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables (DB password from .env)
load_dotenv()

# Path to CSV
csv_file_path = './data/shop-product-catalog.csv'

# Read CSV into DataFrame
data = pd.read_csv(csv_file_path)

# Connect to MySQL
db_connect = mysql.connector.connect(
    host='localhost',
    user='root',
    password=os.getenv('DB_PASSWORD'),
    database='shopassistant'
)

# Create a cursor
cursor = db_connect.cursor()

# SQL insert query with placeholders
insert_query = """
INSERT INTO product_catalog
(ProductID, ProductName, ProductBrand, Gender, Price, Description, PrimaryColor)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

# Convert DataFrame into list of tuples
records = [
    (
        int(row["ProductID"]),
        str(row["ProductName"]),
        str(row["ProductBrand"]),
        str(row["Gender"]),
        int(row["Price"]),
        str(row["Description"]),
        str(row["PrimaryColor"])
    )
    for _, row in data.iterrows()
]

# Insert all rows at once
cursor.executemany(insert_query, records)

"""
Benefits of executemany():
- All inserts are batched together → much faster for large CSVs.
- cursor.rowcount now returns the total number of rows inserted.
"""

# Commit changes
db_connect.commit()

print(f"Successfully inserted {cursor.rowcount} rows into product_catalog")

# Close connection
cursor.close()
db_connect.close()
