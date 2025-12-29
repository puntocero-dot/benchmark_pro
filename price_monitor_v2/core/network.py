
import requests
import random
import time
from playwright.sync_api import sync_playwright
try:
    from fake_useragent import UserAgent
    ua_rotator = UserAgent()
except ImportError:
    ua_rotator = None

from price_monitor_v2.config.settings import PROXY_URL, DEFAULT_HEADERS

class NetworkManager:
    def __init__(self):
        self.proxy = PROXY_URL if PROXY_URL else None

    def _get_headers(self):
        headers = DEFAULT_HEADERS.copy()
        if ua_rotator:
            try:
                headers["User-Agent"] = ua_rotator.random
            except:
                pass
        return headers

    def _get_proxy_config(self):
        """Returns Playwright proxy config dictionary if proxy is set."""
        if not self.proxy:
            return None
        return {"server": self.proxy}

    def _get_requests_proxies(self):
        """Returns Requests proxies dictionary if proxy is set."""
        if not self.proxy:
            return None
        return {"http": self.proxy, "https": self.proxy}

    def fetch_with_requests(self, url: str, method="GET", json_payload=None) -> str:
        """Standard HTTP request."""
        print(f"   [Requests] Connecting to {url}...")
        try:
            proxies = self._get_requests_proxies()
            headers = self._get_headers()
            
            if method == "POST":
                resp = requests.post(url, json=json_payload, headers=headers, proxies=proxies, timeout=30)
            else:
                resp = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"   Error (Requests): {e}")
            return ""

    def fetch_with_playwright(self, url: str, wait_selector=None, interactive_callback=None) -> str:
        """
        Playwright fetch.
        interactive_callback: Function that takes (page) and performs actions (clicking, scrolling).
        """
        print(f"   [Playwright] Connecting to {url}...")
        try:
            with sync_playwright() as p:
                proxy_cfg = self._get_proxy_config()
                
                # Launch options
                launch_args = {"headless": True}
                if proxy_cfg:
                    launch_args["proxy"] = proxy_cfg
                
                browser = p.chromium.launch(**launch_args)
                
                # Context with User Agent
                context = browser.new_context(
                    user_agent=self._get_headers()["User-Agent"],
                    viewport={"width": 1366, "height": 768}
                )
                
                page = context.new_page()
                
                # Navigation
                # 'domcontentloaded' is faster; 'networkidle' is safer.
                # If using callback, we rely on it to wait.
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=20000)
                    except:
                        print(f"   Warning: Timeout waiting for selector {wait_selector}")

                # Custom Interaction (e.g. Campero clicks)
                if interactive_callback:
                    interactive_callback(page)
                else:
                    # Default wait if no interaction
                    time.sleep(3)

                content = page.content()
                browser.close()
                return content
        except Exception as e:
            print(f"   Error (Playwright): {e}")
            return ""
