import asyncio
import cv2
import numpy as np
from PIL import Image
import easyocr
import pytesseract
from playwright.async_api import Page
import re
import base64
import io
import os
import random
from datetime import datetime
from src.utils.stealth import StealthUtils


class AIChallengeSolver:
    def __init__(self):
        # Initialize EasyOCR for better text recognition
        self.reader = easyocr.Reader(['en'])
        self.attempt_count = 0
        self.max_attempts = 5
        self.screenshot_dir = "challenge_screenshots"

        # Create screenshot directory
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    async def analyze_page_content(self, page: Page):
        """Analyze the entire page to understand what type of challenge is present"""
        try:
            # Take a screenshot of the page
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot = await page.screenshot()
            image = Image.open(io.BytesIO(screenshot))

            # Save screenshot for debugging
            screenshot_path = os.path.join(
                self.screenshot_dir, f"challenge_{timestamp}.png")
            image.save(screenshot_path)
            print(f"[AI] Screenshot saved: {screenshot_path}")

            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Extract text from the image
            text_results = self.reader.readtext(cv_image)
            page_text = ' '.join([text[1] for text in text_results])

            print(f"[AI] Detected page text: {page_text[:200]}...")

            return self.classify_challenge(page_text, cv_image)

        except Exception as e:
            print(f"[AI] Error analyzing page: {e}")
            return None

    def classify_challenge(self, text: str, image):
        """Classify the type of challenge based on text and visual analysis"""
        text_lower = text.lower()

        # Press & Hold challenges
        if any(phrase in text_lower for phrase in ['press & hold', 'press and hold', 'hold to confirm']):
            return {
                'type': 'press_hold',
                'confidence': 0.9,
                'action': 'press_and_hold'
            }

        # CAPTCHA challenges
        if any(phrase in text_lower for phrase in ['captcha', 'verify you are human', 'robot check']):
            return {
                'type': 'captcha',
                'confidence': 0.8,
                'action': 'manual_intervention_required'
            }

        # Image selection challenges
        if any(phrase in text_lower for phrase in ['select all images', 'click on', 'find the']):
            return {
                'type': 'image_selection',
                'confidence': 0.7,
                'action': 'manual_intervention_required'
            }

        # Slider challenges
        if any(phrase in text_lower for phrase in ['slide to verify', 'drag the slider']):
            return {
                'type': 'slider',
                'confidence': 0.8,
                'action': 'slide_verification'
            }

        # Checkbox challenges
        if any(phrase in text_lower for phrase in ['i am not a robot', 'check this box']):
            return {
                'type': 'checkbox',
                'confidence': 0.9,
                'action': 'click_checkbox'
            }

        # Cookie consent
        if any(phrase in text_lower for phrase in ['accept cookies', 'cookie policy', 'privacy policy']):
            return {
                'type': 'cookie_consent',
                'confidence': 0.9,
                'action': 'accept_cookies'
            }

        return None

    async def find_interactive_elements(self, page: Page, challenge_type: str):
        """Find interactive elements based on challenge type"""
        elements = []

        if challenge_type == 'press_hold':
            # Look for buttons with various selectors
            selectors = [
                'button:has-text("Press & Hold")',
                'p:has-text("Press & Hold")',
                '[role="button"]:has-text("Press & Hold")',
                'div:has-text("Press & Hold")',
                'span:has-text("Press & Hold")',
                '[class*="button"]:has-text("Press & Hold")',
                '[class*="btn"]:has-text("Press & Hold")',
                'a:has-text("Press & Hold")',
                # Try to find by partial text match
                'button:has-text("Press")',
                'p:has-text("Press")',
                'div:has-text("Press")',
                # Try to find by ID if we know it
                '#ZLAyyssWZRaLUoC',
                '[id="ZLAyyssWZRaLUoC"]',
                # More specific selectors
                '[class*="scOJKUAdFmeUmFj"]',
                '[class*="ZLAyyssWZRaLUoC"]',
                'p[class*="scOJKUAdFmeUmFj"]',
                'div[class*="scOJKUAdFmeUmFj"]',
                # Generic interactive elements
                '[tabindex]',
                '[onclick]',
                '[onmousedown]',
                '[onmouseup]',
                '[onmouseover]'
            ]

            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # Get element details for debugging
                        tag_name = await element.evaluate('el => el.tagName')
                        class_name = await element.evaluate('el => el.className')
                        text_content = await element.evaluate('el => el.textContent')

                        elements.append({
                            'element': element,
                            'selector': selector,
                            'type': 'button',
                            'tag_name': tag_name,
                            'class_name': class_name,
                            'text_content': text_content
                        })
                        print(f"[AI] Found press & hold element:")
                        print(f"    Selector: {selector}")
                        print(f"    Tag: {tag_name}")
                        print(f"    Class: {class_name}")
                        print(f"    Text: {text_content}")
                except Exception as e:
                    print(f"[AI] Selector {selector} failed: {e}")
                    continue

        elif challenge_type == 'checkbox':
            # Look for checkboxes
            selectors = [
                'input[type="checkbox"]',
                '[role="checkbox"]',
                'div[aria-checked="false"]'
            ]

            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        elements.append({
                            'element': element,
                            'selector': selector,
                            'type': 'checkbox'
                        })
                except:
                    continue

        elif challenge_type == 'slider':
            # Look for slider elements
            selectors = [
                '[role="slider"]',
                'input[type="range"]',
                '.slider',
                '[draggable="true"]'
            ]

            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        elements.append({
                            'element': element,
                            'selector': selector,
                            'type': 'slider'
                        })
                except:
                    continue

        return elements

    async def execute_challenge_action(self, page: Page, challenge_info: dict):
        """Execute the appropriate action based on challenge type with retry logic"""
        action = challenge_info.get('action')

        for attempt in range(self.max_attempts):
            self.attempt_count += 1
            print(
                f"[AI] Attempt {self.attempt_count}/{self.max_attempts} for {action}")

            try:
                if action == 'press_and_hold':
                    success = await self.handle_press_hold(page)
                elif action == 'click_checkbox':
                    success = await self.handle_checkbox(page)
                elif action == 'slide_verification':
                    success = await self.handle_slider(page)
                elif action == 'accept_cookies':
                    success = await self.handle_cookie_consent(page)
                elif action == 'manual_intervention_required':
                    print(
                        "[AI] Manual intervention required for this challenge type")
                    return False
                else:
                    success = False

                if success:
                    print(
                        f"[AI] Challenge solved successfully on attempt {self.attempt_count}")

                    # Verify the challenge was actually solved
                    await asyncio.sleep(2)  # Wait for page to update
                    verification_result = await self.verify_challenge_solved(page)

                    if verification_result:
                        print("[AI] Challenge verification successful")
                        return True
                    else:
                        print(
                            "[AI] Challenge verification failed - challenge still present")
                        success = False

                if not success:
                    print(
                        f"[AI] Attempt {self.attempt_count} failed, retrying...")
                    await asyncio.sleep(2)  # Wait before retry

            except Exception as e:
                print(f"[AI] Error on attempt {self.attempt_count}: {e}")
                await asyncio.sleep(2)

        print(f"[AI] All {self.max_attempts} attempts failed")
        return False

    async def verify_challenge_solved(self, page: Page):
        """Verify that the challenge has been successfully solved"""
        try:
            # Wait a moment for the page to update
            await asyncio.sleep(2)

            # Check if the challenge modal is still present (more comprehensive check)
            challenge_indicators = [
                'text="Before we continue..."',
                'text="Press & Hold to confirm"',
                'button:has-text("Press & Hold")',
                'p:has-text("Press & Hold")',
                'div:has-text("Press & Hold")',
                '[class*="scOJKUAdFmeUmFj"]',
                '#ZLAyyssWZRaLUoC',
                'iframe[id="px-captcha-modal"]'
            ]

            for indicator in challenge_indicators:
                try:
                    element = await page.query_selector(indicator)
                    if element:
                        print(f"[AI] Challenge still present: {indicator}")
                        return False
                except:
                    continue

            # Check if search input is now available and interactive (indicates challenge is solved)
            search_selectors = [
                'input[aria-label="Enter an address, neighborhood, city, or ZIP code"]',
                'input[placeholder*="address"]',
                'input[placeholder*="city"]',
                'input[type="text"]'
            ]

            for selector in search_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(
                            f"[AI] Search input found with selector: {selector}")
                        return True
                except:
                    continue

            print("[AI] No search input found - challenge may not be solved")
            return False

        except Exception as e:
            print(f"[AI] Error in challenge verification: {e}")
            return False

    async def remove_interfering_elements(self, page: Page):
        """Remove or disable interfering elements like iframes"""
        try:
            await page.evaluate("""
                () => {
                    // Remove interfering iframes
                    const iframes = document.querySelectorAll('iframe[id*="captcha"], iframe[id*="modal"], iframe[class*="captcha"]');
                    iframes.forEach(iframe => {
                        iframe.style.display = 'none';
                        iframe.style.visibility = 'hidden';
                        iframe.style.pointerEvents = 'none';
                        iframe.style.zIndex = '-1';
                    });
                    
                    // Remove any overlay elements that might block interaction
                    const overlays = document.querySelectorAll('div[class*="overlay"], div[class*="modal"], div[style*="position: fixed"]');
                    overlays.forEach(overlay => {
                        if (overlay.style.zIndex > 1000) {
                            overlay.style.pointerEvents = 'none';
                        }
                    });
                }
            """)
            print("[AI] Removed interfering elements")
        except Exception as e:
            print(f"[AI] Error removing interfering elements: {e}")

    async def find_press_hold_button(self, page: Page):
        """Find the press & hold button using multiple strategies"""
        try:
            # Strategy 1: Look for specific selectors with better text matching
            selectors = [
                'button:has-text("Press & Hold")',
                'div:has-text("Press & Hold")',
                'p:has-text("Press & Hold")',
                'span:has-text("Press & Hold")',
                '[tabindex]',
                '#ZLAyyssWZRaLUoC',
                '.scOJKUAdFmeUmFj',
                '[class*="press"]',
                '[class*="hold"]',
                '[class*="button"]'
            ]

            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        try:
                            text = await element.evaluate('el => el.textContent || ""')
                            if 'press' in text.lower() and 'hold' in text.lower():
                                print(
                                    f"[AI] Found button with selector: {selector}")
                                return element
                        except:
                            continue
                except:
                    continue

            # Strategy 2: JavaScript search with more comprehensive approach
            button = await page.evaluate_handle("""
                () => {
                    // Look for any element with "Press & Hold" text
                    const elements = document.querySelectorAll('*');
                    for (const el of elements) {
                        if (el.textContent && el.textContent.toLowerCase().includes('press') && el.textContent.toLowerCase().includes('hold')) {
                            return el;
                        }
                    }
                    
                    // Look for elements with specific classes or IDs
                    const specificSelectors = [
                        '[tabindex]',
                        '[class*="press"]',
                        '[class*="hold"]',
                        '[class*="button"]',
                        '[id*="press"]',
                        '[id*="hold"]'
                    ];
                    
                    for (const selector of specificSelectors) {
                        try {
                            const els = document.querySelectorAll(selector);
                            for (const el of els) {
                                if (el.textContent && el.textContent.toLowerCase().includes('press')) {
                                    return el;
                                }
                            }
                        } catch (e) {
                            continue;
                        }
                    }
                    
                    return null;
                }
            """)

            if button and await button.evaluate('el => el !== null'):
                print("[AI] Found button via JavaScript search")
                return button

            # Strategy 3: Look for any clickable element in the modal
            try:
                modal_elements = await page.query_selector_all('[role="button"], button, [tabindex], [class*="btn"]')
                for element in modal_elements:
                    try:
                        text = await element.evaluate('el => el.textContent || ""')
                        if text.strip() and ('press' in text.lower() or 'hold' in text.lower()):
                            print(f"[AI] Found button in modal: {text}")
                            return element
                    except:
                        continue
            except:
                pass

            print("[AI] Could not find press & hold button with any strategy")
            return None

        except Exception as e:
            print(f"[AI] Error finding press & hold button: {e}")
            return None

    async def execute_simple_press_hold(self, page: Page, button):
        """Simulate a long press using element.hover() and mouse events (StackOverflow approach)"""
        try:
            print(f"[AI] Using StackOverflow approach: hover + mouse down/up")

            # Get the actual button position
            box = await button.bounding_box()
            if not box:
                print("[AI] Could not get button position")
                return False

            center_x = box['x'] + box['width'] / 2
            center_y = box['y'] + box['height'] / 2

            print(f"[AI] Button position: ({center_x}, {center_y})")

            # Step 1: Hover over the button (crucial for modals/overlays)
            await button.hover()
            await asyncio.sleep(random.uniform(0.2, 0.5))
            print("[AI] Hovered over button")

            # Step 2: Mouse down (start hold) with actual button coordinates
            await page.mouse.click(button='left', delay=10000, x=center_x, y=center_y)
            print("[AI] Mouse down - hold completed")

            return True

        except Exception as e:
            print(f"[AI] Error in StackOverflow press & hold: {e}")
            return False

    async def handle_press_hold(self, page: Page):
        """Handle press and hold challenges - simplified approach"""
        try:
            print("[AI] Starting simplified press & hold approach...")

            # Step 1: Remove any interfering iframes
            await self.remove_interfering_elements(page)

            # Step 2: Find the press & hold button using multiple strategies
            button = await self.find_press_hold_button(page)

            if not button:
                print("[AI] Could not find press & hold button")
                return False

            # Step 3: Execute the press & hold with a simple, reliable method
            success = await self.execute_simple_press_hold(page, button)

            if success:
                # Step 4: Wait and verify
                await asyncio.sleep(3)
                return await self.verify_challenge_solved(page)

            return False

        except Exception as e:
            print(f"[AI] Error in simplified press & hold: {e}")
            return False

    async def handle_checkbox(self, page: Page):
        """Handle checkbox challenges"""
        try:
            elements = await self.find_interactive_elements(page, 'checkbox')

            if elements:
                element = elements[0]['element']
                await element.click()
                print("[AI] Checkbox clicked")
                return True

            return False

        except Exception as e:
            print(f"[AI] Error in checkbox handling: {e}")
            return False

    async def handle_slider(self, page: Page):
        """Handle slider verification challenges"""
        try:
            elements = await self.find_interactive_elements(page, 'slider')

            if elements:
                element = elements[0]['element']
                box = await element.bounding_box()

                if box:
                    # Drag slider from left to right
                    start_x = box['x'] + 10
                    end_x = box['x'] + box['width'] - 10
                    y = box['y'] + box['height'] / 2

                    await page.mouse.move(start_x, y)
                    await page.mouse.down()
                    await page.mouse.move(end_x, y, steps=10)
                    await page.mouse.up()

                    print("[AI] Slider verification completed")
                    return True

            return False

        except Exception as e:
            print(f"[AI] Error in slider handling: {e}")
            return False

    async def handle_iframe_interference(self, page: Page):
        """Handle iframe interference that blocks pointer events"""
        try:
            # Check for interfering iframes
            iframe_selectors = [
                'iframe[id="px-captcha-modal"]',
                'iframe[class*="captcha"]',
                'iframe[class*="modal"]',
                'iframe[src*="captcha"]',
                'iframe[src*="challenge"]'
            ]

            for iframe_selector in iframe_selectors:
                try:
                    iframe = await page.query_selector(iframe_selector)
                    if iframe:
                        print(
                            f"[AI] Found interfering iframe: {iframe_selector}")

                        # Try to remove the iframe
                        await page.evaluate("""
                            (iframeSelector) => {
                                const iframe = document.querySelector(iframeSelector);
                                if (iframe) {
                                    iframe.style.display = 'none';
                                    iframe.style.visibility = 'hidden';
                                    iframe.style.pointerEvents = 'none';
                                    iframe.style.zIndex = '-1';
                                }
                            }
                        """, iframe_selector)

                        print(f"[AI] Disabled iframe: {iframe_selector}")
                        await asyncio.sleep(1)

                except Exception as e:
                    print(f"[AI] Error handling iframe {iframe_selector}: {e}")
                    continue

        except Exception as e:
            print(f"[AI] Error in iframe interference handling: {e}")

    async def handle_cookie_consent(self, page: Page):
        """Handle cookie consent dialogs"""
        try:
            # Look for common cookie accept buttons
            selectors = [
                'button:has-text("Accept")',
                'button:has-text("Accept All")',
                'button:has-text("I Accept")',
                '[data-testid="accept-cookies"]'
            ]

            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        print(f"[AI] Cookie consent accepted with {selector}")
                        return True
                except:
                    continue

            return False

        except Exception as e:
            print(f"[AI] Error in cookie consent: {e}")
            return False
