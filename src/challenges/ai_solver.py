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
                    return True
                else:
                    print(
                        f"[AI] Attempt {self.attempt_count} failed, retrying...")
                    await asyncio.sleep(2)  # Wait before retry

            except Exception as e:
                print(f"[AI] Error on attempt {self.attempt_count}: {e}")
                await asyncio.sleep(2)

        print(f"[AI] All {self.max_attempts} attempts failed")
        return False

    async def handle_press_hold(self, page: Page):
        """Handle press and hold challenges"""
        try:
            elements = await self.find_interactive_elements(page, 'press_hold')

            if elements:
                element_info = elements[0]
                element = element_info['element']

                print(
                    f"[AI] Executing press & hold on {element_info['selector']}")

                # Try multiple approaches for press & hold

                # Approach 1: Direct element interaction
                try:
                    await element.press("MouseDown")
                    await asyncio.sleep(3)  # Hold for 3 seconds
                    await element.press("MouseUp")
                    print("[AI] Press & hold completed (approach 1)")
                    return True
                except Exception as e1:
                    print(f"[AI] Approach 1 failed: {e1}")

                # Approach 2: Human-like mouse interaction with stealth
                try:
                    success = await StealthUtils.human_like_press_hold(page, element, 3.0)
                    if success:
                        print("[AI] Press & hold completed (approach 2 - stealth)")
                        return True
                except Exception as e2:
                    print(f"[AI] Approach 2 failed: {e2}")

                # Approach 3: Click and hold with JavaScript
                try:
                    await page.evaluate("""
                        (element) => {
                            const mouseDownEvent = new MouseEvent('mousedown', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            element.dispatchEvent(mouseDownEvent);
                            
                            setTimeout(() => {
                                const mouseUpEvent = new MouseEvent('mouseup', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                });
                                element.dispatchEvent(mouseUpEvent);
                            }, 3000);
                        }
                    """, element)
                    await asyncio.sleep(3.5)  # Wait for the JavaScript to complete
                    print("[AI] Press & hold completed (approach 3)")
                    return True
                except Exception as e3:
                    print(f"[AI] Approach 3 failed: {e3}")

                # Approach 4: Try clicking the element directly
                try:
                    await element.click()
                    print("[AI] Press & hold completed (approach 4 - direct click)")
                    return True
                except Exception as e4:
                    print(f"[AI] Approach 4 failed: {e4}")

                # Approach 5: Try clicking by coordinates
                try:
                    box = await element.bounding_box()
                    if box:
                        center_x = box['x'] + box['width'] / 2
                        center_y = box['y'] + box['height'] / 2
                        await page.mouse.click(center_x, center_y)
                        print(
                            "[AI] Press & hold completed (approach 5 - coordinate click)")
                        return True
                except Exception as e5:
                    print(f"[AI] Approach 5 failed: {e5}")

                # Approach 6: Try clicking anywhere on the page that looks like a button
                try:
                    # Look for any clickable element with "Press" text
                    all_elements = await page.query_selector_all('*')
                    # Limit to first 20 elements
                    for elem in all_elements[:20]:
                        try:
                            text = await elem.evaluate('el => el.textContent || ""')
                            if 'press' in text.lower() and 'hold' in text.lower():
                                await elem.click()
                                print(
                                    "[AI] Press & hold completed (approach 6 - text search)")
                                return True
                        except:
                            continue
                except Exception as e6:
                    print(f"[AI] Approach 6 failed: {e6}")

            return False

        except Exception as e:
            print(f"[AI] Error in press & hold: {e}")
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
