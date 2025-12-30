
import time
from typing import List, Dict, Any
from .base import BaseParser
from price_monitor_v2.utils.helpers import extract_products_by_heuristics
from price_monitor_v2.config.settings import CATEGORIAS_PRODUCTOS

class CamperoParser(BaseParser):
    def fetch_data(self, url: str) -> str:
        """
        Fetches multiple category pages to ensure coverage of all products.
        Ignores the base 'url' argument in favor of specific paths.
        """
        base_url = "https://sv.campero.com"
        paths = [
            "/menu/pollo-tradicional",
            "/menu/para-compartir",
            "/menu/hamburguesas-y-sandwiches",
            "/menu/postres",
            "/menu/campero-y-mas"  # Often has extras/wings
        ]
        
        full_content = ""
        for path in paths:
            target_url = base_url + path
            print(f"   [Campero] Fetching category: {path}...")
            # We treat each as a separate page load. 
            # We don't need the interactive callback anymore since we go directly to the view.
            # We WAIT for "$" text to ensure prices are loaded.
            html = self.network.fetch_with_playwright(target_url, wait_selector="text=$")
            full_content += html + "\n<!-- SPLIT -->\n"
            time.sleep(1) # Polite delay
            
        return full_content

    # _expand_categories is no longer needed but we can keep it deprecated or remove it.
    def _expand_categories(self, page):
        pass

    def extract_products(self, content: str) -> List[Dict[str, Any]]:
        return extract_products_by_heuristics(content, CATEGORIAS_PRODUCTOS)
