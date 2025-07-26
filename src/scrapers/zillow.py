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


async def scroll_and_collect(page, max_properties=20):
    """Collect property data with improved selectors and error handling"""
    results = []
    seen_urls = set()
    scrolls = 0

    print(f"📊 Collecting up to {max_properties} properties...")

    while len(results) < max_properties and scrolls < 20:
        try:
            # Wait for property cards with multiple selectors
            card_selectors = [
                'ul.photo-cards li article',
                '[data-test="property-card"]',
                '.property-card',
                '[class*="property"]',
                '[class*="listing"]',
                'article[data-test*="property"]',
                'li[data-test*="property"]'
            ]

            cards_found = False
            cards = []
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
                # Take a screenshot for debugging
                screenshot = await page.screenshot()
                with open(f"debug_no_cards_{scrolls}.png", "wb") as f:
                    f.write(screenshot)
                print(
                    f"📸 Debug screenshot saved: debug_no_cards_{scrolls}.png")
                break

            # Process each card
            for card in cards:
                try:
                    # Try to get URL
                    url = await card.evaluate('el => el.querySelector("a")?.href || ""')
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Get property data with multiple selectors
                    title = await card.evaluate('el => el.getAttribute("aria-label") || el.textContent || ""')

                    # Try different price selectors
                    price_selectors = [
                        '[data-test="property-card-price"]',
                        '[data-test*="price"]',
                        '.price',
                        '[class*="price"]'
                    ]
                    price = ""
                    for price_selector in price_selectors:
                        try:
                            price = await card.evaluate(f'el => el.querySelector("{price_selector}")?.textContent || ""')
                            if price.strip():
                                break
                        except:
                            continue

                    # Try different bed/bath selectors
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

            # Scroll down to load more
            await page.mouse.wheel(0, 800)
            await human_delay(1.5, 2.5)
            scrolls += 1

        except Exception as e:
            print(f"❌ Error in collection loop: {e}")
            break

    return results[:max_properties]


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

        # Wait for search results to load
        print("⏳ Waiting for search results to load...")
        await human_delay(5, 8)

        # Get max properties from environment
        max_properties = int(os.getenv('ZILLOW_MAX_PROPERTIES', '20'))
        properties = await scroll_and_collect(page, max_properties)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(properties, f, indent=2)
        print(f"[+] Saved {len(properties)} properties to {OUTPUT_FILE}")
        await browser.close()
        await playwright.stop()
    except Exception as e:
        print(f"[!] Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
