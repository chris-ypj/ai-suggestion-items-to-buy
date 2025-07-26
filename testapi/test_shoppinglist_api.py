import pytest
import requests

BASE_URL = "https://outstanding-programmer.azurewebsites.net/api"
LOGIN_URL = f"{BASE_URL}/auth/login"

@pytest.fixture(scope="session")
def token():
    # Replace with valid credentials
    email = "lucy@gmail.com"
    password = "lucy11"
    payload = {"email": email, "password": password, "remember_me": False}
    response = requests.post(LOGIN_URL, json=payload)
    response.raise_for_status()
    data = response.json()
    token = data.get("token")
    if not token:
        pytest.fail("Token not found in login response.")
    return token

@pytest.fixture
def headers(token):
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.parametrize(
    "payload, expected_code, message_contains",
    [  # username exists → 200
        ({"username": "Lucy"}, 200, ["AI-predicted items added to the shopping cart"]),
    ]
)
@pytest.mark.order(1)
def test_add_ai_predict_to_trolley_success(payload, expected_code, message_contains,headers):
    resp = requests.post(f"{BASE_URL}/shopping/addaipredicttotrolley", headers=headers, json=payload)
    body = resp.json()
    assert body["code"] == expected_code
    assert body.get("message") in message_contains


@pytest.mark.parametrize(
    "payload, expected_code, status",
    [  # lack username → 400
        ({}, 403, "fail"),
        # username does not exist → 400
        ({"username": "alice"}, 403, "fail"),
    ]
)
@pytest.mark.order(2)
def test_add_ai_predict_to_trolley(payload, expected_code, status,headers):
    resp = requests.post(f"{BASE_URL}/shopping/addaipredicttotrolley", headers=headers, json=payload)
    body = resp.json()
    assert body["code"] == expected_code
    assert  body.get("status")==status

@pytest.mark.parametrize(
    "payload, expected_http, expected_code, expect_selected",
    [   # lack username → 400
        ({"username": ""}, 200, 403, None),
        # username does not exist → 400
        ({"username": "alice", "itemname": "banana"}, 200, 403, None),
        # itemname does not exist → 400
        ({"username": "alice", "itemname": "notnot"}, 200, 403, None),
        # username exists → 200
        ({"username": "Lucy", "itemname": "bread", "source": "ai", "selected": True}, 200, 200, True),
        # itemname source is not correct → 400
        ({"username": "Lucy", "itemname": "bread", "source": "manual", "selected": False}, 200, 400, None),
    ]
)
@pytest.mark.order(3)
def test_update_item_status(payload, expected_http, expected_code, expect_selected,headers):
    resp = requests.post(f"{BASE_URL}/shopping/updateitemstatus", headers=headers, json=payload)
    body = resp.json()
    print(body)
    assert body["code"] == expected_code
    if expect_selected is not None:
        items = body["data"]
        for  iteminfo in items['items']:
            if iteminfo['itemName']==payload["itemname"].lower() and iteminfo['source']==payload["source"]:
                select_status = iteminfo['selected']
                break
        assert select_status == expect_selected

@pytest.mark.parametrize(
    "params, expected_http, expected_code, expected_msg_contains",
    [
        # lack username → 400
        ({}, 403, 403, "User and token mismatch"),
        #  username does not exist 200 and data is not none
        ({"username": "alice"}, 403, 403, "User and token mismatch"),
        # username  exists 200 and data is not none
        ({"username": "Lucy"}, 200, 200, None),
    ]
)
@pytest.mark.order(4)
async def test_get_shopping_list(params, expected_http, expected_code, expected_msg_contains,headers):
    resp = requests.get(f"{BASE_URL}/shopping/getshoppinglist", headers=headers, params=params)
    assert resp.status_code == expected_http
    body = resp.json()
    assert body["code"] == expected_code
    if expected_msg_contains:
        assert expected_msg_contains in body.get("message", "")
    else:
        assert "data" in body
        assert isinstance(body["data"], (list, dict))
        assert body["data"]["userName"]==params["username"]

