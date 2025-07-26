# author : chris-jyp

from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
from pymongo import DESCENDING
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from database.databaseconnection import MongoDBClient
from database.functions import FunctionAI
import inflect
from zoneinfo import ZoneInfo

p = inflect.engine()
ai = FunctionAI()
db = MongoDBClient()
# Set New Zealand timezone
nz_tz = ZoneInfo("Pacific/Auckland")


def train_consumption_duration_model(user_items: list, item_name: str):
    """
    Train a RandomForestRegressor to predict the consumption duration (in days) of an item.
    Uses historical items (with both start_date and end_date) of the same type.
    """
    historical = [
        it for it in user_items
        if it["name"].lower() == item_name.lower()
           and it.get("start_date") and it.get("end_date")
    ]
    if len(historical) < 2:
        return None

    training_data = []
    for it in historical:
        validity_days = (it["expiry_date"] - it["purchase_date"]).days if it.get("purchase_date") and it.get(
            "expiry_date") else 0
        consumption_duration = (it["end_date"] - it["start_date"]).days
        conv_factor = ai.get_conversion_factor(it.get("capacity_unit", ""))
        training_data.append({
            "quantity": it.get("quantity", 1),
            "capacity": it.get("capacity", 0),
            "price": it.get("price", 0.0),
            "conversion_factor": conv_factor,
            "validity_days": validity_days,
            "consumption_duration": consumption_duration
        })

    df = pd.DataFrame(training_data)
    X = df[["quantity", "capacity", "price", "conversion_factor", "validity_days"]]
    y = df["consumption_duration"]
    regressor = RandomForestRegressor(random_state=42)
    regressor.fit(X, y)
    return regressor


def forecast_consumption_date(item: dict, user_items: list, default_days: int = 7) -> datetime:
    """
    Forecast the consumption date for an item (which is missing its end_date).
    The method uses a regression model based on similar items to predict the consumption duration from start_date.
    """
    # —— fallback for missing start_date ——
    start = item.get("start_date")
    if start is None:
        purchase = item.get("purchase_date")
        if purchase:
            start = purchase + timedelta(days=1)
        else:
            # no purchase_date either—just use today
            start = datetime.now(nz_tz)
    # —— end fallback ——
    model = train_consumption_duration_model(user_items, item["name"])
    conv_factor = ai.get_conversion_factor(item.get("capacity_unit", ""))
    validity_days = (item["expiry_date"] - item["purchase_date"]).days if item.get("purchase_date") and item.get(
        "expiry_date") else 0
    features = np.array(
        [[item.get("quantity", 1), item.get("capacity", 0), item.get("price", 0.0), conv_factor, validity_days]])

    if model is not None:
        predicted_duration = model.predict(features)[0]
        predicted_duration = max(1, round(predicted_duration))
    else:
        predicted_duration = default_days

    predicted_date = start + timedelta(days=predicted_duration)
    db.items_collection.update_one(
        {"_id": item["_id"]},
        {"$set": {"predicted_consumed_date": predicted_date}}
    )
    item["predicted_consumed_date"] = predicted_date
    return predicted_date


def get_recent_consumption(user_name, item_name):
    """
    Query the items collection for the total consumption of a specific item
    (by item_name) for the given user in the last two weeks (considering consumed items with an end_date).
    Returns a dictionary with:
      - total_quantity: Sum of the quantity fields,
      - total_consumption: Sum of (quantity * capacity) if capacity is available for an item;
                           otherwise, just quantity,
      - capacity_unit: The capacity unit found (assumes they are uniform or returns the first non-null value),
      - capacity: The representative capacity value for a single unit. In this version, it is determined
                  as the maximum of all consumed capacity values.
    """
    two_weeks_ago = datetime.now(nz_tz) - timedelta(days=14)
    cursor = db.items_collection.find({
        "user_name": user_name,
        "name": {"$regex": f"^{item_name}$", "$options": "i"},
        "status": "consumed",
        "end_date": {"$gte": two_weeks_ago}
    })

    total_quantity = 0
    total_consumption = 0
    capacity_unit_found = None
    capacity_values = []  # Accumulate individual capacity values

    for doc in cursor:
        qty = doc.get("quantity", 0)
        total_quantity += qty
        cap = doc.get("capacity")
        if cap is not None:
            try:
                cap_val = float(cap)
                capacity_values.append(cap_val)
                consumption_amount = qty * cap_val
            except Exception as e:
                consumption_amount = qty
        else:
            consumption_amount = qty
        total_consumption += consumption_amount

        # Record capacity_unit if not already set and available.
        if not capacity_unit_found and doc.get("capacity_unit"):
            capacity_unit_found = doc.get("capacity_unit")

    # Determine a representative capacity: choose the maximum capacity from the collected values.
    capacity_value = None
    if capacity_values:
        capacity_value = max(capacity_values)

    return {
        "total_quantity": total_quantity,
        "total_consumption": total_consumption,
        "capacity_unit": capacity_unit_found,
        "capacity": capacity_value
    }


