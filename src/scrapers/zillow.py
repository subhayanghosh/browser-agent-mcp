import asyncio
import json
import os
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from src.challenges.ai_solver import AIChallengeSolver
from src.utils.stealth import StealthUtils
from src.challenges.manual_solver import ManualChallengeSolver

# Configurable city and output file
CITY = os.getenv('ZILLOW_CITY', 'Austin, TX')
OUTPUT_FILE = os.getenv('ZILLOW_OUTPUT', 'zillow_results.json')
PROXY = os.getenv('PROXY')  # e.g. 'http://user:pass@host:port'

# Use stealth utilities for random fingerprinting
USER_AGENT = os.getenv('USER_AGENT', StealthUtils.get_random_user_agent())
VIEWPORT = StealthUtils.get_random_viewport()
LOCALE = os.getenv('LOCALE', 'en-US')
TIMEZONE = os.getenv('TIMEZONE', StealthUtils.get_random_timezone())
GEOLOCATION = StealthUtils.get_random_geolocation()


async def human_delay(min_s=1, max_s=2):
    await asyncio.sleep(random.uniform(min_s, max_s))


async def handle_challenges_with_ai(page, ai_solver):
    """Use AI to detect and handle various types of challenges"""
    try:
        print("[AI] Analyzing page for challenges...")

        # Analyze the page content
        challenge_info = await ai_solver.analyze_page_content(page)

        if challenge_info:
            print(
                f"[AI] Detected challenge type: {challenge_info['type']} (confidence: {challenge_info['confidence']})")

            # Execute the appropriate action
            success = await ai_solver.execute_challenge_action(page, challenge_info)

            if success:
                print("[AI] Challenge handled successfully")
                await human_delay(2, 3)
                return True
            else:
                print("[AI] Failed to handle challenge automatically")
                return False
        else:
            print("[AI] No challenges detected")
            return True

    except Exception as e:
        print(f"[AI] Error in AI challenge handling: {e}")
        return False


async def accept_cookies_or_modals(page):
    # Try to accept cookies or close modals if present
    try:
        # Zillow cookie banner
        await page.wait_for_selector('button:has-text("Accept")', timeout=4000)
        await page.click('button:has-text("Accept")')
        await human_delay(0.5, 1.2)
    except PlaywrightTimeoutError:
        pass

    # Try to close any other popups/modals
    try:
        await page.click('button[aria-label="Close"]', timeout=2000)
        await human_delay(0.5, 1.2)
    except PlaywrightTimeoutError:
        pass


async def handle_listing_type_modal(page):
    """Handle the 'For Sale' vs 'For Rent' modal that appears after search"""
    try:
        print("🔍 Checking for listing type modal...")

        # Wait for the modal to appear
        await page.wait_for_selector('text="What type of listings would you like to see?"', timeout=5000)
        print("✅ Found listing type modal")

        # Look for "For sale" button and click it
        sale_selectors = [
            'button:has-text("For sale")',
            'button:has-text("For Sale")',
            '[data-test="for-sale-button"]',
            'a:has-text("For sale")',
            'a:has-text("For Sale")'
        ]

        for selector in sale_selectors:
            try:
                await page.wait_for_selector(selector, timeout=2000)
                await page.click(selector)
                print(f"✅ Clicked 'For Sale' with selector: {selector}")
                await human_delay(2, 3)
                return True
            except PlaywrightTimeoutError:
                continue

        print("❌ Could not find 'For Sale' button")
        return False

    except PlaywrightTimeoutError:
        print("ℹ️  No listing type modal found")
        return True
    except Exception as e:
        print(f"❌ Error handling listing type modal: {e}")
        return False


