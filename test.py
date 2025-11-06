from pinecone import Pinecone
import os
from dotenv import load_dotenv
load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
idx = pc.Index("ai-shop-assistant-chatbot")
print(idx.describe_index_stats())   # should show total_vector_count > 0


# from pinecone import Pinecone
# import os
# from dotenv import load_dotenv

# load_dotenv()
# pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# index_name = "ai-shop-assistant-chatbot"
# index = pc.Index(index_name)

# # Delete all vectors in the default namespace
# index.delete(delete_all=True)

# print("All vectors deleted, index is now empty.")
