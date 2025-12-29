
import re
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
from price_monitor_v2.config.settings import CATEGORIAS_PRODUCTOS, KEYWORDS_PROMOCION

def clean_price(price_text: str) -> Optional[float]:
    """
    Extracts numeric price from text (e.g., "$5.99" -> 5.99).
    """
    if not price_text:
        return None
    
    text = price_text.strip()
    # Pattern for numbers with decimals
    pattern = r"[\d]+[.,]?\d*"
    matches = re.findall(pattern, text)
    
    if matches:
        price_str = matches[0].replace(",", ".")
        try:
            return float(price_str)
        except ValueError:
            return None
    return None

def classify_product(product_name: str) -> Optional[str]:
    """
    Classifies a product into a category based on keywords.
    """
    name_lower = product_name.lower()
    
    for cat_key, rules in CATEGORIAS_PRODUCTOS.items():
        # Check exclusions first
        if any(excl in name_lower for excl in rules["excluir"]):
            continue
            
        # Check keywords
        if any(kw in name_lower for kw in rules["keywords"]):
            return cat_key
            
    return None

def detect_promotions(html: str, keywords: List[str] = None) -> List[str]:
    """
    Detects promotion keywords in HTML content.
    """
    if keywords is None:
        keywords = KEYWORDS_PROMOCION
    
    found = []
    try:
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text().lower()
        
        for kw in keywords:
            if kw.lower() in text:
                found.append(kw)
    except Exception as e:
        print(f"Warning: Promotion detection error: {e}")
        
    return found

def extract_price_generic(html: str, selector: str) -> Optional[float]:
    """
    Generic extraction using CSS selector or Regex fallback.
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        
        if selector:
            elements = soup.select(selector)
            for el in elements:
                p = clean_price(el.get_text(strip=True))
                if p and p > 0:
                    return p
        
        # Fallback Regex
        text = soup.get_text()
        pattern = r"\$\s*(\d+[.,]\d{2})"
        matches = re.findall(pattern, text)

    except Exception:
        pass
    return None

def extract_products_by_heuristics(html: str, categories_config: Dict) -> List[Dict]:
    """
    Extracts products by finding prices and looking at parent context.
    """
    products = []
    try:
        soup = BeautifulSoup(html, "lxml")
        pattern = re.compile(r"\$\s*\d+\.\d{2}")
        precios_found = soup.find_all(string=pattern)
        
        seen = set()
        
        for node in precios_found:
            try:
                container = node.parent
                price_float = clean_price(node)
                if not price_float or price_float <= 0: continue
                
                pointer = container
                for _ in range(6):
                    if not pointer: break
                    text = pointer.get_text(" ", strip=True)
                    cat = classify_product(text)
                    
                    if cat:
                        key = (cat, price_float)
                        if key not in seen:
                            name = text.split("$")[0].strip()
                            if len(name) > 80: name = name[:80] + "..."
                            
                            products.append({
                                "nombre": name,
                                "precio": price_float,
                                "categoria": cat,
                                "categoria_nombre": categories_config[cat]["nombre"]
                            })
                            seen.add(key)
                        break
                    pointer = pointer.parent
            except:
                continue
    except Exception as e:
        print(f"   Heuristic extraction error: {e}")
    return products

