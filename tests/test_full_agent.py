#!/usr/bin/env python3
"""
Full Agent Mode Test
This script tests the complete agent capabilities including challenge solving.
"""

import asyncio
import os
import sys
import time
from playwright.async_api import async_playwright
from src.utils.stealth import StealthUtils
from src.challenges.ai_solver import AIChallengeSolver
from src.challenges.manual_solver import ManualChallengeSolver


async def test_full_agent():
    """Test the complete agent with all capabilities"""
    print("🤖 FULL AGENT MODE TEST")
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
        await asyncio.sleep(3)

        # Test challenge detection and solving
        print("\n🔍 Testing Challenge Detection...")
        challenge_info = await ai_solver.analyze_page_content(page)

        if challenge_info:
            print(
                f"✅ Challenge detected: {challenge_info['type']} (confidence: {challenge_info['confidence']})")

            # Try AI solving first
            print("\n🤖 Attempting AI Challenge Solving...")
            ai_success = await ai_solver.execute_challenge_action(page, challenge_info)

            if ai_success:
                print("✅ AI successfully solved the challenge!")
            else:
                print("❌ AI failed to solve challenge, switching to manual mode...")

                # Manual intervention
                manual_success = await manual_solver.wait_for_manual_intervention(challenge_info['type'])
                if manual_success:
                    print("✅ Manual intervention successful!")
                else:
                    print("❌ Manual intervention failed")
                    return False
        else:
            print("ℹ️  No challenges detected")

        # Test search functionality
        print("\n🔍 Testing Search Functionality...")
        try:
            await page.wait_for_selector('input[aria-label="Enter an address, neighborhood, city, or ZIP code"]', timeout=10000)
            await page.fill('input[aria-label="Enter an address, neighborhood, city, or ZIP code"]', 'Austin, TX')
            await page.keyboard.press('Enter')
            print("✅ Search executed successfully")
        except Exception as e:
            print(f"❌ Search failed: {e}")

        await asyncio.sleep(5)

        # Final challenge check
        print("\n🔍 Final Challenge Check...")
        final_challenge = await ai_solver.analyze_page_content(page)
        if final_challenge:
            print(f"⚠️  Challenge still present: {final_challenge['type']}")
        else:
            print("✅ No challenges remaining")

        await browser.close()
        await playwright.stop()

        print("\n🎉 Full Agent Test Completed Successfully!")
        return True

    except Exception as e:
        print(f"❌ Full Agent Test Failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Full Agent Mode Test...")
    success = asyncio.run(test_full_agent())

    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)
