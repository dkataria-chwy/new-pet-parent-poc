"""Create payload indexes in Qdrant for filtering."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "chewy_products_117k"

session = requests.Session()
session.headers.update({
    'api-key': QDRANT_API_KEY,
    'Content-Type': 'application/json'
})

print("=" * 80)
print("Creating Payload Indexes in Qdrant")
print("=" * 80)

# Create index for species_dog_flag
print("\n1️⃣ Creating index for species_dog_flag...")
response = session.put(
    f"{QDRANT_URL}/collections/{COLLECTION_NAME}/index",
    json={
        "field_name": "species_dog_flag",
        "field_schema": "bool"
    }
)

if response.status_code == 200:
    print("✅ species_dog_flag index created successfully")
else:
    print(f"❌ Failed: {response.status_code} - {response.text}")

# Create index for species_cat_flag
print("\n2️⃣ Creating index for species_cat_flag...")
response = session.put(
    f"{QDRANT_URL}/collections/{COLLECTION_NAME}/index",
    json={
        "field_name": "species_cat_flag",
        "field_schema": "bool"
    }
)

if response.status_code == 200:
    print("✅ species_cat_flag index created successfully")
else:
    print(f"❌ Failed: {response.status_code} - {response.text}")

print("\n" + "=" * 80)
print("✅ Indexes created successfully!")
print("=" * 80)