async def search_city(page, city):
    """Search for a city with improved selectors and retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🔍 Search attempt {attempt + 1}/{max_retries}")

            # Wait for page to be ready after challenge solving
            await human_delay(2, 3)

            # Try multiple selectors for the search input
            selectors = [
                'input[aria-label="Enter an address, neighborhood, city, or ZIP code"]',
                'input[placeholder*="address"]',
                'input[placeholder*="city"]',
                'input[placeholder*="ZIP"]',
                '[data-test="search-input"]',
                'input[type="text"]',
                'input[class*="search"]',
                'input[class*="input"]'
            ]

            search_input = None
            for selector in selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=5000)
                    if search_input:
                        print(
                            f"✅ Found search input with selector: {selector}")
                        break
                except:
                    continue

            if not search_input:
                print(
                    f"❌ Search attempt {attempt + 1} failed - no input found")
                # Try refreshing the page
                if attempt < max_retries - 1:
                    print("🔄 Refreshing page and retrying...")
                    await page.reload()
                    await human_delay(3, 5)
                continue

            # Clear the input and fill with city
            await search_input.click()
            await search_input.fill('')
            await human_delay(0.5, 1)
            await search_input.fill(city)
            await human_delay(0.5, 1.5)

            # Press Enter to search
            await page.keyboard.press('Enter')
            print(f"✅ Search successful for: {city}")
            await human_delay(3, 5)
            return True

        except Exception as e:
            print(f"❌ Search attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await human_delay(2, 3)

    print("❌ All search attempts failed")
    return False


async def collect_properties(page, max_properties=20):
    """Collect property information from the search results"""
    try:
        print(f"📊 Collecting up to {max_properties} properties...")

        # Wait for property cards to load
        await human_delay(3, 5)

        # Try multiple selectors for property cards
        card_selectors = [
            '[data-test="property-card"]',
            '[data-test*="property"]',
            '[class*="property-card"]',
            '[class*="listing"]',
            'article',
            '[role="article"]',
            'div[class*="card"]'
        ]

        cards = []
        for selector in card_selectors:
            try:
                cards = await page.query_selector_all(selector)
                if cards:
                    print(
                        f"✅ Found {len(cards)} cards with selector: {selector}")
                    break
            except:
                continue

        if not cards:
            # Fallback: look for any elements that might be property cards
            try:
                all_elements = await page.query_selector_all('div, article')
                cards = []
                for element in all_elements:
                    try:
                        text = await element.evaluate('el => el.textContent || ""')
                        if any(keyword in text.lower() for keyword in ['$', 'bds', 'ba', 'sqft', 'bed', 'bath']):
                            cards.append(element)
                    except:
                        continue
                print(
                    f"✅ Found {len(cards)} potential cards via text analysis")
            except:
                pass

        if not cards:
            print("❌ No property cards found")
            # Take debug screenshot
            await page.screenshot(path="debug_no_cards_1.png")
            return []

        results = []
        cards_to_process = min(len(cards), max_properties)

        print(f"🔍 Processing {cards_to_process} property cards...")

        for i, card in enumerate(cards[:cards_to_process]):
            try:
                # Extract property information
                title = await card.evaluate('el => el.getAttribute("aria-label") ? el.getAttribute("aria-label") : (el.textContent ? el.textContent : "")')

                # Extract data from title text using regex patterns
                import re

                # Extract price (look for $XXX,XXX pattern)
                price_match = re.search(r'\$([0-9,]+)', title)
                price = price_match.group(0) if price_match else ""

                # Extract beds (look for "X bds" pattern)
                beds_match = re.search(r'(\d+)\s*bds', title)
                beds = beds_match.group(1) + " bds" if beds_match else ""

                # Extract baths (look for "X ba" pattern)
                baths_match = re.search(r'(\d+)\s*ba', title)
                baths = baths_match.group(1) + " ba" if baths_match else ""

                # Extract sqft (look for "X,XXX sqft" pattern)
                sqft_match = re.search(r'([0-9,]+)\s*sqft', title)
                sqft = sqft_match.group(1) + " sqft" if sqft_match else ""

                # Clean up title (remove extra text after address)
                title_clean = re.sub(
                    r'(.*?)(?:COMPASS|SPROUT|COLDWELL|REALTY|LLC|\$[0-9,]+).*', r'\1', title)
                title_clean = title_clean.strip()

                # Get URL
                url = await card.evaluate('el => el.querySelector("a") ? el.querySelector("a").href : ""')

                # Only add if we have meaningful data
                if title_clean and (price or beds or baths):
                    results.append({
                        'title': title_clean,
                        'price': price,
                        'url': url,
                        'beds': beds,
                        'baths': baths,
                        'sqft': sqft
                    })
                    print(f"✅ Property {i+1}: {title_clean[:50]}...")

            except Exception as e:
                print(f"❌ Error processing card {i+1}: {e}")
                continue

        print(f"📊 Successfully collected {len(results)} properties")
        return results

    except Exception as e:
        print(f"❌ Error collecting properties: {e}")
        return []


async def main():
    try:
        # Initialize AI challenge solver
        ai_solver = AIChallengeSolver()

        playwright = await async_playwright().start()
        browser_args = {}
        if PROXY:
            browser_args['proxy'] = {"server": PROXY}
        browser = await playwright.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(
            viewport=VIEWPORT,
            user_agent=USER_AGENT,
            locale=LOCALE,
            timezone_id=TIMEZONE,
            geolocation=GEOLOCATION,
            permissions=["geolocation"]
        )
        page = await context.new_page()

        # Inject stealth scripts to mask automation
        await StealthUtils.inject_stealth_scripts(page)

        # Navigate to Zillow
        await page.goto('https://www.zillow.com', timeout=30000)
        await human_delay(2, 3)

        # Initialize manual solver
        manual_solver = ManualChallengeSolver()
        await manual_solver.setup_manual_solver(page)

        # Handle any challenges with AI
        challenge_success = await handle_challenges_with_ai(page, ai_solver)
        if not challenge_success:
            print("[!] AI failed to handle challenges, switching to manual mode...")
            await accept_cookies_or_modals(page)

            # Use manual solver
            manual_success = await manual_solver.wait_for_manual_intervention("Press & Hold")
            if not manual_success:
                print("[!] Manual intervention failed or skipped")
                return

                # Search for the city
        search_success = await search_city(page, CITY)
        if not search_success:
            print("❌ Search failed, cannot proceed with scraping")
            return

        await human_delay(3, 5)

        # Check for additional challenges after search
        await handle_challenges_with_ai(page, ai_solver)

        # Handle "For Sale" vs "For Rent" modal
        await handle_listing_type_modal(page)

        # Wait for search results to load
        print("⏳ Waiting for search results to load...")
        await human_delay(5, 8)

        # Check for challenges again after waiting
        print("🔍 Checking for post-search challenges...")
        await handle_challenges_with_ai(page, ai_solver)

        # Final wait for page to stabilize
        await human_delay(3, 5)

        # Get max properties from environment
        max_properties = int(os.getenv('ZILLOW_MAX_PROPERTIES', '20'))
        properties = await collect_properties(page, max_properties)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(properties, f, indent=2)
        print(f"[+] Saved {len(properties)} properties to {OUTPUT_FILE}")
        await browser.close()
        await playwright.stop()
    except Exception as e:
        print(f"[!] Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
