from pymongo import MongoClient

try:
    client = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    print("MongoDB connection successful!")

    db = client["smartlab"]

    print("Database selected:", db.name)

except Exception as e:
    print("MongoDB connection failed!")
    print(e)