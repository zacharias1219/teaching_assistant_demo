#!/usr/bin/env python3
"""
Simple OpenAI API Key Tester
Run this to verify your OpenAI API key is working
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_key():
    """Test OpenAI API key"""
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No OPENAI_API_KEY found in .env file")
        print("💡 Add OPENAI_API_KEY=your_key_here to your .env file")
        return False
    
    if api_key == "your_openai_api_key_here":
        print("❌ Please replace 'your_openai_api_key_here' with your actual API key")
        return False
    
    print(f"🔍 Testing API key: {api_key[:10]}...")
    print(f"🔍 Full key length: {len(api_key)} characters")
    print(f"🔍 Key starts with: {api_key[:20]}...")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        
        print("✅ OpenAI API key is working!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API key test failed: {e}")
        
        if "401" in str(e) or "Incorrect API key" in str(e):
            print("\n💡 Solutions:")
            print("1. Go to https://platform.openai.com/account/api-keys")
            print("2. Create a new API key")
            print("3. Update your .env file with the new key")
            print("4. Make sure you have credits/billing set up in OpenAI")
        
        return False

if __name__ == "__main__":
    print("🔑 OpenAI API Key Tester")
    print("=" * 40)
    test_openai_key()
    print("=" * 40)
