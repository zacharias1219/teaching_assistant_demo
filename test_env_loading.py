#!/usr/bin/env python3
import os
from dotenv import load_dotenv

print("🔍 Testing Environment Variable Loading")
print("=" * 50)

# Load environment variables
load_dotenv()

# Test OpenAI API Key
api_key = os.getenv('OPENAI_API_KEY')
print(f"📋 OPENAI_API_KEY loaded: {'✅ Yes' if api_key else '❌ No'}")
if api_key:
    print(f"   Length: {len(api_key)} characters")
    print(f"   Starts with: {api_key[:10]}..." if len(api_key) > 10 else f"   Full key: {api_key}")
    print(f"   Ends with: ...{api_key[-4:]}" if len(api_key) > 10 else "")
else:
    print("   ❌ API key not found!")

# Check if .env file exists
import pathlib
env_file = pathlib.Path('.env')
print(f"\n📋 .env file exists: {'✅ Yes' if env_file.exists() else '❌ No'}")
if env_file.exists():
    print(f"   Size: {env_file.stat().st_size} bytes")

# Test other environment variables
print(f"\n📋 Other environment variables:")
print(f"   DATABASE_PATH: {os.getenv('DATABASE_PATH', 'Not set (using default)')}")
print(f"   SECRET_KEY: {'✅ Set' if os.getenv('SECRET_KEY') else '❌ Not set'}")

print("\n" + "=" * 50)
print("💡 Next steps:")
print("1. Make sure .env file exists in the project root")
print("2. Add this line to .env file:")
print("   OPENAI_API_KEY=your_actual_api_key_here")
print("3. Restart the Streamlit app")
