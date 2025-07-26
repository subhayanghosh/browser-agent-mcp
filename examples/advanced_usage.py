#!/usr/bin/env python3
"""
Advanced Usage Example
Demonstrates advanced features of the Browser Agent MCP.
"""

import asyncio
import os
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.scrapers.zillow import main
from src.utils.stealth import StealthUtils


async def advanced_example():
    """Advanced example with custom configuration"""
    print("🚀 Advanced Zillow Scraping Example")
    print("=" * 45)

    # Custom configuration
    config = {
        'city': 'San Francisco, CA',
        'output': 'sf_properties.json',
        'max_properties': 15,
        'proxy': None,  # Set to proxy URL if needed
        'headless': False
    }

    print("Advanced Configuration:")
    print(f"  City: {config['city']}")
    print(f"  Output: {config['output']}")
    print(f"  Max Properties: {config['max_properties']}")
    print(f"  Proxy: {config['proxy'] or 'None'}")
    print(f"  Headless: {config['headless']}")
    print()

    # Set environment variables
    os.environ['ZILLOW_CITY'] = config['city']
    os.environ['ZILLOW_OUTPUT'] = config['output']
    os.environ['ZILLOW_MAX_PROPERTIES'] = str(config['max_properties'])
    if config['proxy']:
        os.environ['PROXY'] = config['proxy']
    if config['headless']:
        os.environ['HEADLESS'] = 'true'

    try:
        await main()

        # Read and display results
        if os.path.exists(config['output']):
            with open(config['output'], 'r') as f:
                results = json.load(f)

            print(f"\n📊 Results Summary:")
            print(f"  Total Properties: {len(results)}")

            if results:
                print(f"\n📋 Sample Properties:")
                for i, prop in enumerate(results[:3]):
                    print(f"  {i+1}. {prop.get('title', 'N/A')[:50]}...")
                    print(f"     Price: {prop.get('price', 'N/A')}")
                    print(
                        f"     Beds: {prop.get('beds', 'N/A')} | Baths: {prop.get('baths', 'N/A')}")
                    print()

        print("✅ Advanced scraping completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(advanced_example())
