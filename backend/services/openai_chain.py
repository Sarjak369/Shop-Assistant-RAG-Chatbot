import os
from dotenv import load_dotenv
from backend.services.vectorstore import vectorstore
from langchain_openai import ChatOpenAI

load_dotenv()

system_message = (
    "You are a helpful assistant that helps users find information about products in a shop."
    "You can answer questions about product details, availability, and recommendations based on user preferences."
    "If you don't know the answer, you should say 'I don't know'. "
)


def get_relevant_context(query):
    results = vectorstore.similarity_search(query, k=2)
    if results:
        metadata = results[0].metadata
        return (
            f"Product Name: {metadata.get('ProductName')}\n"
            f"Brand: {metadata.get('ProductBrand')}\n"
            f"Price: {metadata.get('Price')}\n"
            f"Gender: {metadata.get('Gender')}\n"
            f"Color: {metadata.get('PrimaryColor')}\n"
            f"Description: {results[0].page_content}"
        )
    return "No relevant search found."


def generate_response(query, history):
    model = ChatOpenAI(model='gpt-4o')

    history.append(f"User: {query}")
    context = get_relevant_context(query)

    prompt = f"{system_message}\n\n" + \
        "\n".join(history) + f"\n\nContext:\n{context}\n\nAssistant:"

    response = model.invoke(prompt).content

    history.append(f"Assistant: {response}")

    return {
        "response": response,
        "history": history
    }
