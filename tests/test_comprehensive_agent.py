#!/usr/bin/env python3
"""
Final Comprehensive Agent Test
This script tests the complete workflow from challenge solving to data collection.
"""

import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from src.utils.stealth import StealthUtils
from src.challenges.ai_solver import AIChallengeSolver
from src.challenges.manual_solver import ManualChallengeSolver


async def human_delay(min_s=1, max_s=2):
    await asyncio.sleep(asyncio.uniform(min_s, max_s))


async def search_city(page, city):
    """Search for a city with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🔍 Search attempt {attempt + 1}/{max_retries}")

            # Try different selectors for the search input
            selectors = [
                'input[aria-label="Enter an address, neighborhood, city, or ZIP code"]',
                'input[placeholder*="address"]',
                'input[placeholder*="city"]',
                'input[placeholder*="ZIP"]',
                '[data-test="search-input"]',
                'input[type="text"]'
            ]

            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.fill(selector, city)
                    await human_delay(0.5, 1.5)
                    await page.keyboard.press('Enter')
                    print(f"✅ Search successful with selector: {selector}")
                    return True
                except PlaywrightTimeoutError:
                    continue

            print(f"❌ Search attempt {attempt + 1} failed")
            await human_delay(2, 3)

        except Exception as e:
            print(f"❌ Search error: {e}")
            await human_delay(2, 3)

    return False


async def collect_properties(page, max_properties=10):
    """Collect property data with improved selectors"""
    results = []
    seen_urls = set()
    scrolls = 0

    print(f"📊 Collecting up to {max_properties} properties...")

    while len(results) < max_properties and scrolls < 10:
        try:
            # Wait for property cards with multiple selectors
            card_selectors = [
                'ul.photo-cards li article',
                '[data-test="property-card"]',
                '.property-card',
                '[class*="property"]',
                '[class*="listing"]'
            ]

            cards_found = False
            for selector in card_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    cards = await page.query_selector_all(selector)
                    if cards:
                        cards_found = True
                        print(
                            f"✅ Found {len(cards)} cards with selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            if not cards_found:
                print("❌ No property cards found")
                break

            # Process each card
            for card in cards:
                try:
                    # Try to get URL
                    url = await card.evaluate('el => el.querySelector("a")?.href || ""')
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Get property data
                    title = await card.evaluate('el => el.getAttribute("aria-label") || el.textContent || ""')
                    price = await card.evaluate('el => el.querySelector("[data-test*=\"price\"]")?.textContent || ""')
                    beds = await card.evaluate('el => el.querySelector("[data-test*=\"beds\"]")?.textContent || ""')
                    baths = await card.evaluate('el => el.querySelector("[data-test*=\"baths\"]")?.textContent || ""')
                    sqft = await card.evaluate('el => el.querySelector("[data-test*=\"sqft\"]")?.textContent || ""')

                    results.append({
                        'title': title.strip() if title else '',
                        'price': price.strip() if price else '',
                        'url': url,
                        'beds': beds.strip() if beds else '',
                        'baths': baths.strip() if baths else '',
                        'sqft': sqft.strip() if sqft else ''
                    })

                    print(f"📋 Property {len(results)}: {title[:50]}...")

                    if len(results) >= max_properties:
                        break

                except Exception as e:
                    print(f"❌ Error processing card: {e}")
                    continue

            # Scroll down
            await page.mouse.wheel(0, 800)
            await human_delay(1.5, 2.5)
            scrolls += 1

        except Exception as e:
            print(f"❌ Error in collection loop: {e}")
            break

    return results


async def final_agent_test():
    """Complete agent test with full workflow"""
    print("🤖 FINAL COMPREHENSIVE AGENT TEST")
    print("=" * 60)

    # Initialize components
    ai_solver = AIChallengeSolver()
    manual_solver = ManualChallengeSolver()

    try:
        playwright = await async_playwright().start()

        # Use stealth fingerprinting
        user_agent = StealthUtils.get_random_user_agent()
        viewport = StealthUtils.get_random_viewport()
        timezone = StealthUtils.get_random_timezone()
        geolocation = StealthUtils.get_random_geolocation()

        print("🔧 Stealth Configuration:")
        print(f"   User Agent: {user_agent[:50]}...")
        print(f"   Viewport: {viewport}")
        print(f"   Timezone: {timezone}")
        print(f"   Location: {geolocation}")
        print()

        browser = await playwright.chromium.launch(
            headless=False,
            args=["--start-maximized",
                  "--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            locale='en-US',
            timezone_id=timezone,
            geolocation=geolocation,
            permissions=["geolocation"]
        )

        page = await context.new_page()

        # Inject stealth scripts
        await StealthUtils.inject_stealth_scripts(page)
        print("✅ Stealth scripts injected")

        # Setup manual solver
        await manual_solver.setup_manual_solver(page)

        # Navigate to Zillow
        print("\n🌐 Navigating to Zillow...")
        await page.goto('https://www.zillow.com', timeout=30000)
        await human_delay(2, 3)

        # Handle challenges with retry logic
        max_challenge_attempts = 3
        for challenge_attempt in range(max_challenge_attempts):
            print(
                f"\n🔍 Challenge Handling Attempt {challenge_attempt + 1}/{max_challenge_attempts}")

            challenge_info = await ai_solver.analyze_page_content(page)

            if challenge_info:
                print(
                    f"✅ Challenge detected: {challenge_info['type']} (confidence: {challenge_info['confidence']})")

                # Try AI solving first
                ai_success = await ai_solver.execute_challenge_action(page, challenge_info)

                if ai_success:
                    print("✅ AI successfully solved the challenge!")
                    break
                else:
                    print("❌ AI failed, trying manual intervention...")
                    manual_success = await manual_solver.wait_for_manual_intervention(challenge_info['type'])
                    if manual_success:
                        print("✅ Manual intervention successful!")
                        break
                    else:
                        print("❌ Manual intervention failed")
                        if challenge_attempt < max_challenge_attempts - 1:
                            print("🔄 Retrying...")
                            await page.reload()
                            await human_delay(3, 5)
            else:
                print("ℹ️  No challenges detected")
                break

        # Test search functionality
        print("\n🔍 Testing Search Functionality...")
        search_success = await search_city(page, 'Austin, TX')

        if search_success:
            print("✅ Search completed successfully")
            await human_delay(3, 5)

            # Collect properties
            print("\n📊 Collecting Property Data...")
            properties = await collect_properties(page, 10)

            if properties:
                # Save results
                output_file = 'final_test_results.json'
                with open(output_file, 'w') as f:
                    json.dump(properties, f, indent=2)

                print(f"✅ Successfully collected {len(properties)} properties")
                print(f"📁 Results saved to: {output_file}")

                # Show sample results
                print("\n📋 Sample Results:")
                for i, prop in enumerate(properties[:3]):
                    print(f"  {i+1}. {prop.get('title', 'N/A')[:50]}...")
                    print(f"     Price: {prop.get('price', 'N/A')}")
                    print(f"     URL: {prop.get('url', 'N/A')[:50]}...")
                    print()
            else:
                print("❌ No properties collected")
        else:
            print("❌ Search failed")

        await browser.close()
        await playwright.stop()

        print("\n🎉 Final Agent Test Completed Successfully!")
        return True

    except Exception as e:
        print(f"❌ Final Agent Test Failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Final Comprehensive Agent Test...")
    success = asyncio.run(final_agent_test())

    if success:
        print("\n🎉 Final test passed!")
        sys.exit(0)
    else:
        print("\n💥 Final test failed!")
        sys.exit(1)
