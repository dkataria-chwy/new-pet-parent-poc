"""
Simple script to test Qdrant connection and diagnose issues.
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("🔍 Qdrant Connection Test")
print("=" * 80)

# Check environment variables
print("\n1️⃣ Checking environment variables...")
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_cluster_id = os.getenv("QDRANT_CLUSTER_ID")

print(f"   QDRANT_URL: {qdrant_url}")
print(f"   QDRANT_API_KEY: {'*' * 10}...{qdrant_api_key[-10:] if qdrant_api_key else 'NOT SET'}")
print(f"   QDRANT_CLUSTER_ID: {qdrant_cluster_id}")

if not qdrant_url or not qdrant_api_key:
    print("\n❌ Error: QDRANT_URL or QDRANT_API_KEY not set in .env")
    exit(1)

print("\n✅ Environment variables are set")

# Try to import qdrant_client
print("\n2️⃣ Checking qdrant-client installation...")
try:
    from qdrant_client import QdrantClient
    print("   ✅ qdrant-client is installed")
except ImportError:
    print("   ❌ qdrant-client not installed")
    print("   Run: pip install qdrant-client")
    exit(1)

# Try to connect with increased timeout
print("\n3️⃣ Testing connection to Qdrant cloud...")
print(f"   Connecting to: {qdrant_url}")
print("   (This may take 30-60 seconds...)")

try:
    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        timeout=60  # Increased timeout
    )
    print("   ✅ Client initialized")
    
    print("\n4️⃣ Fetching collections...")
    collections = client.get_collections()
    
    print(f"   ✅ Connected successfully!")
    print(f"   📊 Found {len(collections.collections)} existing collection(s):")
    for col in collections.collections:
        print(f"      - {col.name} ({col.vectors_count} vectors)")
    
    print("\n" + "=" * 80)
    print("✅ SUCCESS - Qdrant connection is working!")
    print("=" * 80)
    print("\nYou can now run the migration script:")
    print("   python migrate_to_qdrant.py")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n" + "=" * 80)
    print("🔧 TROUBLESHOOTING STEPS:")
    print("=" * 80)
    print("\n1. Verify your Qdrant cluster is running:")
    print("   - Go to https://cloud.qdrant.io/")
    print("   - Log in to your account")
    print("   - Check if your cluster is 'Active' (not paused)")
    print(f"   - Cluster ID should be: {qdrant_cluster_id}")
    
    print("\n2. Verify the cluster URL:")
    print(f"   - Current URL: {qdrant_url}")
    print("   - Format should be: https://<cluster-id>.<region>.aws.cloud.qdrant.io")
    print("   - Check if the region matches your cluster's region")
    
    print("\n3. Verify API credentials:")
    print("   - Go to your cluster in Qdrant cloud console")
    print("   - Navigate to 'API Keys' section")
    print("   - Verify the API key matches what's in your .env file")
    
    print("\n4. If cluster doesn't exist, create one:")
    print("   - Go to https://cloud.qdrant.io/")
    print("   - Click 'Create Cluster'")
    print("   - Choose a region (e.g., us-east-1)")
    print("   - Select a plan (Free tier is fine for testing)")
    print("   - Wait for cluster to be 'Active' (may take 2-5 minutes)")
    print("   - Copy the cluster URL and API key to your .env file")
    
    print("\n5. Check network connectivity:")
    print("   - Verify you can access cloud.qdrant.io in a browser")
    print("   - Check if any firewall/VPN is blocking the connection")
    
    print("\n" + "=" * 80)
    exit(1)

