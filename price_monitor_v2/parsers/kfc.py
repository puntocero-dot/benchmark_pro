
from typing import List, Dict, Any
from .base import BaseParser
from price_monitor_v2.utils.helpers import extract_products_by_heuristics
from price_monitor_v2.config.settings import CATEGORIAS_PRODUCTOS

class KFCParser(BaseParser):
    def fetch_data(self, url: str) -> str:
        # KFC requires JavaScript rendering
        return self.network.fetch_with_playwright(url, wait_selector="button")

    def extract_products(self, content: str) -> List[Dict[str, Any]]:
        return extract_products_by_heuristics(content, CATEGORIAS_PRODUCTOS)
