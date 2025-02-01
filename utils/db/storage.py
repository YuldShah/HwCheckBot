from pymongo import MongoClient
from pymongo.server_api import ServerApi


class DatabaseManager:
    def __init__(self, uri, db_name):
        """Connects to MongoDB using the given URI and database name."""
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = self.client[db_name]
        
        # Ping the server to check the connection
        try:
            self.client.admin.command('ping')
            print("[MongoDB] Successfully Connected!")
        except Exception as e:
            print(f"[MongoDB] Connection Error: {e}")

    def insert_one(self, collection, data):
        """Insert a single document into a collection."""
        return self.db[collection].insert_one(data).inserted_id

    def fetch_one(self, collection, query):
        """Fetch a single document based on a query."""
        return self.db[collection].find_one(query)

    def fetch_all(self, collection, query={}):
        """Fetch all documents matching a query. Defaults to all documents."""
        return list(self.db[collection].find(query))

    def update_one(self, collection, query, new_values):
        """Update a single document."""
        return self.db[collection].update_one(query, {"$set": new_values})

    def delete_one(self, collection, query):
        """Delete a single document matching a query."""
        return self.db[collection].delete_one(query)

    def count_documents(self, collection, query={}):
        """Count the number of documents matching a query."""
        return self.db[collection].count_documents(query)

    def create_index(self, collection, field, unique=False):
        """Create an index on a field."""
        return self.db[collection].create_index([(field, 1)], unique=unique)

    def __del__(self):
        self.client.close()