@pytest.mark.parametrize(
    "payload, expected_http, expected_code, expect_keys",
    [  # add an item to a user that does not exist
        ({"username": "alice"}, 403, 403, ["status", "message"]),
        # add an item to a user that exists
        ({"username": "Lucy", "item": {"itemName":"banana","price":2,"quantity":1,"capacity":1,"capacity_unit":"pcs"}}, 200, 200, ["status", "data"]),
    ]
)
@pytest.mark.order(5)
def test_add_item_to_trolley(payload, expected_http, expected_code, expect_keys,headers):
    resp = requests.post(f"{BASE_URL}/shopping/additemtotrolley", headers=headers, json=payload)
    assert resp.status_code == expected_http
    body = resp.json()
    assert body["code"] == expected_code
    for key in expect_keys:
        assert key in body
    if expected_code == 200:
        item = body["data"][-1] if isinstance(body["data"], list) else body["data"]
        assert item["userName"]==payload["username"]
        assert any(iteminfo["itemName"] == payload["item"]["itemName"] for iteminfo in item["items"])
        assert any(iteminfo["capacity"] == payload["item"]["capacity"] for iteminfo in item["items"])


@pytest.mark.parametrize(
    "payload, expected_http, expected_code, expected_keys",
    [    # delete an item that exists
        ({"username": "Lucy", "itemname": "banana", "source": "manual"}, 200, 200, ["status", "data"]),
        #delete an item that has been deleted
        ({"username": "Lucy", "itemname": "banana", "source": "manual"}, 200, 400, ["status", "message"]),
    ]
)
@pytest.mark.order(6)
def test_remove_deleted_item_from_trolley(payload, expected_http, expected_code, expected_keys,headers):
    resp = requests.delete(f"{BASE_URL}/shopping/removeitemfromtrolley", headers=headers, json=payload)
    assert resp.status_code == expected_http
    body = resp.json()
    assert body["code"] == expected_code
    # Validate that all expected keys are in the response body.
    for key in expected_keys:
        assert key in body, f"Missing key '{key}' in response"
    if "data" in expected_keys:
        # Verify that the deleted item does not appear in the response.
        data = body.get("data", {})
        items = data.get("items", []) if isinstance(data, dict) and "items" in data else data
        for item in items:
            if item['itemName']==payload["itemname"].lower() and item['source']==payload["source"]:
                delete_status = item.get("status")
                break
        assert  (delete_status=="delete"), f" deleted item '{payload['itemname']}' from source '{payload['source']} failed' "


@pytest.mark.parametrize(
    "payload, expected_http, expected_code, expected_message",
    [    # delete an item from a user that does not exist
        ({"username": "alice", "itemname": "Banana"}, 403, 403, "User and token mismatch"),
        # delete an item  that does not exist
        ({"username": "Lucy", "itemname": "DoesNotExist", "source": "manual"}, 200, 400, None),
    ]
)
@pytest.mark.order(7)
def test_remove_item_from_trolley(payload, expected_http, expected_code, expected_message,headers):
    resp = requests.delete(f"{BASE_URL}/shopping/removeitemfromtrolley", headers=headers, json=payload)
    assert resp.status_code == expected_http
    body = resp.json()
    assert body["code"] == expected_code
    if expected_message:
        assert expected_message in body.get("message", "")
    else:
        assert "no the item" in body["message"]

@pytest.mark.parametrize(
    "payload, expected_http, expected_code, status",
    [   # lack username → 400
        ({}, 403, 403, 'fail'),
        # username does not exist → 400
        ({"username": "alice"}, 403, 403, 'fail'),
        # username exists → 200
        ({"username": "Lucy"}, 200, 200, 'success'),
    ]
)
@pytest.mark.order(8)
def test_done_shopping_list(payload, expected_http, expected_code, status,headers):
    resp = requests.post(f"{BASE_URL}/shopping/done", headers=headers, json=payload)
    assert resp.status_code == expected_http
    body = resp.json()
    assert body["code"] == expected_code
    if status:
        assert body.get("status")==status
    else:
        assert "data" in body or "message" in body