def train_rf_model_classification(username: str, items: list, threshold_days: int = 7):
    """
    Train a RandomForestClassifier to predict if an item should be repurchased soon.
    Features: quantity, capacity, price, conversion_factor, validity_days, days_since_usage.
    Label: 1 if the item is predicted to be consumed within threshold_days from now.
    """
    now = datetime.utcnow()
    training_data = []
    for it in items:
        if not it.get("predicted_consumed_date"):
            forecast_consumption_date(it, items)
        validity_days = (it["expiry_date"] - it["purchase_date"]).days if it.get("purchase_date") and it.get(
            "expiry_date") else 0
        days_since_usage = (now - it["start_date"]).days if it.get("start_date") else 0
        conv_factor = ai.get_conversion_factor(it.get("capacity_unit", ""))
        label = 1 if (it["predicted_consumed_date"] - now).days <= threshold_days else 0

        training_data.append({
            "quantity": it.get("quantity", 1),
            "capacity": it.get("capacity", 0),
            "price": it.get("price", 0.0),
            "conversion_factor": conv_factor,
            "validity_days": validity_days,
            "days_since_usage": days_since_usage,
            "label": label
        })

    if len(training_data) < 2:
        return None

    df = pd.DataFrame(training_data)
    X = df[["quantity", "capacity", "price", "conversion_factor", "validity_days", "days_since_usage"]]
    y = df["label"]
    model = RandomForestClassifier(random_state=42)
    model.fit(X, y)
    return model

def merge_recommended_items(recommended_items, user_name):
    """
    Merge duplicate recommended items in the list based on itemName and unit.
    For each merged item, query the user's consumption over the last two weeks.
    The final quantity is determined as follows:
      - If recent consumption can be computed (nonzero), use that as the final quantity.
      - Otherwise, use the summed recommended quantity.
      - In any case, if the final quantity exceeds 4, cap it at 4.
    Each merged item will have its total_price recalculated (assuming 'price' is the unit price),
    and will be marked with "source": ai.
    """
    merged = {}
    for item in recommended_items:
        # normalize itemName: lowercase and singular conversion
        item_name = item["itemName"].strip().lower()
        singular_name = p.singular_noun(item_name)
        if singular_name:
            item_name = singular_name
        key = item_name
        if key not in merged:
            merged[key] = item.copy()
        else:
            merged[key]["quantity"] += item["quantity"]
    merged_items = []
    for key, item  in merged.items():
        print("keykeykey",key)
        # Query the user's consumption for this item in the last two weeks.
        recent_consumption = get_recent_consumption(user_name, key)
        print("recent_consumption",recent_consumption)
        # Determine final quantity:
        if recent_consumption['total_quantity'] and recent_consumption['total_quantity'] > 0:
            final_quantity = recent_consumption['total_quantity']
        else:
            final_quantity = item["quantity"]
        cap = recent_consumption.get("capacity")
        capacity = cap if cap is not None else 1
        unit = recent_consumption.get("capacity_unit")
        quantity = final_quantity
        # If that's None or empty, query the DB for another item
        if not unit:
            fallback = db.items_collection.find_one(
                {
                    "name": {
                            "$regex": f"^{key}$",
                            "$options": "i"
                        },
                    "capacity_unit": {
                    "$exists": True,
                    "$nin": [None, ""]}
                },
                sort=[("purchase_date", DESCENDING)],  # pick the most recent
                projection=["capacity_unit","capacity","quantity"]
            )
            if fallback:
                unit = fallback["capacity_unit"]
                capacity = fallback["capacity"]
                quantity = fallback["quantity"]
            else:
                unit = "pcs"
                capacity = 1
                quantity = 2
        # Cap the final quantity at 4
        if final_quantity > 4:
            final_quantity = 4
        item["quantity"] = final_quantity
        item["capacity_unit"] = unit
        item["capacity"] = max(capacity or 0, 1)
        # Recalculate total_price using the unit price (assuming "price" is per unit).
        item["total_price"] = round(item["quantity"] * item["price"], 2)
        item["source"] =  "ai"
        merged_items.append(item)
    return merged_items

