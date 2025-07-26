#!/usr/bin/env python3
"""
Basic Usage Example
Demonstrates how to use the Browser Agent MCP for Zillow scraping.
"""

import asyncio
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.scrapers.zillow import main


async def basic_example():
    """Basic example of using the Zillow scraper"""
    print("🏠 Basic Zillow Scraping Example")
    print("=" * 40)

    # Set configuration
    os.environ['ZILLOW_CITY'] = 'Austin, TX'
    os.environ['ZILLOW_OUTPUT'] = 'example_results.json'
    os.environ['ZILLOW_MAX_PROPERTIES'] = '10'

    print("Configuration:")
    print(f"  City: {os.environ['ZILLOW_CITY']}")
    print(f"  Output: {os.environ['ZILLOW_OUTPUT']}")
    print(f"  Max Properties: {os.environ['ZILLOW_MAX_PROPERTIES']}")
    print()

    try:
        await main()
        print("✅ Scraping completed successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(basic_example())
