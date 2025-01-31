from pymongo import MongoClient


class DatabaseManager:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def insert_one(self, collection, data):
        """Insert a single document into a collection."""
        return self.db[collection].insert_one(data).inserted_id

    def insert_many(self, collection, data_list):
        """Insert multiple documents into a collection."""
        return self.db[collection].insert_many(data_list).inserted_ids

    def fetch_one(self, collection, query):
        """Fetch a single document based on a query."""
        return self.db[collection].find_one(query)

    def fetch_all(self, collection, query={}):
        """Fetch all documents matching a query. Defaults to all documents."""
        return list(self.db[collection].find(query))

    def update_one(self, collection, query, new_values):
        """Update a single document."""
        return self.db[collection].update_one(query, {"$set": new_values})

    def update_many(self, collection, query, new_values):
        """Update multiple documents."""
        return self.db[collection].update_many(query, {"$set": new_values})

    def delete_one(self, collection, query):
        """Delete a single document matching a query."""
        return self.db[collection].delete_one(query)

    def delete_many(self, collection, query):
        """Delete multiple documents matching a query."""
        return self.db[collection].delete_many(query)

    def count_documents(self, collection, query={}):
        """Count the number of documents matching a query."""
        return self.db[collection].count_documents(query)

    def create_index(self, collection, field, unique=False):
        """Create an index on a field."""
        return self.db[collection].create_index([(field, 1)], unique=unique)

    def drop_collection(self, collection):
        """Drop a collection from the database."""
        self.db[collection].drop()

    def __del__(self):
        self.client.close()


# Example collections based on your SQLite structure:
# users: { _id, userid, fullname, username, regdate, banned }
# exams: { _id, code, title, about, num_questions, correct, running }
# submissions: { _id, exid, userid, date, corr }
# channel: { _id, chid, title, username }
