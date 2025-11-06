import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# Init embedding model
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

# Init Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("ai-shop-assistant-chatbot")

# Init vectorstore
vectorstore = PineconeVectorStore(
    index=index,
    embedding=embedding_model,
    text_key="Description"
)
