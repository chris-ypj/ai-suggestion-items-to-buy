# author : chris-jyp

import random
import sys
import os
from datetime import datetime, timedelta
from database.databaseconnection import MongoDBClient
import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

class FunctionAI:

    def __init__(self):
        self.client = MongoDBClient()

        self.usernames = [
            # "Lucy",       # from "Lucy@gmail.com"
            # "Jim",        # from "jim@gmail.com"
            # "Abraham",    # from "Abraham@gmail.com"
            # "Alexis",     # from "Alexis@gmail.com"
            # "Aliyah"      # from "Aliyah@gmail.com"
            "chris",      # from "chris@gmail.com"
        ]

        # --- MANDATORY ITEMS (must appear in every receipt) ---
        # Now only include Whole Milk, Chicken, and Water as required items.
        self.MANDATORY_ITEMS = [
            {
                "name": "Whole Milk",
                "price_per_unit": 2.5,
                "capacity": 1,
                "capacity_unit": "L",
                "category": "Dairy"
            },
            {
                "name": "Chicken",
                "price_per_unit": 7.0,  # per kg (example)
                "capacity": 1,
                "capacity_unit": "kg",
                "category": "Meat"
            },
            {
                "name": "Water",
                "price_per_unit": 1.0,  # per litre (example)
                "capacity": 1,
                "capacity_unit": "L",
                "category": "Beverage"
            }
        ]

        # --- OPTIONAL DAILY CONSUMPTION ITEMS ---
        self.OPTIONAL_ITEMS = [
            {"name": "Carrots", "price_per_unit": 1.0, "capacity": 0.5, "capacity_unit": "kg", "category": "Vegetables"},
            {"name": "Apples", "price_per_unit": 0.5, "capacity": 4, "capacity_unit": "pcs", "category": "Fruits"},
            {"name": "Bananas", "price_per_unit": 0.3, "capacity": 6, "capacity_unit": "pcs", "category": "Fruits"},
            {"name": "Fish", "price_per_unit": 9.0, "capacity": 1, "capacity_unit": "kg", "category": "Seafood"},
            {"name": "Beef", "price_per_unit": 12.0, "capacity": 1, "capacity_unit": "kg", "category": "Meat"},
            {"name": "Cheese", "price_per_unit": 3.0, "capacity": 0.25, "capacity_unit": "kg", "category": "Dairy"},
            {"name": "Tomato", "price_per_unit": 0.8, "capacity": 0.5, "capacity_unit": "kg", "category": "Vegetables"},
            {"name": "Onion", "price_per_unit": 0.5, "capacity": 0.5, "capacity_unit": "kg", "category": "Vegetables"},
            {"name": "Butter", "price_per_unit": 2.5, "capacity": 0.25, "capacity_unit": "kg", "category": "Dairy"},
            {"name": "Yogurt", "price_per_unit": 1.5, "capacity": 0.5, "capacity_unit": "L", "category": "Dairy"},
            {"name": "Cereal", "price_per_unit": 3.0, "capacity": 1, "capacity_unit": "box", "category": "Grocery"},
            {"name": "Rice", "price_per_unit": 2.0, "capacity": 1, "capacity_unit": "kg", "category": "Grains"}
        ]


    def random_date_in_2025(self):
        """
        Generate a random datetime in the year 2025.
        """
        nz_tz = ZoneInfo("Pacific/Auckland")
        start = datetime(2025, 1, 1, tzinfo=nz_tz)
        end = datetime(2025, 4, 16, tzinfo=nz_tz)
        diff = end - start
        random_days = random.randint(0, diff.days)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        random_time = start + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
        return random_time


    def generate_purchase_date_by_status(self, status: str):
        """
        Generate a purchase_date based on the given status.
          - For "recent", return a date within the last 7 days.
          - For "expired", return an older date (e.g. 30 to 90 days ago).
          - Otherwise, fallback to random date in 2025.
        """
        nz_tz = ZoneInfo("Pacific/Auckland")
        now_nz = datetime.now(nz_tz)
        if status == "recent":
            start = now_nz - timedelta(days=7)
            random_seconds = random.randint(0, 7 * 24 * 3600)
            return start + timedelta(seconds=random_seconds)
        elif status == "expired":
            days_ago = random.randint(30, 90)
            random_seconds = random.randint(0, 24 * 3600)
            return now_nz - timedelta(days=days_ago, seconds=random_seconds)
        elif status == "today":
            today_start = now_nz.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1) - timedelta(microseconds=1)
            random_seconds = random.randint(0, int((today_end - today_start).total_seconds()))
            return today_start + timedelta(seconds=random_seconds)
        else:
            return self.random_date_in_2025()

    def generate_items_list(self):
        """
        Generate a list of at least 10 items for a receipt.
        This list includes the 3 mandatory items (Whole Milk, Chicken, Water) and
        7 random items picked from OPTIONAL_ITEMS.
        Each item document includes the required fields plus 'start_date' and 'end_date'.
        """
        final_items = []

        # Add mandatory items with random quantity (for demonstration purposes).
        for m_item in self.MANDATORY_ITEMS:
            quantity = random.randint(1, 3)
            capacity = m_item["capacity"]
            capacity_unit = m_item["capacity_unit"]
            total_price = round(quantity * m_item["price_per_unit"], 2)
            final_items.append({
                "name": m_item["name"],
                "quantity": quantity,
                "price_per_unit": m_item["price_per_unit"],
                "total_price": total_price,
                "capacity": capacity,
                "capacity_unit": capacity_unit,
                "category": m_item["category"],
                "start_date": None,  # to be assigned later
                "end_date": None  # optionally assigned later
            })

        # Choose 7 random items from OPTIONAL_ITEMS.
        random_items = random.sample(self.OPTIONAL_ITEMS, 7)
        for r_item in random_items:
            quantity = random.randint(1, 3)
            capacity = r_item["capacity"]
            capacity_unit = r_item["capacity_unit"]
            total_price = round(quantity * r_item["price_per_unit"], 2)
            final_items.append({
                "name": r_item["name"],
                "quantity": quantity,
                "price_per_unit": r_item["price_per_unit"],
                "total_price": total_price,
                "capacity": capacity,
                "capacity_unit": capacity_unit,
                "category": r_item["category"],
                "start_date": None,
                "end_date": None
            })

        return final_items


    def build_receipt(self,username, status="recent"):
        """
        Build a receipt document for insertion into MongoDB.
        purchase_dt is the purchase_date for the receipt.
        Each item will get a start_date (purchase_dt + 1 day) and an optional end_date.
        """
        nz_tz = ZoneInfo("Pacific/Auckland")
        # Localize purchase_dt with New Zealand timezone
        purchase_dt = self.generate_purchase_date_by_status(status).astimezone(nz_tz)
        purchase_dt = purchase_dt.replace(tzinfo=nz_tz)
        items = self.generate_items_list()
        subtotal = sum(item["total_price"] for item in items)
        tax = round(subtotal * 0.15, 2)  # example: 15% tax
        total = round(subtotal + tax, 2)
        # For each item, assign start_date and optionally an end_date.
        for item in items:
            start_dt = purchase_dt + timedelta(days=1)
            start_dt = start_dt.astimezone(nz_tz)
            item["start_date"] = start_dt  # stored as ISO string
            if random.random() < 0.5:
                # Leave end_date as None
                item["end_date"] = None
            else:
                # Set end_date 3-7 days after start_date
                random_offset = random.randint(3, 7)
                end_dt = start_dt + timedelta(days=random_offset)
                end_dt = end_dt.astimezone(nz_tz)
                # If the computed end_date is in the future, reset it to None.
                now = datetime.now(nz_tz)
                if end_dt > now:
                    item["end_date"] = None
                else:
                    item["end_date"] = end_dt
        # Generate a unique receipt number
        receipt_number = "SM-{:%Y%m%d-%H%M}-{:04d}".format(purchase_dt, random.randint(1, 9999))

        return {
            "store_name": "SuperMart",
            "store_location": "123 Queen Street, Auckland",
            "purchase_date": purchase_dt,
            "items": items,
            "subtotal": round(subtotal, 2),
            "tax": tax,
            "total": total,
            "payment_method": "Credit Card",
            "receipt_number": receipt_number,
            "user_name": username,
            "image_url": ""
        }


    def insert_receipt_to_db(self, username="Lucy", status="recent",num=5):
        try:
            # print("Inserting receipts into the database...")
            for _ in range(num):
                receipt_doc = self.build_receipt(username, status)
                print("receipt_doc", receipt_doc)
                # Insert the receipt document into the MongoDB collection
                result = self.client.insert_one("receipts",receipt_doc)
                if result:
                    logging.info("Receipt inserted successfully.")
                else:
                    logging.error("Failed to insert receipt.")
        except Exception as e:
            logging.error(f"Error inserting receipt: {e}")



if __name__ == "__main__":
    ai = FunctionAI()
    usernames = [
        "lucy",       # from "lucy@gmail.com"
        "chris",        # from "chris@gmail.com"
        "jim",    # from "jim@gmail.com"
        "tony",  # from "tony@gmail.com"
        "adam",  # from "adam@gmail.com"
    ]
    # For expired receipts:
    for user in usernames:
        print(user)
        ai.insert_receipt_to_db(username=user, status="recent",num=20)
        ai.insert_receipt_to_db(username=user, status="expired",num=20)
        ai.insert_receipt_to_db(username=user, status="today",num=10)