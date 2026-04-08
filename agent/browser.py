import asyncio
import base64
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_stealth import Stealth


class BrowserController:
    def __init__(self, headless: bool = False, screenshot_dir: str = "screenshots"):
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self.page: Page | None = None
        self._step = 0

    async def start(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            channel="chrome",          # use real installed Chrome, not bundled Chromium
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="de-DE",
            timezone_id="Europe/Berlin",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        self.page = await self._context.new_page()
        await Stealth().apply_stealth_async(self.page)   # patch navigator, webdriver, plugins, etc.

    async def stop(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    # --- Navigation ---

    async def navigate(self, url: str):
        await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await self._random_delay()

    async def get_url(self) -> str:
        return self.page.url

    async def dismiss_consent(self):
        """
        Try to dismiss cookie/GDPR consent banners using known CSS selectors.
        Silently does nothing if no banner is found.
        """
        selectors = [
            "button[data-testid='as24-cmp-accept-all-button']",   # autoscout24
            "button.cmp-intro_acceptAll",
            "button#onetrust-accept-btn-handler",
            "[aria-label='Alle akzeptieren']",
            "button:has-text('Alle akzeptieren')",
            "button:has-text('Accept all')",
            "button:has-text('Akzeptieren')",
            "button:has-text('Zustimmen')",
            ".consent-button-accept",
            "#accept-all-cookies",
        ]
        for selector in selectors:
            try:
                locator = self.page.locator(selector).first
                if await locator.is_visible(timeout=1500):
                    await locator.click()
                    await self._random_delay(500, 1000)
                    return True
            except Exception:
                continue
        return False

    # --- Screenshot ---

    async def screenshot(self, label: str = "") -> bytes:
        self._step += 1
        name = f"step_{self._step:03d}_{label}.png" if label else f"step_{self._step:03d}.png"
        path = self.screenshot_dir / name
        data = await self.page.screenshot(full_page=False)
        path.write_bytes(data)
        return data

    @staticmethod
    def to_base64(image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    # --- Actions ---

    async def click(self, x: int, y: int):
        await self.page.mouse.move(x, y)
        await self._random_delay(100, 250)
        await self.page.mouse.click(x, y)
        await self._random_delay()

    async def click_selector(self, selector: str):
        await self.page.locator(selector).first.click(timeout=10000)
        await self._random_delay()

    async def type_text(self, text: str, delay_ms: int = 60):
        await self.page.keyboard.type(text, delay=delay_ms)
        await self._random_delay()

    async def fill(self, selector: str, text: str):
        await self.page.locator(selector).first.fill(text)
        await self._random_delay()

    async def press(self, key: str):
        await self.page.keyboard.press(key)
        await self._random_delay()

    async def scroll(self, direction: str = "down", amount: int = 400):
        delta = amount if direction == "down" else -amount
        await self.page.mouse.wheel(0, delta)
        await self._random_delay(300, 600)

    # --- Page info ---

    async def get_page_text(self) -> str:
        return await self.page.inner_text("body")

    async def wait_for_load(self, timeout: int = 5000):
        await self.page.wait_for_load_state("networkidle", timeout=timeout)

    # --- Helpers ---

    async def _random_delay(self, min_ms: int = 400, max_ms: int = 900):
        import random
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)

    # --- Context manager support ---

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()
