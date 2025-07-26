#!/usr/bin/env python3
"""
Advanced AI Agent Test Script for Zillow Scraping
This script tests the full agent mode with stealth capabilities and challenge solving.
"""

import asyncio
import os
import sys
from src.scrapers.zillow import main


async def test_agent():
    """Test the enhanced AI agent"""
    print("🤖 Starting Advanced AI Agent Test")
    print("=" * 50)

    # Set environment variables for testing
    os.environ['ZILLOW_CITY'] = 'Austin, TX'
    os.environ['ZILLOW_OUTPUT'] = 'test_results.json'

    print("📋 Configuration:")
    print(f"   City: {os.environ['ZILLOW_CITY']}")
    print(f"   Output: {os.environ['ZILLOW_OUTPUT']}")
    print(f"   Stealth Mode: Enabled")
    print(f"   AI Challenge Solver: Enabled")
    print(f"   Retry Logic: Enabled")
    print()

    try:
        await main()
        print("✅ Agent test completed successfully!")

        # Check if results were saved
        if os.path.exists('test_results.json'):
            import json
            with open('test_results.json', 'r') as f:
                results = json.load(f)
            print(f"📊 Collected {len(results)} properties")
        else:
            print("⚠️  No results file found")

    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    print("🚀 Launching Advanced AI Agent...")
    success = asyncio.run(test_agent())

    if success:
        print("\n🎉 Agent test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Agent test failed!")
        sys.exit(1)
