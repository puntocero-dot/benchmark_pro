
import json
from typing import List, Dict, Any
from .base import BaseParser
from price_monitor_v2.utils.helpers import classify_product, clean_price
from price_monitor_v2.config.settings import CATEGORIAS_PRODUCTOS

class CampestreParser(BaseParser):
    def fetch_data(self, url: str) -> str:
        # Campestre uses a POST API
        payload = {"country": "sv", "language": "es"}
        return self.network.fetch_with_requests(url, method="POST", json_payload=payload)

    def extract_products(self, content: str) -> List[Dict[str, Any]]:
        productos = []
        try:
            data = json.loads(content)
            sections = data.get("data", {}).get("sections", [])
            
            for section in sections:
                for item in section.get("data", []):
                    sub_products = item.get("dataProducts", [])
                    for p in sub_products:
                        name = p.get("name", "")
                        try:
                            price = float(p.get("salePrice", 0))
                        except:
                            price = 0.0
                            
                        cat = classify_product(name)
                        if cat and price > 0:
                            productos.append({
                                "nombre": name,
                                "precio": price,
                                "categoria": cat,
                                "categoria_nombre": CATEGORIAS_PRODUCTOS[cat]["nombre"]
                            })
                            
            # Deduplicate logic similar to KFC but key can include name for safety
            unique = []
            seen = set()
            for p in productos:
                key = (p["categoria"], p["precio"])
                if key not in seen:
                    seen.add(key)
                    unique.append(p)
            return unique
            
        except Exception as e:
            print(f"   Error parsing Campestre API: {e}")
            return []
