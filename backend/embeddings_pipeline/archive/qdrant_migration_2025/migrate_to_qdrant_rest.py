"""
Alternative migration script using REST API directly (bypasses httpx timeout issues).

This script uses the requests library to directly call Qdrant's REST API,
avoiding the httpx connection timeout issues we encountered with the Python client.
"""

import requests
import json
from pathlib import Path
import os
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Load environment variables
load_dotenv()

# Qdrant credentials
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "chewy_products_117k"

# Set up session with API key
session = requests.Session()
session.headers.update({
    'api-key': QDRANT_API_KEY,
    'Content-Type': 'application/json'
})


def check_connection():
    """Test connection to Qdrant."""
    print("🔍 Testing connection to Qdrant...")
    try:
        response = session.get(f"{QDRANT_URL}/collections", timeout=30)
        response.raise_for_status()
        print(f"✅ Connection successful!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False


def delete_collection():
    """Delete existing collection if it exists."""
    try:
        response = session.delete(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", timeout=30)
        if response.status_code == 200:
            print(f"✅ Deleted existing collection: {COLLECTION_NAME}")
            time.sleep(2)
            return True
        elif response.status_code == 404:
            print(f"✅ Collection doesn't exist yet - will create new one")
            return True
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Error checking/deleting collection: {e}")
        return True  # Proceed anyway


def create_collection():
    """Create Qdrant collection with optimized settings."""
    print(f"📦 Creating collection: {COLLECTION_NAME}")
    
    collection_config = {
        "vectors": {
            "size": 3072,  # Actual dimension from your embeddings (text-embedding-3-large with increased dims)
            "distance": "Cosine"
        },
        "optimizers_config": {
            "indexing_threshold": 20000
        },
        "hnsw_config": {
            "m": 16,
            "ef_construct": 100
        }
    }
    
    try:
        response = session.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
            json=collection_config,
            timeout=60
        )
        response.raise_for_status()
        print(f"✅ Created collection: {COLLECTION_NAME}")
        return True
    except Exception as e:
        print(f"❌ Failed to create collection: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
        return False


def upload_batch(points, batch_num):
    """Upload a batch of points to Qdrant."""
    try:
        payload = {
            "points": points
        }
        
        response = session.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points",
            json=payload,
            params={"wait": "true"},  # Wait for confirmation (was "false" - that's why data wasn't persisted!)
            timeout=180  # Longer timeout since we're waiting
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"\n⚠️  Error uploading batch {batch_num}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text[:200]}")
        return False


def migrate_to_qdrant():
    """Migrate 117K embeddings to Qdrant using REST API."""
    
    print("=" * 80)
    print("🚀 Starting Qdrant migration for 117K products (REST API)")
    print("=" * 80)
    
    # Test connection
    if not check_connection():
        print("\n❌ Cannot connect to Qdrant. Please check your credentials.")
        return
    
    # Check/delete existing collection
    print(f"\n⚠️  Checking for existing collection '{COLLECTION_NAME}'...")
    delete_collection()  # Auto-proceed with deletion
    
    # Create collection
    if not create_collection():
        return
    
    # Load embeddings
    embeddings_path = Path(__file__).parent / "artifacts" / "catalog_embeds.jsonl"
    
    if not embeddings_path.exists():
        print(f"❌ Error: Embeddings file not found at {embeddings_path}")
        return
    
    print(f"\n📂 Loading embeddings from: {embeddings_path}")
    
    # Count total lines
    with open(embeddings_path, 'r') as f:
        total_lines = sum(1 for _ in f)
    print(f"📊 Total products to migrate: {total_lines}")
    
    # Upload in batches
    BATCH_SIZE = 100  # Smaller batches for REST API reliability
    points = []
    total_uploaded = 0
    batch_num = 0
    failed_batches = []
    
    print("\n⬆️  Uploading vectors...")
    
    with open(embeddings_path, 'r') as f:
        for idx, line in tqdm(enumerate(f), total=total_lines, desc="Migrating"):
            try:
                data = json.loads(line)
                
                # Create point in Qdrant format (matching actual JSONL structure)
                point = {
                    "id": idx,
                    "vector": data['embedding'],
                    "payload": {
                        # Core product identifiers
                        'product_part_number': data.get('product_part_number', ''),
                        'parent_product_part_number': data.get('parent_product_part_number', ''),
                        'product_name': data.get('product_name', ''),
                        
                        # Product details
                        'search_text': data.get('search_text', ''),
                        'product_link': data.get('product_link', ''),
                        'product_price_current': data.get('product_price_current', None),
                        
                        # Species flags for filtering
                        'species_dog_flag': data.get('species_dog_flag', False),
                        'species_cat_flag': data.get('species_cat_flag', False),
                        
                        # Additional flags
                        'product_autoship_save_eligible_flag': data.get('product_autoship_save_eligible_flag', False),
                        
                        # Metadata
                        'embedded_at': data.get('embedded_at', '')
                    }
                }
                points.append(point)
                
                # Upload batch when full
                if len(points) >= BATCH_SIZE:
                    batch_num += 1
                    if upload_batch(points, batch_num):
                        total_uploaded += len(points)
                    else:
                        failed_batches.append(batch_num)
                    points = []
                    
                    # Progress update every 50 batches
                    if batch_num % 50 == 0:
                        print(f"\n📊 Progress: {total_uploaded:,} vectors uploaded ({batch_num} batches)")
            
            except Exception as e:
                print(f"\n⚠️  Error processing line {idx}: {e}")
                continue
    
    # Upload remaining points
    if points:
        batch_num += 1
        if upload_batch(points, batch_num):
            total_uploaded += len(points)
        else:
            failed_batches.append(batch_num)
    
    print(f"\n✅ Migration complete!")
    print(f"   📊 Uploaded: {total_uploaded:,} vectors")
    print(f"   📦 Batches: {batch_num}")
    if failed_batches:
        print(f"   ⚠️  Failed batches: {len(failed_batches)}")
    
    # Wait for indexing
    print("\n⏳ Waiting for indexing to complete (30 seconds)...")
    time.sleep(30)
    
    # Check final status
    print("\n🔍 Checking collection status...")
    try:
        response = session.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", timeout=30)
        response.raise_for_status()
        collection_info = response.json()['result']
        
        print(f"\n🎉 Final stats:")
        print(f"   - Vectors indexed: {collection_info['points_count']:,}")
        print(f"   - Status: {collection_info['status']}")
        
        if collection_info['points_count'] == total_uploaded:
            print(f"\n✅ All {total_uploaded:,} vectors successfully migrated and indexed!")
        else:
            print(f"\n⚠️  Warning: Uploaded {total_uploaded:,} but indexed {collection_info['points_count']:,}")
    
    except Exception as e:
        print(f"⚠️  Could not verify collection status: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Migration complete! You can now enable Qdrant:")
    print("   1. Set USE_QDRANT=true in your .env file")
    print("   2. Restart your backend server")
    print("=" * 80)


if __name__ == "__main__":
    migrate_to_qdrant()

