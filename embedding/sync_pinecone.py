import os
import time
import pinecone
import mysql.connector
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from tqdm.auto import tqdm
import pandas as pd
from langchain.schema import Document


# Load environment variables

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY missing in .env file")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY missing in .env file")


# Initialize a client object
pc = Pinecone(api_key=PINECONE_API_KEY)

spec = ServerlessSpec(
    cloud='aws', region='us-east-1'
)

# Now that we are connected to Pinecone, the next step is to store data in an index.
# Create an index
# In Pinecone, we use dense indexes for semantic search and sparse indexes for lexical search.

index_name = 'ai-shop-assistant-chatbot'

# Every index in our Pinecone index will be unique. So, we need to check if this index exists or not.
# Fetching and storing all the existing indexes from our pinecone client
existing_indexes = [index_info['name'] for index_info in pc.list_indexes()]

# Check if index exists, else create
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI text-embedding-3-small → returns 1536 dimensions
        metric='cosine',  # Best for semantic product search
        spec=spec
    )
    # After creating the index, we cannot just directly upload the data. It's better to give some relaxation time to our index.

    while not pc.describe_index(index_name).status['ready']:
        print(f"Waiting for the index {index_name} to be ready...")
        # if index is not ready then we give some 5 secs of time to make it ready
        time.sleep(5)


# Connect to the index
index = pc.Index(index_name)
time.sleep(2)

# Connect to MySQL
db_connect = mysql.connector.connect(
    host='localhost',
    user='root',
    password=os.getenv('DB_PASSWORD'),
    database='shopassistant'
)

# Create a cursor
cursor = db_connect.cursor()


# Create embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)


# Read data from MySQL in order to fetch product_catalog table data

def fetch_data():

    # create a dictionary cursor
    cursor = db_connect.cursor(dictionary=True)

    # run SQL query
    query = "SELECT * FROM product_catalog"
    cursor.execute(query)

    # fetch all rows as list of dicts
    data = cursor.fetchall()

    # convert directly to DataFrame - pandas automatically uses dict keys as columns
    df = pd.DataFrame(data)

    return df


"""
Why use dictionary=True?

- Normally cursor.fetchall() gives you a list of tuples → you then need cursor.description to map column names.

- With dictionary=True, MySQL Connector automatically returns each row as a Python dict → Pandas can directly convert it into a DataFrame.

- So we skip the cursor.description step entirely
"""


def sync_with_pinecone(data):
    """
    This function:

    Takes your product catalog DataFrame.
    Breaks it into small batches.
    Creates embeddings (numerical vectors) for each product.
    Attaches useful metadata.
    Uploads everything to Pinecone for fast semantic search.

    So after running sync_with_pinecone(df), your entire MySQL product catalog lives inside Pinecone as searchable vectors.

    """
    batch_size = 100
    # If you have 10,000 products, you don’t want to embed them all at once (too heavy).
    # Instead, it processes them in batches of 100 rows. So, total_batches = number of chunks we’ll process.
    # Defining a batch_size is crucial for performance. Instead of sending 1 record at a time to Pinecone (which would be incredibly slow for a large dataset), we group them into batches.
    # And this significantly reduces the numbers of API calls.

    # this help us to track the progress
    total_batches = (len(data)+batch_size - 1) // batch_size

    # Looping through the DataFrame in chunks (0–100, 100–200, etc.). Using tqdm to show a nice progress bar and batch is just a small slice of our full DataFrame.
    for i in tqdm(range(0, len(data), batch_size), desc="Processing Batches", unit='batch', total=total_batches):
        # This loop iterates through our data and extracts the batch of record at a time, using pandas iloc function.
        i_end = min(len(data), i + batch_size)
        batch = data.iloc[i:i_end]

        # Generate unique IDs -> Each product gets a unique string ID (using ProductID from MySQL).
        ids = [str(row['ProductID']) for _, row in batch.iterrows()]

        # combine text fields into one string for embedding
        texts = [
            f"{row['Description']} {row['ProductName']} {row['ProductBrand']} {row['Gender']} {row['Price']} {row['PrimaryColor']}"
            for _, row in batch.iterrows()
        ]  # Builds a single text blob for each product (all important fields concatenated).
        # Example for a Nike shoe: "Lightweight running shoes Presto Fly Nike Women 10999 Pink"
        # This is what gets sent to the embedding model.

        # Create embeddings for texts
        embeds = embedding_model.embed_documents(texts)
        """
        Calls OpenAI’s embedding model (text-embedding-3-small).
        Converts each product’s text into a 1536-dimensional vector.
        These vectors let Pinecone understand similarity between products.
        """

        # Prepare metadata
        metadata = [
            {
                'ProductName': row['ProductName'],
                'ProductBrand': row['ProductBrand'],
                'Gender': row['Gender'],
                'Price': row['Price'],
                'PrimaryColor': row['PrimaryColor'],
                'Description': row['Description'],
            }
            for _, row in batch.iterrows()
        ]  # Metadata = key–value info stored alongside the vector.
        # Useful for filtering in queries (e.g., “only Nike products”, “only Men’s shoes”).

        # Upsert vectors into Pinecone
        # Progress bar for vectors - Shows progress for each vector batch being uploaded.
        with tqdm(total=len(ids), desc="Upserting Vectors", unit='vector') as upsert_vector:
            """
            Sends the batch into Pinecone.
            upsert = “insert or update if exists”.
            Each vector in Pinecone = (id, embedding, metadata).
            """
            # zip(ids, embeds, metadata) creates a zip object (an iterator), not a list.
            # Pinecone’s typing hints (List[Vector]) expect a list of tuples like
            vectors = list(zip(ids, embeds, metadata))
            index.upsert(vectors=vectors)
            upsert_vector.update(len(ids))


def main():
    data = fetch_data()
    sync_with_pinecone(data)


if __name__ == "__main__":
    main()


cursor.close()
db_connect.close()
