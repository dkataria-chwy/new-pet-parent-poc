"""
Migration script to upload 117K product embeddings from JSONL to Qdrant.

This script handles the one-time migration of embeddings to Qdrant cloud,
optimized for large datasets with batching and progress tracking.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, OptimizersConfigDiff
import json
from pathlib import Path
import os
from dotenv import load_dotenv
from tqdm import tqdm
import time
import httpx

# Load environment variables
load_dotenv()

# Qdrant credentials
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "chewy_products_117k"

def migrate_to_qdrant():
    """Migrate 117K embeddings to Qdrant with optimized batching."""
    
    print("🚀 Starting Qdrant migration for 117K products...")
    
    # Initialize Qdrant client with extended timeout and custom httpx client
    print("   Initializing Qdrant client (this may take 30-60 seconds)...")
    
    # Create custom httpx client with longer timeouts
    http_client = httpx.Client(
        timeout=httpx.Timeout(
            connect=60.0,  # 60 seconds to establish connection
            read=180.0,    # 3 minutes to read response
            write=180.0,   # 3 minutes to write request
            pool=10.0      # 10 seconds for connection pool
        ),
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20
        )
    )
    
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=180,  # 3 minutes overall timeout
        prefer_grpc=False,  # Use REST API instead of gRPC
        https=http_client if QDRANT_URL.startswith('https') else None
    )
    print(f"✅ Connected to Qdrant at {QDRANT_URL}")
    
    # Try to create collection (if it exists, we'll handle the error)
    print(f"📦 Checking if collection '{COLLECTION_NAME}' exists...")
    try:
        collection_info = client.get_collection(collection_name=COLLECTION_NAME)
        print(f"⚠️  Collection '{COLLECTION_NAME}' already exists with {collection_info.points_count} vectors.")
        response = input("Do you want to recreate it? This will delete all existing data. (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Migration cancelled.")
            return
        
        print(f"🗑️  Deleting existing collection...")
        client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"✅ Deleted existing collection: {COLLECTION_NAME}")
        time.sleep(2)  # Wait for deletion to complete
    except Exception as e:
        # Collection doesn't exist, which is fine
        if "Not found" in str(e) or "not found" in str(e).lower():
            print(f"✅ Collection doesn't exist yet - will create new one")
        else:
            print(f"⚠️  Could not check collection status: {e}")
            print(f"   Proceeding with creation anyway...")
    
    # Create collection with optimized settings for 117K vectors
    print(f"📦 Creating collection: {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1536,  # OpenAI embedding dimension
            distance=Distance.COSINE,
        ),
        # Optimize for large dataset
        hnsw_config={
            "m": 16,  # Number of edges per node (balance between speed and memory)
            "ef_construct": 100,  # Construction time accuracy
        },
        optimizers_config=OptimizersConfigDiff(
            indexing_threshold=20000,  # Start indexing after 20K vectors
        )
    )
    print(f"✅ Created optimized collection: {COLLECTION_NAME}")
    
    # Load embeddings from JSONL
    embeddings_path = Path(__file__).parent / "artifacts" / "catalog_embeds.jsonl"
    
    if not embeddings_path.exists():
        print(f"❌ Error: Embeddings file not found at {embeddings_path}")
        return
    
    print(f"📂 Loading embeddings from: {embeddings_path}")
    
    # Count total lines for progress bar
    with open(embeddings_path, 'r') as f:
        total_lines = sum(1 for _ in f)
    print(f"📊 Total products to migrate: {total_lines}")
    
    # Upload in batches
    BATCH_SIZE = 500  # Larger batches for 117K dataset
    points = []
    total_uploaded = 0
    batch_num = 0
    
    with open(embeddings_path, 'r') as f:
        for idx, line in tqdm(enumerate(f), total=total_lines, desc="Migrating vectors"):
            try:
                data = json.loads(line)
                
                # Create point with all metadata
                point = PointStruct(
                    id=idx,
                    vector=data['embedding'],
                    payload={
                        'product_id': data.get('product_id', f"prod_{idx}"),
                        'product_name': data.get('product_name', ''),
                        'description': data.get('description', ''),
                        'species': data.get('species', ''),
                        'category': data.get('category', ''),
                        'subcategory': data.get('subcategory', ''),
                        'price': data.get('price', 0.0),
                        'brand': data.get('brand', ''),
                        'image_url': data.get('image_url', ''),
                        'product_url': data.get('product_url', ''),
                        # Add any other metadata fields
                    }
                )
                points.append(point)
                
                # Upload batch when full
                if len(points) >= BATCH_SIZE:
                    batch_num += 1
                    client.upsert(
                        collection_name=COLLECTION_NAME,
                        points=points,
                        wait=False  # Async upload for speed
                    )
                    total_uploaded += len(points)
                    points = []
                    
                    # Periodic status update
                    if batch_num % 10 == 0:
                        print(f"\n📦 Uploaded {total_uploaded} vectors ({batch_num} batches)...")
            
            except Exception as e:
                print(f"\n⚠️  Error processing line {idx}: {e}")
                continue
    
    # Upload remaining points
    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        total_uploaded += len(points)
    
    print(f"\n✅ Migration complete! Uploaded {total_uploaded} vectors")
    
    # Wait for indexing to complete
    print("\n⏳ Waiting for indexing to complete (this may take a few minutes)...")
    time.sleep(30)  # Initial wait
    
    # Check collection status
    max_retries = 20
    for i in range(max_retries):
        collection_info = client.get_collection(collection_name=COLLECTION_NAME)
        print(f"📊 Collection status: {collection_info.points_count} vectors indexed, "
              f"Status: {collection_info.status}")
        
        if collection_info.status == "green":
            break
        
        time.sleep(10)
    
    # Final verification
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    print(f"\n🎉 Final stats:")
    print(f"   - Vectors indexed: {collection_info.points_count}")
    print(f"   - Collection status: {collection_info.status}")
    print(f"   - Total uploaded: {total_uploaded}")
    
    if collection_info.points_count == total_uploaded:
        print("\n✅ All vectors successfully migrated and indexed!")
    else:
        print(f"\n⚠️  Warning: Mismatch between uploaded ({total_uploaded}) "
              f"and indexed ({collection_info.points_count}) vectors")


if __name__ == "__main__":
    migrate_to_qdrant()

