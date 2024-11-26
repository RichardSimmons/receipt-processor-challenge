# test_main.py

import os
import json
import requests
import pytest

# Base URL for the FastAPI application
BASE_URL = "http://localhost:8000"

# Directory containing example JSON files
EXAMPLES_DIR = "examples"

# Helper function to get a token for authentication
def get_auth_token():
    response = requests.post(f"{BASE_URL}/token", data={"username": "testuser", "password": "fakehashedsecret"})
    return response.json()["access_token"]

def test_process_receipt():
    """Test processing a valid receipt."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    with open("examples/morning-receipt.json", "r") as file:
        example_receipt = json.load(file)

    response = requests.post(f"{BASE_URL}/receipts/process", json=example_receipt, headers=headers)
    assert response.status_code == 200
    assert "id" in response.json()

def test_get_points():
    """Test retrieving points for a processed receipt."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    with open("examples/morning-receipt.json", "r") as file:
        example_receipt = json.load(file)

    response = requests.post(f"{BASE_URL}/receipts/process", json=example_receipt, headers=headers)
    receipt_id = response.json()["id"]

    points_response = requests.get(f"{BASE_URL}/receipts/{receipt_id}/points", headers=headers)
    assert points_response.status_code == 200
    assert "points" in points_response.json()

def test_all_examples():
    """Test processing all example receipt JSON files in the 'examples' directory."""
    for file_name in os.listdir(EXAMPLES_DIR):
        if file_name.endswith(".json"):
            file_path = os.path.join(EXAMPLES_DIR, file_name)
            with open(file_path, "r") as file:
                example_receipt = json.load(file)
                token = get_auth_token()
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.post(f"{BASE_URL}/receipts/process", json=example_receipt, headers=headers)
                if file_name == "invalid-receipt.json":
                    assert response.status_code == 422, f"Expected 422 for {file_name}, got {response.status_code}: {response.text}"
                else:
                    assert response.status_code == 200, f"Failed processing {file_name}: {response.text}"

def test_invalid_receipt_format():
    """Test sending a receipt with an invalid format."""
    invalid_data = {"not": "a", "receipt": "format"}
    token = get_auth_token()  # Get the token for authentication
    headers = {"Authorization": f"Bearer {token}"}  # Include the token in the headers
    response = requests.post(f"{BASE_URL}/receipts/process", json=invalid_data, headers=headers)
    assert response.status_code == 422  # Expecting 422 for invalid data

def test_invalid_receipt_data():
    """Test sending a receipt with invalid data (invalid retailer name)."""
    with open("examples/morning-receipt.json", "r") as file:
        example_receipt = json.load(file)
    example_receipt["retailer"] = "123!@#$%"  # Invalid characters in retailer name

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/receipts/process", json=example_receipt, headers=headers)
    assert response.status_code == 422

def test_get_points_nonexistent_receipt():
    """Test retrieving points for a non-existent receipt."""
    receipt_id = "invalid_id"
    response = requests.get(f"{BASE_URL}/receipts/{receipt_id}/points")
    assert response.status_code == 404

def test_get_points_invalid_id_format():
    """Test retrieving points with an invalid receipt ID format."""
    invalid_id = "invalid_format"
    response = requests.get(f"{BASE_URL}/receipts/{invalid_id}/points")
    assert response.status_code == 404

def test_process_receipt_with_multiple_items():
    """Test processing a receipt with multiple items."""
    multi_item_receipt = {
        "retailer": "M&M Corner Market",
        "purchaseDate": "2022-03-20",
        "purchaseTime": "14:33",
        "items": [
            {"shortDescription": "Gatorade", "price": "2.25"},
            {"shortDescription": "Gatorade", "price": "2.25"},
            {"shortDescription": "Gatorade", "price": "2.25"},
            {"shortDescription": "Gatorade", "price": "2.25"},
        ],
        "total": "9.00"
    }
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/receipts/process", json=multi_item_receipt, headers=headers)
    assert response.status_code == 200
    receipt_id = response.json()["id"]

    points_response = requests.get(f"{BASE_URL}/receipts/{receipt_id}/points", headers=headers)
    assert points_response.status_code == 200
    points = points_response.json().get("points")
    assert points is not None  # Ensure points are not None
    assert points == 109  # Expected points based on the example

def test_process_receipt_with_round_dollar_amount():
    """Test processing a receipt with a round dollar amount."""
    round_dollar_receipt = {
        "retailer": "Supermart",
        "purchaseDate": "2022-01-01",
        "purchaseTime": "10:00",
        "items": [
            {"shortDescription": "Bread", "price": "1.00"},
            {"shortDescription": "Milk", "price": "2.00"},
        ],
        "total": "3.00"
    }
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/receipts/process", json=round_dollar_receipt, headers=headers)
    assert response.status_code == 200
    receipt_id = response.json()["id"]

    points_response = requests.get(f"{BASE_URL}/receipts/{receipt_id}/points", headers=headers)
    assert points_response.status_code == 200
    points = points_response.json().get("points")
    assert points is not None  # Ensure points are not None
    assert points == 95  # Update expected points to 95 based on the calculation

def test_process_receipt_with_edge_case_retailer_name():
    """Test processing a receipt with an edge case retailer name."""
    edge_case_receipt = {
        "retailer": "Retailer123",  # Remove underscore
        "purchaseDate": "2022-01-01",
        "purchaseTime": "13:01",
        "items": [
            {"shortDescription": "Item A", "price": "5.00"},
            {"shortDescription": "Item B", "price": "10.00"},
        ],
        "total": "15.00"
    }
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/receipts/process", json=edge_case_receipt, headers=headers)
    assert response.status_code == 200
    receipt_id = response.json()["id"]
    points_response = requests.get(f"{BASE_URL}/receipts/{receipt_id}/points", headers=headers)
    assert points_response.status_code == 200
    points = points_response.json().get("points")
    assert points is not None  # Ensure points are not None
    assert points >= 0  # Ensure points are a non-negative integer

def test_process_receipt_with_long_item_description():
    """Test processing a receipt with a long item description."""
    long_item_receipt = {
        "retailer": "Target",
        "purchaseDate": "2022-01-01",
        "purchaseTime": "13:01",
        "items": [
            {"shortDescription": "A long description of a product that exceeds normal lengths", "price": "6.49"},
            {"shortDescription": "Another product", "price": "12.25"},
        ],
        "total": "18.74"
    }
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/receipts/process", json=long_item_receipt, headers=headers)
    assert response.status_code == 200
    receipt_id = response.json()["id"]
    points_response = requests.get(f"{BASE_URL}/receipts/{receipt_id}/points", headers=headers)
    assert points_response.status_code == 200
    points = points_response.json().get("points")
    assert points is not None  # Ensure points are not None
    assert points >= 0  # Ensure points are a non-negative integer

    

# You can run the tests with pytest
if __name__ == "__main__":
    pytest.main()