def predict_and_recommend_service(username: str) -> dict:
    """
    This service function implements the business logic:
      1. Retrieve user's items.
      2. For items missing an end_date, forecast a predicted consumption date.
      3. Train a classifier to predict repurchase needs.
      4. Generate recommendations.
    Returns a summary dictionary.
    """
    now = datetime.now(nz_tz)
    threshold_days = 2  # Threshold to decide if repurchase is needed.

    user_items = ai.get_items_for_user(username)
    if not user_items:
        return {"error": "No items found for the specified user."}

    # Forecast consumption dates for items without an end_date.
    for it in user_items:
        if not it.get("end_date") and not it.get("predicted_consumed_date") and it.get("start_date"):
            forecast_consumption_date(it, user_items)

    rf_model_classification = train_rf_model_classification(username, user_items, threshold_days=threshold_days)
    recommendations = []

    for it in user_items:
        validity_days = (it["expiry_date"] - it["purchase_date"]).days if it.get("purchase_date") and it.get("expiry_date") else 0
        conv_factor = ai.get_conversion_factor(it.get("capacity_unit", ""))
        # Ensure `it["start_date"]` is offset-aware
        if it.get("start_date"):
            start_date = it["start_date"].replace(tzinfo=nz_tz)  # Assign UTC timezone if missing
            days_since_usage = (now - start_date).days
        else:
            days_since_usage = 0
        # Ensure `features` has the same structure as the training data
        feature_columns = ["quantity", "capacity", "price", "conversion_factor", "validity_days", "days_since_usage"]
        features = [[
            it.get("quantity", 1),
            it.get("capacity", 0),
            it.get("price", 0.0),
            conv_factor,
            validity_days,
            days_since_usage
        ]]
        features_df = pd.DataFrame(features, columns=feature_columns)        # Use the DataFrame for prediction
        if rf_model_classification is not None:
            prediction = rf_model_classification.predict(features_df)[0]
        else:
            days_to_consumption = (it["predicted_consumed_date"] - now).days if it.get(
                "predicted_consumed_date") else 999
            prediction = 1  if days_to_consumption <= threshold_days else 0
        if prediction == 1:
            # Normalize the item name (lowercase and singular)
            normalized_name = it.get("name", "").strip().lower()
            singular_name = p.singular_noun(normalized_name)
            if singular_name:
                normalized_name = singular_name
            recommendations.append({
                "itemName": normalized_name,
                "quantity": it.get("quantity", 1),
                "capacity_unit": it.get("capacity_unit", "pcs"),
                "price": it.get("price", 0.0),
                "predicted_consumed_date": it["predicted_consumed_date"].isoformat() if it.get(
                    "predicted_consumed_date") else "",
                "suggestion": f"{it.get('name', '')} is predicted to be consumed by {it.get('predicted_consumed_date').date() if it.get('predicted_consumed_date') else 'N/A'}. Please consider repurchasing soon."
            })

    shopping_list = ai.get_or_create_shopping_list(username)
    existing_items = [item["itemName"].lower() for item in shopping_list.get("items", [])]
    for rec in recommendations:
        if rec["itemName"].lower() not in existing_items:
            shopping_list["items"].append({
                "itemName": rec["itemName"],
                "quantity": rec["quantity"],
                "capacity_unit": rec["capacity_unit"],
                "price": rec["price"],
                "source": "ai",
                "status": "pending"
            })
            shopping_list["totalItems"] = 0
            shopping_list["estimatedTotal"] = 0
            shopping_list["updatedAt"] = datetime.now(nz_tz)

    # --- Merge duplicate recommended items using recent consumption info ---
    merged_items = merge_recommended_items(shopping_list["items"], username)
    shopping_list["items"] = merged_items
    # Optionally, recalc totalItems and estimatedTotal after merge:
    shopping_list["totalItems"] = len(merged_items)
    shopping_list["estimatedTotal"] = round(sum(item["price"] * item["quantity"] for item in merged_items), 2)
    # Update the shopping list in the database.
    # ai.update_shopping_list(shopping_list)
    result =  {
        "code":200,
        "status":"success",
        "username": username,
        "model_trained": rf_model_classification is not None,
        "recommendations": merged_items,
        "shopping_list": shopping_list
    }
    print("result",result)
    return result
if __name__ == "__main__":
    predict_and_recommend_service('chris')