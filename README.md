# ai-suggestion-items-to-buy
# AI-Powered Shopping List Service

## Overview

This repository implements a complete pipeline for an AI-driven shopping list service for items management on course compsci 732, if you want the database design, please mark a star, and then send me an email:

1. **Synthetic Data Generation**: Tools to generate realistic historical receipts (`generatereceipt.py`) and corresponding item usage records (`generateitems.py`).
2. **Model Training**: A script (`training.py`) that trains both regression and classification Random Forest models to predict consumption durations and reorder flags.
3. **API Service**: A FastAPI router (`airouter.py`) exposing endpoints for data simulation, model prediction, and recommendation.

## Repository Structure

```
├── generatereceipt.py     # Receipt generation tool
├── generateitems.py       # Item simulation tool
├── training.py            # Model training script
├── airouter.py            # FastAPI router for data and prediction
├── start.sh                # start server locally
├── requirement.txt        # dependencies
├── dockerfile             # you can use this to create docker image
└── README.md              # This documentation file
```

## Dependencies
* pymongo
* fastapi
* uvicorn
* pymongo
* scikit-learn
* pandas
* numpy
* pydantic
* pydantic-settings
* gunicorn
* uvloop
* inflect
* pytest
* pytest-asyncio (if testing async endpoints)
* requests (for tests)

Install via:

```bash
pip3 install pymongo fastapi uvicorn pymongo scikit-learn pandas numpy gunicorn uvloop inflect pytest pytest-asyncio requests
```

## Usage

### 1. Generate Synthetic Data

#### Receipts
request post:  'https://localhost:9999/api/receipts/insert'
{
  "username": "gary",
  "status": "recent",
  "num": 1
}

#### Items

request post  'https://localhost:9999/api/items/simulate' 
{
  "username": "gary",
  "num_receipts": 10
}'

* generated receipts and expands each into item documents.
* Simulates `start_date`, `end_date`, and `predicted_consumed_date`, etc.

### 2. Train Models
training.py 
request post  'http://localhost:9999/api/predictandrecommend' 
{
  "username": "gary"
}'

* Loads all item records for the username from MongoDB.
* Performs feature engineering (`validity_days`, `days_since_usage`, `consumption_rate`, `price_per_day`).
* Trains:
  * ** Train a RandomForestRegressor to predict the consumption duration (in days) of an item.
  * **Forecast the consumption date for an item (which is missing its end_date).
      The method uses a regression model based on similar items to predict the consumption duration from start_date.
      Query the items collection for the total consumption of a specific item (by item_name) for the given user in the last two weeks (considering consumed items with an end_date).
  * Train a RandomForestClassifier to predict if an item should be repurchased soon. Features: quantity, capacity, price, conversion_factor, validity_days, days_since_usage.
  * Merge duplicate recommended items in the list based on itemName and unit. For each merged item, query the user's consumption over the last two weeks.
  * Finally, 
      1. Retrieve user's items.
      2. For items missing an end_date, forecast a predicted consumption date.
      3. Train a classifier to predict repurchase needs.
      4. Generate recommendations.
      Returns a summary dictionary.
### 3. Run API Service
```bash
     sh start.sh
```
or run
```bash
     uvicorn main:app --reload --host 0.0.0.0 --port 9999
```

### 4. Automated Testing

```bash
pytest test_shoppinglist_api.py
```

* Validates correct behaviors for all `/shopping` endpoints and `/predictandrecommend`.
* Includes positive and negative test cases.

## Configuration

* MongoDB connection details can be set via environment variables: `mongodb_uri`, `mongodb_db`.
* If you want the database, please give a star and fork and then email me or comment.

## Deploy online

* Integrate Docker and GitHub Actions for CI/CD.
* Add front-end dashboard for live recommendation visualization.
* This project is just backend, the frontend is in a private project. If you want some guidence on course project, devops or automation test, you can email me. 
* <img width="227" height="524" alt="image" src="https://github.com/user-attachments/assets/78633f0c-331d-4ff2-8644-459c52a18910" />
