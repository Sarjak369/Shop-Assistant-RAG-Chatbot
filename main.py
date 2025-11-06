from fastapi import FastAPI

app = FastAPI(title="AI Shop Assistant")


@app.get("/")
async def root():
    return {"message": "Welcome to AI Shop Assistent Chatbot!"}


def main():
    print("Hello from ai-shopassistant!")


if __name__ == "__main__":
    main()
