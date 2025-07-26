# author : chris-jyp
import random
import pprint
from datetime import datetime, timedelta, timezone
from database.databaseconnection import MongoDBClient

class GenerateItems:
    """
    This class queries receipt documents from the receipts collection,
    simulates missing usage dates (start_date, end_date, predicted_consumed_date)
    for each receipt item, and then builds and inserts corresponding item documents
    into the items collection.
    """

    def __init__(self):
        self.client = MongoDBClient()
        self.receipts_collection = self.client.receipts_collection
        self.items_collection = self.client.items_collection
        self.usernames = [
            # "Lucy",  # from "Lucy@gmail.com"
            # "Jim",  # from "jim@gmail.com"
            # "Abraham",  # from "Abraham@gmail.com"
            # "Alexis",  # from "Alexis@gmail.com"
            # "Aliyah"  # from "Aliyah@gmail.com"
            "chris",  # from "chris@gmail.com"
        ]

    def query_receipts_by_user(self, username: str,num_receipts: int = 10):
        """
        Query receipts collection for documents corresponding to a given user.
        """
        try:
            receipts = list(self.receipts_collection.find({"user_name": username}, {"_id": 0}).limit(num_receipts))
            print(f"Found {len(receipts)} receipt documents for user: {username}")
            receipt_list = []
            for receipt in receipts:
                receipt.pop("_id", None)
                receipt_list.append(receipt)
            print(f"Found receipt : {receipt_list}")
            return receipt_list
        except Exception as e:
            print(f"Error querying receipts for user {username}: {e}")
            return []

    def query_sample_receipts(self):
        """
        Query the receipts collection to retrieve all receipt documents.
        Returns a list of receipt documents.
        """
        try:
            receipts = list(self.receipts_collection.find({}))
            print(f"Found {len(receipts)} receipt documents.")
            return receipts
        except Exception as e:
            print(f"Error querying receipts: {e}")
            return []

    def random_start_date_from_purchase(self, purchase_date):
        """
        Generate a random start_date based on the receipt's purchase_date.
        For example, start_date = purchase_date + 1 to 2 days.
        """
        return purchase_date + timedelta(days=random.randint(1, 2))

    def random_end_date_from_start(self, start_date):
        """
        Randomly generate an end_date. With a 70% chance, return start_date + 3 to 7 days;
        otherwise, return None (simulate ongoing consumption).
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")  # Adjust format as needed

        if random.random() < 0.7:
            return start_date + timedelta(days=random.randint(3, 7))
        return None

    def compute_predicted_consumed_date(self, start_date, expiry_date):
        """
        Compute the midpoint between start_date and expiry_date.
        This ensures predicted_consumed_date is later than start_date and earlier than expiry_date.
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")  # Adjust format as needed
        if isinstance(expiry_date, str):
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%dT%H:%M:%S")  # Adjust format as needed

        if start_date and expiry_date and start_date < expiry_date:
            return start_date + (expiry_date - start_date) / 2
        return None

    def simulate_item_usage_dates(self, receipt):
        """
        For each item in the receipt, simulate missing usage fields:
         - If start_date is missing, generate one based on the receipt's purchase_date.
         - If end_date is missing, randomly assign one.
         - If predicted_consumed_date is missing, compute it as the midpoint between start_date and expiry_date.
        For receipts missing expiry_date, a fallback is computed as purchase_date + 15 days.
        """
        purchase_date = receipt.get("purchase_date")
        if isinstance(purchase_date, str):
            purchase_date = datetime.strptime(purchase_date, "%Y-%m-%dT%H:%M:%S")  # Adjust format as needed
        # If expiry_date is missing, use a fallback: purchase_date + 15 days.
        expiry_date = receipt.get("expiry_date") or (purchase_date + timedelta(days=15))
        # Save the computed expiry_date back into the receipt so later mapping works.
        receipt["expiry_date"] = expiry_date

        for item in receipt.get("items", []):
            # Generate start_date if missing.
            if not item.get("start_date"):
                item["start_date"] = self.random_start_date_from_purchase(purchase_date)
            # Generate end_date randomly if missing.
            if "end_date" not in item or item["end_date"] is None:
                item["end_date"] = self.random_end_date_from_start(item["start_date"])
            # Compute predicted_consumed_date if missing.
            if not item.get("predicted_consumed_date"):
                item["predicted_consumed_date"] = self.compute_predicted_consumed_date(item["start_date"], expiry_date)
        return receipt


    def build_item_from_receipt(self, receipt, r_item):
        """
        Assemble an item document for the items collection from a receipt and one receipt item.
        Sets status based on the following conditions:
          - If no start_date exists and expiry_date is after now, status = "not opened".
            If expiry_date is not after now, status = "expired".
          - If start_date exists and no end_date is available:
              * If start_date <= now and expiry_date > now then status = "consuming".
              * If expiry_date is in the past, status = "expired".
          - If start_date exists and an end_date exists, and end_date <= now, then status = "consumed".
        """
        now = datetime.now()

        # Convert purchase_date, start_date, end_date, expiry_date if they are strings
        purchase_date = receipt.get("purchase_date")
        if isinstance(purchase_date, str):
            purchase_date = datetime.strptime(purchase_date, "%Y-%m-%dT%H:%M:%S")

        start_date = r_item.get("start_date")
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")

        end_date = r_item.get("end_date")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S")

        expiry_date = receipt.get("expiry_date")
        if isinstance(expiry_date, str):
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%dT%H:%M:%S")

        # Determine status based on the provided conditions
        if not start_date:
            if expiry_date > now:
                status = "not opened"
            else:
                status = "expired"
        else:
            if end_date is None:
                if start_date <= now and expiry_date > now:
                    status = "consuming"
                elif expiry_date <= now:
                    status = "expired"
                else:
                    status = "consuming"
            else:
                if end_date <= now:
                    status = "consumed"
                else:
                    # In case end_date exists but is in the future, you may consider "consuming"
                    status = "consuming"

        price = float(r_item.get("total_price", 0))
        item_doc = {
            "user_name": receipt.get("user_name"),
            "name": r_item.get("name"),
            "category_name": r_item.get("category"),
            "receipt_number": receipt.get("receipt_number"),
            "status": status,
            "purchase_date": purchase_date,
            "expiry_date": expiry_date,
            "price": price,
            "location": "Fridge",
            "quantity": r_item.get("quantity"),
            "capacity": r_item.get("capacity"),
            "capacity_unit": r_item.get("capacity_unit"),
            "creat_date": purchase_date,
            "start_date": start_date,
            "end_date": end_date,
            "predicted_consumed_date": r_item.get("predicted_consumed_date")
        }
        return item_doc


    def process_receipts_to_items(self,username="Lucy",num_receipts=10):
        """
        Query receipts, simulate missing usage fields (start_date, end_date, predicted_consumed_date),
        convert each receipt's items into item documents, and insert these documents into the items collection.
        Also returns the simulated receipt documents.
        """
        all_items = []

        print("Processing receipts for user:", username)
        user_receipts = self.query_receipts_by_user(username, num_receipts=num_receipts)

        items_to_insert = []
        for receipt in user_receipts:
            simulated = self.simulate_item_usage_dates(receipt)
            for r_item in simulated.get("items", []):
                r_item.pop("_id", None)
                item_doc = self.build_item_from_receipt(simulated, r_item)
                items_to_insert.append(item_doc)
                all_items.append(item_doc)

        if items_to_insert:
            result = self.items_collection.insert_many(items_to_insert)
            print(f"Inserted {len(result.inserted_ids)} items for {username}")
        else:
            print(f"No items to insert for {username}")
        return all_items


if __name__ == "__main__":
    generator = GenerateItems()
    usernames = [
        "lucy",  # from "lucy@gmail.com"
        "chris",  # from "chris@gmail.com"
        "jim",  # from "jim@gmail.com"
        "tony",  # from "tony@gmail.com"
        "adam",  # from "adam@gmail.com"
    ]
    # For expired receipts:
    for user in usernames:
        simulated_receipts = generator.process_receipts_to_items(username=user, num_receipts=50)
    # pprint.pprint(simulated_receipts)