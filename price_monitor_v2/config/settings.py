
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Security & Network ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
PROXY_URL = os.getenv("PROXY_URL", "") # Magnetic or other proxy URL

# --- Monitoring Config ---
INTERVALO_HORAS = int(os.getenv("INTERVALO_HORAS", "4"))
HORA_INICIO = int(os.getenv("HORA_INICIO", "8"))
HORA_FIN = int(os.getenv("HORA_FIN", "19"))
ARCHIVO_HISTORIAL = "precios_historial.json"

# --- Constants ---
KEYWORDS_PROMOCION = ["off", "promo", "descuento", "oferta", "2x1", "gratis", "especial"]

CATEGORIAS_PRODUCTOS = {
    "hamburguesas": {
        "nombre": "Hamburguesas / Sandwiches",
        "keywords": ["kruncher", "sandwich", "hamburguesa", "burger", "bacon"],
        "excluir": ["pizza", "postre", "brownie", "pastel", "pie", "helado"],
    },
    "pollo_individual": {
        "nombre": "Menú Pollo Individual",
        "keywords": ["combo", "box", "menú", "menu", "personal", "individual", "2 piezas", "3 piezas"],
        "excluir": ["familiar", "compartir", "pack", "banquete", "pizza", "kruncher", "sandwich", "postre", "brownie", "pastel", "pie", "helado"],
    },
    "pollo_familiar": {
        "nombre": "Pollo Familiar / Compartir",
        "keywords": ["familiar", "compartir", "pack", "banquete", "bucket", "full", "8 piezas", "12 piezas"],
        "excluir": ["pizza", "postre", "brownie", "pastel", "pie", "helado"],
    },
    "alitas": {
        "nombre": "Alitas",
        "keywords": ["alita", "wing", "alitas", "wings"],
        "excluir": ["pizza", "postre", "brownie", "pastel", "pie", "helado"],
    },
    "postres": {
        "nombre": "Postres",
        "keywords": ["postre", "brownie", "pastel", "pie", "tres leches", "flan", "helado", "sundae"],
        "excluir": ["combo", "menu", "pollo"],
    },
}

PRECIOS_REFERENCIA_CAMPERO = {
    "hamburguesas": {
        "nombre": "Sandwich Campero",
        "precio": 0.0, 
    },
    "pollo_individual": {
        "nombre": "Menú Campero (2 piezas)",
        "precio": 6.90,
    },
    "pollo_familiar": {
        "nombre": "Combo 12 Piezas",
        "precio": 25.95,
    },
    "alitas": {
        "nombre": "Menú Alitas",
        "precio": 9.40,
    },
    "postres": {
        "nombre": "Postre Campero",
        "precio": 0.0,
    },
}

# --- Competitors ---
# Refers to Parser class names (strings) to avoid circular imports. 
# Loaders will instantiate them.
COMPETITORS = [
    {
        "name": "Pollo Campero",
        "url": "https://sv.campero.com/menu",
        "parser": "CamperoParser",
        "active": True,
        "use_playwright": True,
        "is_reference": True
    },
    {
        "name": "KFC El Salvador",
        "url": "https://www.kfc.com.sv/categorias",
        "parser": "KFCParser",
        "active": True,
        "use_playwright": True
    },
    {
        "name": "Pollo Campestre",
        "url": "https://api.pollocampestre.com.sv/v2/home/GetHomeConfiguration",
        "parser": "CampestreParser",
        "active": True,
        "use_playwright": False
    }
]

# Default Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}
