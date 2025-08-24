#!/usr/bin/env python3
"""
MongoDB Connection Troubleshooter
Run this script to test and fix MongoDB connection issues
"""

import os
import ssl
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB connection with different configurations"""
    
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("❌ MONGODB_URI not found in environment variables")
        print("Please set MONGODB_URI in your .env file")
        return False
    
    print(f"🔍 Testing MongoDB connection...")
    print(f"URI: {mongodb_uri[:50]}..." if len(mongodb_uri) > 50 else f"URI: {mongodb_uri}")
    
    try:
        from pymongo import MongoClient
        
        # Test 1: Basic connection
        print("\n1️⃣ Testing basic connection...")
        try:
            client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            print("✅ Basic connection successful")
            client.close()
            return True
        except Exception as e:
            print(f"❌ Basic connection failed: {e}")
        
        # Test 2: Connection with SSL options
        print("\n2️⃣ Testing with SSL options...")
        try:
            ssl_options = {
                'ssl': True,
                'ssl_cert_reqs': ssl.CERT_NONE,
                'tlsAllowInvalidCertificates': True,
                'serverSelectionTimeoutMS': 5000,
                'connectTimeoutMS': 10000
            }
            
            client = MongoClient(mongodb_uri, **ssl_options)
            client.admin.command('ping')
            print("✅ SSL connection successful")
            client.close()
            return True
        except Exception as e:
            print(f"❌ SSL connection failed: {e}")
        
        # Test 3: Alternative SSL configuration
        print("\n3️⃣ Testing alternative SSL configuration...")
        try:
            alt_ssl_options = {
                'tls': True,
                'tlsInsecure': True,
                'serverSelectionTimeoutMS': 5000
            }
            
            client = MongoClient(mongodb_uri, **alt_ssl_options)
            client.admin.command('ping')
            print("✅ Alternative SSL connection successful")
            client.close()
            return True
        except Exception as e:
            print(f"❌ Alternative SSL connection failed: {e}")
        
        return False
        
    except ImportError:
        print("❌ pymongo not installed. Run: pip install pymongo[srv]")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def suggest_fixes():
    """Suggest potential fixes for MongoDB connection issues"""
    print("\n🔧 Suggested Fixes:")
    print("1. Update pymongo: pip install --upgrade 'pymongo[srv]'")
    print("2. Install certificates: pip install --upgrade certifi")
    print("3. Check your MongoDB Atlas connection string format:")
    print("   mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority")
    print("4. Verify your IP is whitelisted in MongoDB Atlas Network Access")
    print("5. Check if your firewall/antivirus is blocking the connection")
    print("6. Try using a different network (mobile hotspot) to test connectivity")

def create_fixed_env():
    """Create a sample .env file with proper MongoDB configuration"""
    sample_env = """# MongoDB Configuration (Update with your actual values)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/teaching_assistant?retryWrites=true&w=majority&ssl=true
MONGODB_DB_NAME=teaching_assistant

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# App Configuration  
SECRET_KEY=your_secure_secret_key_here
"""
    
    with open('.env.example.fixed', 'w') as f:
        f.write(sample_env)
    
    print("\n📝 Created .env.example.fixed with proper MongoDB format")
    print("Copy this to your .env file and update with your actual credentials")

if __name__ == "__main__":
    print("🔍 MongoDB Connection Troubleshooter")
    print("=" * 50)
    
    success = test_mongodb_connection()
    
    if not success:
        suggest_fixes()
        create_fixed_env()
    else:
        print("\n🎉 MongoDB connection is working!")
    
    print("\n" + "=" * 50)
    print("Run this script again after making changes to test the connection")
