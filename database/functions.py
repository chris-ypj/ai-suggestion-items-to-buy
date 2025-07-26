# author : chris-jyp

from database.databaseconnection import MongoDBClient
from datetime import datetime, timezone,timedelta
from config.config import NZ_TZ

class FunctionAI:
    """
    FunctionAI class to handle MongoDB operations.
    It initializes the MongoDB client and provides methods to interact with the database.
    """

    def __init__(self):
        self.client = MongoDBClient()

    def get_items_for_user(self,username: str) -> list:
        """Retrieve all item documents for a given user."""
        user =  list(self.client.items_collection.find({"user_name": username}))
        return user


    def get_or_create_shopping_list(self,username: str) -> dict:
        """
        Retrieve today's shopping list for the given user.
        If it doesn't exist, create one.
        """
        today = datetime.now(timezone.utc)
        seven_days_ago = today - timedelta(days=14)
        shopping_list = self.client.shopping_collection.find_one({
            "userName": username,
            "trolley_status": "inProgress",
            "createdAt": {"$gte": seven_days_ago}
        })
        if shopping_list is None:
            new_list = {
                "userName": username,
                "items": [],
                "totalItems": 0,
                "estimatedTotal": 0.0,
                "trolley_status": "inProgress",
                "createdAt": datetime.now(NZ_TZ),
                "updatedAt": datetime.now(NZ_TZ)
            }
            self.client.shopping_collection.insert_one(new_list)
            shopping_list = self.client.shopping_collection.find_one({
                "userName": username,
                "createdAt": {"$gte": datetime(today.year, today.month, today.day)}
            })
        else:
            # This list comprehension retains only items with "source" equal to "ai"
            shopping_list["items"] = [
                item for item in shopping_list.get("items", [])
                if item.get("source") == "ai"
            ]
        return shopping_list


    def get_conversion_factor(self,unit_symbol: str) -> float:
        """
        Retrieve the conversion factor for a given capacity unit (e.g., 'L') from the capacity_units collection.
        If not found, default to 1.
        """
        doc = self.client.capacity_units_collection.find_one({"symbol": unit_symbol})
        return doc.get("conversion_factor", 1) if doc else 1