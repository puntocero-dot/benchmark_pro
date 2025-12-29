
import time
from typing import List, Dict, Any
from .base import BaseParser
from price_monitor_v2.utils.helpers import extract_products_by_heuristics
from price_monitor_v2.config.settings import CATEGORIAS_PRODUCTOS

class CamperoParser(BaseParser):
    def fetch_data(self, url: str) -> str:
        return self.network.fetch_with_playwright(url, interactive_callback=self._expand_categories)

    def _expand_categories(self, page):
        print("   [Campero] Expanding categories interactively...")
        try:
            # Wait for items
            page.wait_for_selector(".category-item", state="attached", timeout=15000)
            cats = page.locator(".category-item").all()
            print(f"   Found {len(cats)} categories.")
            
            # Click each one to ensure products are rendered in DOM
            for i, cat in enumerate(cats):
                try:
                    if cat.is_visible():
                        cat.click()
                        time.sleep(0.5) 
                except Exception:
                    pass
            time.sleep(2)
        except Exception as e:
            print(f"   [Campero] Warning: Failed to expand categories ({e})")

    def extract_products(self, content: str) -> List[Dict[str, Any]]:
        return extract_products_by_heuristics(content, CATEGORIAS_PRODUCTOS)
