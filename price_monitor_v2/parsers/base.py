
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from price_monitor_v2.core.network import NetworkManager

class BaseParser(ABC):
    def __init__(self, network_manager: NetworkManager):
        self.network = network_manager

    @abstractmethod
    def fetch_data(self, url: str) -> str:
        pass

    @abstractmethod
    def extract_products(self, content: str) -> List[Dict[str, Any]]:
        pass
    
    def detect_pagination(self, content: str) -> Optional[str]:
        """
        Generic pagination detection.
        Returns URL of next page if found, else None.
        """
        try:
            soup = BeautifulSoup(content, "lxml")
            # Look for rel="next"
            link = soup.find("link", rel="next")
            if link and link.get("href"):
                return link.get("href")
                
            # Look for <a> with text "Next", "Siguiente", "»"
            for text in ["Siguiente", "Next", "»", ">"]:
                a_tag = soup.find("a", string=lambda x: x and text in x)
                if a_tag and a_tag.get("href"):
                    return a_tag.get("href")
        except:
            pass
        return None
