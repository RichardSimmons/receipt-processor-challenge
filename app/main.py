from fastapi import FastAPI, HTTPException, Path, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator
from uuid import uuid4
from datetime import date, time
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# In-memory store for receipts and points
receipts_store: Dict[str, dict] = {}
points_store: Dict[str, int] = {}

# OAuth2 Password Bearer for user authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dummy user database
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "testuser@example.com",
        "hashed_password": "fakehashedsecret",  # In a real app, hash passwords
        "disabled": False,
    }
}

class InvalidReceiptDataError(Exception):
    pass

# Models based on OpenAPI specification
class Item(BaseModel):
    shortDescription: str = Field(
        ...,
        example="Mountain Dew 12PK",
        description="A short description of the item."
    )
    price: str = Field(
        ...,
        example="6.49",
        description="The price of the item, formatted as a string with two decimal places."
    )

    @validator("shortDescription")
    def validate_short_description(cls, description: str) -> str:
        """Ensure the description contains only valid characters."""
        if not all(c.isalnum() or c.isspace() or c in {'-', '_'} for c in description):
            raise ValueError(
                "Short description must contain only letters, numbers, spaces, hyphens, or underscores."
            )
        return description.strip()

    @validator("price")
    def validate_price(cls, price: str) -> str:
        """Ensure the price is a valid string representing a float with two decimal places."""
        try:
            parsed_price = float(price)
            if parsed_price <= 0:
                raise ValueError("Price must be greater than zero.")
            # Ensure it has exactly two decimal places
            if len(price.split('.')[-1]) != 2:
                raise ValueError("Price must have exactly two decimal places.")
        except ValueError:
            raise ValueError("Price must be a valid number formatted as a string (e.g., '6.49').")
        return price

class Receipt(BaseModel):
    retailer: str = Field(
        ...,
        example="M&M Corner Market",
        description="The name of the retailer or store."
    )
    purchaseDate: date = Field(
        ...,
        example="2022-01-01",
        description="The date of the purchase in YYYY-MM-DD format."
    )
    purchaseTime: time = Field(
        ...,
        example="13:01",
        description="The time of the purchase in 24-hour format (HH:MM)."
    )
    items: List[Item] = Field(
        ...,
        description="A list of at least one purchased item."
    )
    total: str = Field(
        ...,
        example="6.49",
        description="The total amount paid, formatted as a string with two decimal places."
    )

    @validator("retailer")
    def validate_retailer(cls, retailer: str) -> str:
        """Ensure the retailer name contains valid characters."""
        if not all(c.isalnum() or c.isspace() or c in {'-', '&'} for c in retailer):
            raise ValueError(
                "Retailer name must contain only letters, numbers, spaces, hyphens, or ampersands."
            )
        return retailer.strip()

    @validator("total")
    def validate_total(cls, total: str) -> str:
        """Ensure the total is a valid string representing a float with two decimal places."""
        try:
            parsed_total = float(total)
            if parsed_total <= 0:
                raise ValueError("Total must be greater than zero.")
            # Ensure it has exactly two decimal places
            if len(total.split('.')[-1]) != 2:
                raise ValueError("Total must have exactly two decimal places.")
        except ValueError:
            raise ValueError("Total must be a valid number formatted as a string (e.g., '6.49').")
        return total

# Endpoint: Token login for user authentication
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not user["hashed_password"] == "fakehashedsecret":  # Replace with hashed password check
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"access_token": user["username"], "token_type": "bearer"}

# Endpoint: Submit a receipt
@app.post("/receipts/process", status_code=200)
def process_receipt(receipt: Receipt, token: str = Depends(oauth2_scheme)):
    receipt_id = str(uuid4())
    receipts_store[receipt_id] = receipt.dict()
    points, breakdown = calculate_points(receipt)
    points_store[receipt_id] = points
    logger.info(f"Processed receipt for {receipt.retailer}: ID {receipt_id}, Points {points}")
    return {"id": receipt_id, "points": points, "breakdown": breakdown}

# Endpoint: Get points for a receipt
@app.get("/receipts/{id}/points", status_code=200)
def get_points(id: str = Path(..., regex=r"\S+")):
    if id not in receipts_store:
        logger.error(f"Receipt ID {id} not found.")
        raise HTTPException(status_code=404, detail="No receipt found for that ID.")
    return {"points": points_store[id]}

# Points calculation logic
def calculate_points(receipt: Receipt):
    points = 0
    breakdown = {}

    # Rule 1: 1 point per alphanumeric character in the retailer name
    points += sum(c.isalnum() for c in receipt.retailer)
    breakdown['retailer_points'] = points

    # Rule 2: 50 points if the total is a round dollar amount with no cents
    total_float = float(receipt.total)
    if total_float.is_integer():
        points += 50
        breakdown['round_dollar_points'] = 50

    # Rule 3: 25 points if the total is a multiple of 0.25
    if total_float % 0.25 == 0:
        points += 25
        breakdown['multiple_of_0.25_points'] = 25

    # Rule 4: 5 points for every two items on the receipt
    points += (len(receipt.items) // 2) * 5
    breakdown['item_points'] = (len(receipt.items) // 2) * 5

    # Rule 5: If the purchase date is odd, add 6 points
    if receipt.purchaseDate.day % 2 == 1:
        points += 6
        breakdown['odd_date_points'] = 6

    # Rule 6: If the purchase time is between 14:00 and 16:00, add 10 points
    if time(14, 0) <= receipt.purchaseTime < time(16, 0):
        points += 10
        breakdown['time_points'] = 10

    return points, breakdown

@app.exception_handler(InvalidReceiptDataError)
async def handle_invalid_receipt_data(request: Request, exc: InvalidReceiptDataError):
    return JSONResponse(status_code=400, content={"message": str(exc)})

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>FastAPI Receipt Processing Service</title>
        </head>
        <body>
            <h1>Welcome to the FastAPI Receipt Processing Service</h1>
            <p>Use the <a href="/docs">API documentation</a> to interact with the service.</p>
        </body>
    </html>
    """

# Run FastAPI application if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)