# author : chris-jyp
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from config.config import settings

class MongoDBClient:
    def __init__(self):
        # MongoDB Atlas connection string with SRV protocol.
        self.uri = settings.mongodb_uri
        # Create a MongoClient instance
        self.client = MongoClient(self.uri )
        # Choose a database (replace 'YourDatabaseName' with your actual database name)
        self.db = self.client[settings.mongodb_db]
        self.items_collection = self.db.get_collection("items")
        self.shopping_collection = self.db.get_collection("shoppinglists")
        self.capacity_units_collection = self.db.get_collection("capacityunit")
        self.receipts_collection = self.db.get_collection("receipts")

    def db_close(self, connection_string: str) -> None:
        # Close the connection when done.
        self.client.close()

    def get_collection(self, collection_name: str):
        return self.db[collection_name]

    def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.get_collection(collection_name).find_one(query)

    def find(self, collection_name: str, query: Dict[str, Any], projection: Optional[Dict[str, Any]] = None) -> List[
        Dict[str, Any]]:
        return list(self.get_collection(collection_name).find(query, projection))

    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Any:
        result = self.get_collection(collection_name).insert_one(document)
        return result.inserted_id

    def update_one(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any],
                   upsert: bool = False) -> int:
        result = self.get_collection(collection_name).update_one(query, update, upsert=upsert)
        return result.modified_count

    def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        result = self.get_collection(collection_name).delete_one(query)
        return result.deleted_count

    def close(self) -> None:
        self.client.close()


# Example usage:
if __name__ == "__main__":
    # Find one document
    client = MongoDBClient()
    doc = client.find_one("receipt", {"user_name": "Lucy"})
    client.close()