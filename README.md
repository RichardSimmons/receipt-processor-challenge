# Receipt Processor

## Overview

The Receipt Processor is a simple web service that processes receipts and calculates points based on specific rules. It utilizes FastAPI for building the API and Docker for containerization.

### Key Features
- **User Authentication**: Secure endpoints using OAuth2 password flow.
- **Receipt Processing**: Submit receipts and receive calculated points.
- **Detailed Points Breakdown**: Get a breakdown of how points are calculated for each receipt.
- **Robust Testing**: Comprehensive unit and integration tests to ensure reliability.

---

## How to Use

Follow these steps to set up and use the Receipt Processor Challenge application:

### 1. Clone the Repository
```
git clone https://github.com/RichardSimmons/receipt-processor-challenge.git
```
2. Navigate to the Project Directory
```
cd receipt-processor-challenge
```
Open terminal and install requirements
```
pip install requirements.txt
```

4. Start the Application

Open a terminal in the project directory and run:
```
docker compose up --build
```
This command builds the Docker image and starts the FastAPI application. You can access the API at http://localhost:8000.


4. Run Tests

Open a new terminal and run:
```
pytest tests/main_test.py
```
This will execute all the tests defined in the tests folder.


Manual Testing
Submit a Receipt
Use the following curl command to submit a receipt for processing:

```
curl -X POST "http://localhost:8000/receipts/process" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <your_token_here>" \
     -d '{
           "retailer": "M&M Corner Market",
           "purchaseDate": "2022-01-01",
           "purchaseTime": "13:01",
           "items": [{"shortDescription": "Mountain Dew 12PK", "price": "6.49"}],
           "total": "6.49"
         }'
Expected Response:


{
  "id": "your_receipt_id",
  "points": 10,
  "breakdown": {
    "retailer_points": 10,
    "round_dollar_points": 50,
    "multiple_of_0.25_points": 25,
    "item_points": 5,
    "odd_date_points": 6,
    "time_points": 0
  }
}
```
Retrieve Points for a Receipt
Replace {id} with the receipt ID returned from the previous step and run:

```
curl -X GET "http://localhost:8000/receipts/{id}/points" \
     -H "Authorization: Bearer <your_token_here>"
Example Response:


{
  "points": 100
}
Notes
Ensure that Docker is installed and running before starting the application.
The examples in the examples folder are pre-configured to work with the provided pytest setup.
The application uses dummy user authentication. To access protected endpoints, you need to log in and obtain a token.
Example of Obtaining a Token
You can obtain a token by running:


curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=fakehashedsecret"
Expected Response:


{
  "access_token": "testuser",
  "token_type": "bearer"
}
```
Error Handling
The API returns appropriate HTTP status codes for different scenarios:
200 OK: Successful requests.
401 Unauthorized: Missing or invalid authentication.
422 Unprocessable Entity: Invalid data format or validation errors.
404 Not Found: Requested resource does not exist.
