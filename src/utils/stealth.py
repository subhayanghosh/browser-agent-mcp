import random
import asyncio
from playwright.async_api import Page


class StealthUtils:
    @staticmethod
    async def inject_stealth_scripts(page: Page):
        """Inject scripts to mask automation detection"""
        await page.add_init_script("""
            // Override webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Override chrome runtime
            window.chrome = {
                runtime: {},
            };
            
            // Override permissions
            const originalGetProperty = Object.getOwnPropertyDescriptor;
            Object.getOwnPropertyDescriptor = function(obj, prop) {
                if (prop === 'webdriver') {
                    return undefined;
                }
                return originalGetProperty(obj, prop);
            };
        """)

    @staticmethod
    def get_random_user_agent():
        """Get a random realistic user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)

    @staticmethod
    def get_random_viewport():
        """Get a random realistic viewport size"""
        viewports = [
            {"width": 1280, "height": 720},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864},
            {"width": 1920, "height": 1080},
            {"width": 2560, "height": 1440}
        ]
        return random.choice(viewports)

    @staticmethod
    def get_random_timezone():
        """Get a random timezone"""
        timezones = [
            'America/New_York',
            'America/Chicago',
            'America/Denver',
            'America/Los_Angeles',
            'America/Phoenix',
            'America/Anchorage',
            'Pacific/Honolulu'
        ]
        return random.choice(timezones)

    @staticmethod
    def get_random_geolocation():
        """Get a random geolocation for major US cities"""
        locations = [
            {"longitude": -74.006, "latitude": 40.7128},  # NYC
            {"longitude": -87.6298, "latitude": 41.8781},  # Chicago
            {"longitude": -118.2437, "latitude": 34.0522},  # LA
            {"longitude": -95.3698, "latitude": 29.7604},  # Houston
            {"longitude": -112.0740, "latitude": 33.4484},  # Phoenix
            {"longitude": -97.7431, "latitude": 30.2672},  # Austin
            {"longitude": -122.4194, "latitude": 37.7749},  # San Francisco
        ]
        return random.choice(locations)

    @staticmethod
    async def human_like_mouse_movement(page: Page, target_x: float, target_y: float, duration: float = 0.5):
        """Simulate human-like mouse movement with natural curves"""
        start_x, start_y = await page.evaluate("() => [window.innerWidth / 2, window.innerHeight / 2]")

        # Generate control points for natural curve
        control_x = start_x + (target_x - start_x) * random.uniform(0.3, 0.7)
        control_y = start_y + (target_y - start_y) * random.uniform(0.3, 0.7)

        steps = int(duration * 60)  # 60 FPS
        for i in range(steps + 1):
            t = i / steps
            # Quadratic Bezier curve for natural movement
            x = (1 - t) ** 2 * start_x + 2 * (1 - t) * \
                t * control_x + t ** 2 * target_x
            y = (1 - t) ** 2 * start_y + 2 * (1 - t) * \
                t * control_y + t ** 2 * target_y

            await page.mouse.move(x, y)
            await asyncio.sleep(duration / steps)

    @staticmethod
    async def human_like_press_hold(page: Page, element, duration: float = 3.0):
        """Simulate human-like press and hold with micro-movements"""
        try:
            box = await element.bounding_box()
            if not box:
                return False

            center_x = box['x'] + box['width'] / 2
            center_y = box['y'] + box['height'] / 2

            # Move to element with human-like movement
            await StealthUtils.human_like_mouse_movement(page, center_x, center_y, 0.8)

            # Small pause before pressing
            await asyncio.sleep(random.uniform(0.1, 0.3))

            # Press down
            await page.mouse.down()

            # Add micro-movements while holding
            hold_steps = int(duration * 10)  # 10 movements per second
            for i in range(hold_steps):
                # Small random movement within the button area
                offset_x = random.uniform(-5, 5)
                offset_y = random.uniform(-5, 5)
                await page.mouse.move(center_x + offset_x, center_y + offset_y)
                await asyncio.sleep(duration / hold_steps)

            # Release
            await page.mouse.up()

            return True

        except Exception as e:
            print(f"[Stealth] Error in human-like press & hold: {e}")
            return False
