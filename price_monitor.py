# -*- coding: utf-8 -*-
"""
=============================================================================
MONITOR DE PRECIOS DE COMPETIDORES - EL SALVADOR
=============================================================================
Script automatizado para monitorear precios de KFC, Pollo Campestre y 
compararlos con Pollo Campero El Salvador.

Autor: Generado por Antigravity AI
Fecha: Diciembre 2024
=============================================================================
"""

import os
import json
import time
import random
import re
from datetime import datetime
from typing import Optional, Dict, List, Any

import requests
from bs4 import BeautifulSoup
import schedule
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Token y Chat ID de Telegram (configurar en .env)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Intervalo de revisión en horas (configurable via .env o aquí)
INTERVALO_HORAS = int(os.getenv("INTERVALO_HORAS", "4"))

# Horario de operación (24h) - Por defecto 08:00 a 19:00
HORA_INICIO = int(os.getenv("HORA_INICIO", "8"))
HORA_FIN = int(os.getenv("HORA_FIN", "19"))

# Archivo para persistencia de datos
ARCHIVO_HISTORIAL = "precios_historial.json"

# Keywords para detectar promociones (case-insensitive)
KEYWORDS_PROMOCION = ["off", "promo", "descuento", "oferta", "2x1", "gratis", "especial"]

# =============================================================================
# CATEGORÍAS DE PRODUCTOS - Solo pollo, sin pizza
# =============================================================================
CATEGORIAS_PRODUCTOS = {
    "combo_individual": {
        "nombre": "Combo Individual",
        "keywords": ["combo", "box", "menú", "menu", "kruncher", "personal", "individual"],
        "excluir": ["familiar", "compartir", "pack", "banquete", "pizza"],
    },
    "combo_familiar": {
        "nombre": "Combo Familiar",
        "keywords": ["familiar", "compartir", "pack", "banquete", "bucket", "full"],
        "excluir": ["pizza"],
    },
    "alitas": {
        "nombre": "Alitas",
        "keywords": ["alita", "wing", "alitas", "wings"],
        "excluir": ["pizza"],
    },
}

# =============================================================================
# PRECIOS DE REFERENCIA - POLLO CAMPERO (para comparar)
# Tienda: Alameda Roosevelt y 61 Av. Sur #3134, S.S
# Actualizados: 2024-12-29
# =============================================================================
PRECIOS_REFERENCIA_CAMPERO = {
    "combo_individual": {
        "nombre": "Menú Campero (2 piezas + acompañamiento + bebida)",
        "precio": 6.90,
    },
    "combo_familiar": {
        "nombre": "Combo 12 Piezas (12 piezas + 6 acompañamientos)",
        "precio": 25.95,
    },
    "alitas": {
        "nombre": "Menú Súper Campero de Alitas (9 alitas + 2 acompañamientos)",
        "precio": 9.40,
    },
}

# Headers realistas para simular navegación
HEADERS_NAVEGADOR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

# =============================================================================
# ESTRUCTURA DE COMPETIDORES
# =============================================================================
# Puedes agregar más competidores fácilmente siguiendo esta estructura.
# Para sitios con JavaScript dinámico, usa_playwright=True (requiere configuración adicional)

COMPETIDORES = [
    {
        "nombre": "KFC El Salvador",
        # URL corregida - redirige a /categorias
        "url": "https://www.kfc.com.sv/categorias",
        # Selector encontrado: precios están en td dentro de buttons
        "selector_precio": "button td, button table td",
        "selector_promo": ".promo, .oferta, .discount, [class*='promo']",
        "usa_playwright": True,
        "activo": True,
    },
    {
        "nombre": "Pollo Campestre",
        # URL del menú
        "url": "https://pollocampestre.com.sv/menu-ref/2",
        # Selector encontrado: precios usan clase text-rojo
        "selector_precio": "p.text-rojo, .text-rojo",
        "selector_promo": ".promo, .oferta, [class*='promo']",
        "usa_playwright": True,
        "activo": True,
    },
    {
        "nombre": "Pollo Campero (Referencia)",
        # Nota: Este sitio requiere seleccionar tienda antes de ver precios
        # Por ahora lo dejamos inactivo hasta implementar flujo completo
        "url": "https://sv.campero.com/menu/productos-nuevos",
        "selector_precio": ".product-price-content span, .product-price",
        "selector_promo": ".promo, .oferta, [class*='promo']",
        "usa_playwright": True,
        "activo": False,  # Requiere selección de tienda - flujo complejo
    },
]


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def pausa_aleatoria(minimo: float = 2.0, maximo: float = 5.0) -> None:
    """
    Pausa aleatoria entre peticiones para evitar ser bloqueado.
    
    Args:
        minimo: Segundos mínimos de espera
        maximo: Segundos máximos de espera
    """
    tiempo = random.uniform(minimo, maximo)
    print(f"   ⏳ Esperando {tiempo:.1f} segundos...")
    time.sleep(tiempo)


def limpiar_precio(texto_precio: str) -> Optional[float]:
    """
    Extrae el valor numérico de un texto de precio.
    Maneja formatos como: "$5.99", "USD 5.99", "5,99", etc.
    
    Args:
        texto_precio: Texto que contiene el precio
        
    Returns:
        Precio como float o None si no se puede extraer
    """
    if not texto_precio:
        return None
    
    # Limpiar el texto
    texto = texto_precio.strip()
    
    # Buscar patrones de precio (números con decimales)
    patron = r"[\d]+[.,]?\d*"
    coincidencias = re.findall(patron, texto)
    
    if coincidencias:
        # Tomar el primer número encontrado
        precio_str = coincidencias[0].replace(",", ".")
        try:
            return float(precio_str)
        except ValueError:
            return None
    
    return None


def obtener_timestamp() -> str:
    """Retorna timestamp formateado para logs y archivos."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# MOTOR DE SCRAPING
# =============================================================================

def obtener_html_requests(url: str) -> Optional[str]:
    """
    Obtiene el HTML de una página usando Requests (para sitios estáticos).
    
    Args:
        url: URL del sitio a scrapear
        
    Returns:
        HTML como string o None si hay error
    """
    try:
        response = requests.get(
            url, 
            headers=HEADERS_NAVEGADOR, 
            timeout=30,
            allow_redirects=True
        )
        response.raise_for_status()
        return response.text
    
    except requests.exceptions.Timeout:
        print(f"   ⚠️  Timeout al conectar con {url}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Error de conexión con {url}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"   ⚠️  Error HTTP {e.response.status_code} en {url}")
        return None
    except Exception as e:
        print(f"   ⚠️  Error inesperado: {str(e)}")
        return None


def obtener_html_playwright(url: str) -> Optional[str]:
    """
    Obtiene HTML usando Playwright para sitios con JavaScript.
    
    Args:
        url: URL del sitio a scrapear
        
    Returns:
        HTML como string o None si hay error
    """
    from playwright.sync_api import sync_playwright
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(HEADERS_NAVEGADOR)
            page.goto(url, wait_until="networkidle", timeout=60000)
            # Esperar a que cargue el contenido dinámico
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"   ⚠️  Error con Playwright: {str(e)}")
        return None


def extraer_precio(html: str, selector: str) -> Optional[float]:
    """
    Extrae el precio de una página HTML usando el selector CSS.
    
    Args:
        html: Contenido HTML de la página
        selector: Selector CSS para encontrar el elemento del precio
        
    Returns:
        Precio como float o None si no se encuentra
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        
        # Intentar encontrar el precio con el selector
        elementos = soup.select(selector)
        
        for elemento in elementos:
            texto = elemento.get_text(strip=True)
            precio = limpiar_precio(texto)
            if precio and precio > 0:
                return precio
        
        # Si no encuentra con el selector, buscar patrones de precio en todo el HTML
        texto_completo = soup.get_text()
        patron_precio = r"\$\s*(\d+[.,]\d{2})"
        coincidencias = re.findall(patron_precio, texto_completo)
        
        if coincidencias:
            return float(coincidencias[0].replace(",", "."))
        
        return None
        
    except Exception as e:
        print(f"   ⚠️  Error al extraer precio: {str(e)}")
        return None


def clasificar_producto(nombre_producto: str) -> Optional[str]:
    """
    Clasifica un producto en una categoría basándose en su nombre.
    
    Args:
        nombre_producto: Nombre del producto
        
    Returns:
        ID de categoría o None si no aplica
    """
    nombre_lower = nombre_producto.lower()
    
    for categoria_id, config in CATEGORIAS_PRODUCTOS.items():
        # Verificar si tiene palabras a excluir
        tiene_exclusion = any(excl in nombre_lower for excl in config["excluir"])
        if tiene_exclusion:
            continue
        
        # Verificar si tiene keywords de la categoría
        tiene_keyword = any(kw in nombre_lower for kw in config["keywords"])
        if tiene_keyword:
            return categoria_id
    
    return None


def extraer_productos_kfc(html: str) -> List[Dict[str, Any]]:
    """
    Extrae productos de KFC usando búsqueda heurística por precios ($) y keywords.
    Robusto contra clases CSS dinámicas/ofuscadas.
    """
    productos = []
    try:
        soup = BeautifulSoup(html, "lxml")
        
        # Estrategia: Buscar todos los elementos de texto que parecen precios
        # Regex para $10.50, $ 10.50, 10.50
        precio_pattern = re.compile(r"\$\s*\d+\.\d{2}")
        precios_found = soup.find_all(string=precio_pattern)
        
        for precio_node in precios_found:
            try:
                # El nodo de texto es hijo de alguien. Subamos buscando contexto.
                contenedor = precio_node.parent
                
                # Subir hasta 6 niveles buscando un contenedor que tenga texto de producto
                nombre_encontrado = None
                precio_float = limpiar_precio(precio_node)
                
                if not precio_float or precio_float <= 0:
                    continue
                    
                # Buscar en los padres
                temp_pointer = contenedor
                for _ in range(6): 
                    if not temp_pointer: break
                    
                    texto_completo = temp_pointer.get_text(" ", strip=True)
                    
                    # Intentar clasificar con el texto acumulado del contenedor
                    categoria = clasificar_producto(texto_completo)
                    
                    if categoria:
                        # Limpiar el nombre (tomar primeros 50 chars o algo razonable si es muy largo)
                        nombre_limpio = texto_completo.split("$")[0].strip() # Cortar antes del precio si aparece
                        if len(nombre_limpio) > 60:
                            nombre_limpio = nombre_limpio[:60] + "..."
                            
                        productos.append({
                            "nombre": nombre_limpio,
                            "precio": precio_float,
                            "categoria": categoria,
                            "categoria_nombre": CATEGORIAS_PRODUCTOS[categoria]["nombre"]
                        })
                        break # Ya clasificamos este precio, siguiente.
                    
                    temp_pointer = temp_pointer.parent
                    
            except Exception:
                continue
                
        # Eliminar duplicados exactos
        productos_unicos = []
        vistos = set()
        for p in productos:
            key = (p["categoria"], p["precio"])
            if key not in vistos:
                vistos.add(key)
                productos_unicos.append(p)
                
    except Exception as e:
        print(f"   ⚠️  Error extrayendo productos KFC (Heurística): {str(e)}")
    
    return productos_unicos


def extraer_productos_campestre(html: str) -> List[Dict[str, Any]]:
    """
    Extrae productos de Campestre usando búsqueda heurística (igual que KFC).
    """
    productos = []
    try:
        soup = BeautifulSoup(html, "lxml")
        
        # Estrategia: Buscar precios ($)
        precio_pattern = re.compile(r"\$\s*\d+\.\d{2}")
        precios_found = soup.find_all(string=precio_pattern)
        
        for precio_node in precios_found:
            try:
                contenedor = precio_node.parent
                precio_float = limpiar_precio(precio_node)
                
                if not precio_float or precio_float <= 0:
                    continue
                    
                temp_pointer = contenedor
                for _ in range(6): 
                    if not temp_pointer: break
                    
                    texto_completo = temp_pointer.get_text(" ", strip=True)
                    categoria = clasificar_producto(texto_completo)
                    
                    if categoria:
                        nombre_limpio = texto_completo.split("$")[0].strip()
                        if len(nombre_limpio) > 60:
                            nombre_limpio = nombre_limpio[:60] + "..."
                            
                        productos.append({
                            "nombre": nombre_limpio,
                            "precio": precio_float,
                            "categoria": categoria,
                            "categoria_nombre": CATEGORIAS_PRODUCTOS[categoria]["nombre"]
                        })
                        break
                    
                    temp_pointer = temp_pointer.parent
                    
            except Exception:
                continue
                
        # Eliminar duplicados
        productos_unicos = []
        vistos = set()
        for p in productos:
            key = (p["categoria"], p["precio"])
            if key not in vistos:
                vistos.add(key)
                productos_unicos.append(p)
                
    except Exception as e:
        print(f"   ⚠️  Error extrayendo productos Campestre (Heurística): {str(e)}")
    
    return productos_unicos


def comparar_con_campero(productos: List[Dict], competidor: str) -> List[Dict]:
    """
    Compara productos encontrados con los precios de referencia de Campero.
    
    Returns:
        Lista de alertas cuando un competidor tiene precio menor
    """
    alertas = []
    
    for producto in productos:
        categoria = producto["categoria"]
        
        if categoria in PRECIOS_REFERENCIA_CAMPERO:
            precio_campero = PRECIOS_REFERENCIA_CAMPERO[categoria]["precio"]
            precio_competidor = producto["precio"]
            
            if precio_competidor < precio_campero:
                diferencia = precio_campero - precio_competidor
                porcentaje = (diferencia / precio_campero) * 100
                
                alertas.append({
                    "tipo": "competidor_mas_barato",
                    "competidor": competidor,
                    "producto": producto["nombre"],
                    "categoria": producto["categoria_nombre"],
                    "precio_competidor": precio_competidor,
                    "precio_campero": precio_campero,
                    "diferencia": diferencia,
                    "porcentaje": porcentaje,
                })
    
    return alertas


def detectar_promociones(html: str, keywords: List[str] = None) -> List[str]:
    """
    Detecta palabras clave de promoción en el HTML.
    
    Args:
        html: Contenido HTML de la página
        keywords: Lista de palabras clave a buscar
        
    Returns:
        Lista de keywords encontradas
    """
    if keywords is None:
        keywords = KEYWORDS_PROMOCION
    
    encontradas = []
    
    try:
        soup = BeautifulSoup(html, "lxml")
        texto = soup.get_text().lower()
        
        for keyword in keywords:
            if keyword.lower() in texto:
                encontradas.append(keyword)
        
    except Exception as e:
        print(f"   ⚠️  Error al detectar promociones: {str(e)}")
    
    return encontradas


# =============================================================================
# PERSISTENCIA DE DATOS
# =============================================================================

def cargar_historial() -> Dict[str, Any]:
    """
    Carga el historial de precios desde el archivo JSON.
    
    Returns:
        Diccionario con el historial o vacío si no existe
    """
    try:
        if os.path.exists(ARCHIVO_HISTORIAL):
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️  Error al cargar historial: {str(e)}")
    
    return {"competidores": {}, "ultima_actualizacion": None}


def guardar_historial(historial: Dict[str, Any]) -> bool:
    """
    Guarda el historial de precios en el archivo JSON.
    
    Args:
        historial: Diccionario con los datos a guardar
        
    Returns:
        True si se guardó correctamente, False en caso contrario
    """
    try:
        historial["ultima_actualizacion"] = obtener_timestamp()
        
        with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)
        
        return True
        
    except IOError as e:
        print(f"⚠️  Error al guardar historial: {str(e)}")
        return False


def actualizar_precio_historial(
    historial: Dict[str, Any], 
    nombre: str, 
    precio: float,
    promociones: List[str]
) -> Dict[str, Any]:
    """
    Actualiza el precio de un competidor en el historial.
    
    Args:
        historial: Diccionario del historial actual
        nombre: Nombre del competidor
        precio: Nuevo precio detectado
        promociones: Lista de promociones detectadas
        
    Returns:
        Historial actualizado con el precio anterior para comparación
    """
    if nombre not in historial["competidores"]:
        historial["competidores"][nombre] = {
            "precio_anterior": None,
            "precio_actual": precio,
            "promociones": promociones,
            "historial_precios": [],
            "ultima_revision": obtener_timestamp()
        }
    else:
        # Mover el precio actual al anterior
        historial["competidores"][nombre]["precio_anterior"] = \
            historial["competidores"][nombre]["precio_actual"]
        historial["competidores"][nombre]["precio_actual"] = precio
        historial["competidores"][nombre]["promociones"] = promociones
        historial["competidores"][nombre]["ultima_revision"] = obtener_timestamp()
        
        # Guardar en historial de precios (mantener últimos 100)
        historial["competidores"][nombre]["historial_precios"].append({
            "precio": precio,
            "fecha": obtener_timestamp()
        })
        historial["competidores"][nombre]["historial_precios"] = \
            historial["competidores"][nombre]["historial_precios"][-100:]
    
    return historial


# =============================================================================
# SISTEMA DE NOTIFICACIONES - TELEGRAM
# =============================================================================

def enviar_telegram(mensaje: str) -> bool:
    """
    Envía un mensaje a través del Bot de Telegram.
    
    Configuración previa requerida:
    1. Crear bot con @BotFather en Telegram
    2. Obtener el TOKEN del bot
    3. Obtener tu CHAT_ID (envía mensaje al bot y visita:
       https://api.telegram.org/bot<TOKEN>/getUpdates)
    4. Configurar TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env
    
    Args:
        mensaje: Texto del mensaje a enviar
        
    Returns:
        True si se envió correctamente, False en caso contrario
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram no configurado. Mensaje no enviado.")
        print(f"   Mensaje: {mensaje[:100]}...")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML"  # Permite formato HTML en el mensaje
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Mensaje enviado a Telegram correctamente")
            return True
        else:
            print(f"⚠️  Error al enviar a Telegram: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"⚠️  Error de conexión con Telegram: {str(e)}")
        return False


def formatear_alerta(
    nombre: str, 
    precio_actual: float, 
    precio_anterior: Optional[float],
    promociones: List[str],
    tipo_alerta: str
) -> str:
    """
    Formatea el mensaje de alerta para Telegram.
    
    Args:
        nombre: Nombre del competidor
        precio_actual: Precio detectado actualmente
        precio_anterior: Precio anterior guardado
        promociones: Lista de promociones encontradas
        tipo_alerta: Tipo de alerta (PRECIO_BAJO, PROMOCION, etc.)
        
    Returns:
        Mensaje formateado en HTML para Telegram
    """
    emoji = "🚨" if tipo_alerta == "PRECIO_BAJO" else "🎯"
    
    mensaje = f"""
{emoji} <b>ALERTA: {tipo_alerta}</b> {emoji}

🏪 <b>Competidor:</b> {nombre}
💰 <b>Precio Actual:</b> ${precio_actual:.2f}
"""
    
    if precio_anterior:
        diferencia = precio_anterior - precio_actual
        porcentaje = (diferencia / precio_anterior) * 100
        mensaje += f"📉 <b>Precio Anterior:</b> ${precio_anterior:.2f}\n"
        mensaje += f"💥 <b>Diferencia:</b> -${diferencia:.2f} ({porcentaje:.1f}% menos)\n"
    
    if promociones:
        mensaje += f"\n🏷️ <b>Promociones detectadas:</b> {', '.join(promociones)}\n"
    
    mensaje += f"\n⏰ <i>{obtener_timestamp()}</i>"
    
    return mensaje


def formatear_alerta_comparacion(alerta: Dict[str, Any]) -> str:
    """
    Formatea mensaje de alerta cuando competidor está más barato que Campero.
    
    Args:
        alerta: Diccionario con datos de la alerta de comparación
        
    Returns:
        Mensaje formateado en HTML para Telegram
    """
    mensaje = f"""
⚠️ <b>ALERTA: COMPETIDOR MÁS BARATO</b> ⚠️

🏪 <b>Competidor:</b> {alerta['competidor']}
📦 <b>Producto:</b> {alerta['producto']}
📂 <b>Categoría:</b> {alerta['categoria']}

💰 <b>Precio Competidor:</b> ${alerta['precio_competidor']:.2f}
🐔 <b>Precio Campero:</b> ${alerta['precio_campero']:.2f}

💥 <b>Diferencia:</b> ${alerta['diferencia']:.2f} menos ({alerta['porcentaje']:.1f}%)

⏰ <i>{obtener_timestamp()}</i>
"""
    return mensaje


# =============================================================================
# LÓGICA PRINCIPAL DE MONITOREO
# =============================================================================

def revisar_competidor(competidor: Dict[str, Any], historial: Dict[str, Any]) -> Dict[str, Any]:
    """
    Revisa un competidor individual y genera alertas si corresponde.
    Ahora extrae productos por categoría y compara con precios de Campero.
    
    Args:
        competidor: Diccionario con datos del competidor
        historial: Historial de precios actual
        
    Returns:
        Historial actualizado
    """
    nombre = competidor["nombre"]
    url = competidor["url"]
    selector = competidor["selector_precio"]
    usa_playwright = competidor.get("usa_playwright", False)
    
    print(f"\n🔍 Revisando: {nombre}")
    print(f"   URL: {url}")
    
    # Obtener HTML según el método configurado
    if usa_playwright:
        html = obtener_html_playwright(url)
    else:
        html = obtener_html_requests(url)
    
    if not html:
        print(f"   ❌ No se pudo obtener el HTML de {nombre}")
        return historial
    
    # =========================================================================
    # EXTRACCIÓN DE PRODUCTOS POR CATEGORÍA
    # =========================================================================
    
    productos = []
    
    # Usar extractor específico según el competidor
    if "KFC" in nombre:
        productos = extraer_productos_kfc(html)
    elif "Campestre" in nombre:
        productos = extraer_productos_campestre(html)
    else:
        # Extracción genérica para otros competidores
        precio = extraer_precio(html, selector)
        if precio:
            productos = [{"nombre": nombre, "precio": precio, "categoria": None, "categoria_nombre": "General"}]
    
    if not productos:
        # Fallback: intentar extracción genérica
        precio = extraer_precio(html, selector)
        if precio:
            print(f"   � Precio genérico encontrado: ${precio:.2f}")
        else:
            print(f"   ⚠️  No se encontraron productos en {nombre}")
        return historial
    
    # Mostrar productos encontrados
    print(f"   � Productos encontrados: {len(productos)}")
    for p in productos[:5]:  # Mostrar máximo 5
        print(f"      • {p['categoria_nombre']}: {p['nombre']} - ${p['precio']:.2f}")
    
    # Detectar promociones
    promociones = detectar_promociones(html)
    
    if promociones:
        print(f"   🏷️  Promociones: {', '.join(promociones)}")
    
    # =========================================================================
    # COMPARACIÓN CON PRECIOS DE CAMPERO
    # =========================================================================
    
    alertas_comparacion = comparar_con_campero(productos, nombre)
    
    for alerta in alertas_comparacion:
        print(f"   ⚠️  ¡{nombre} más barato en {alerta['categoria']}!")
        print(f"      Competidor: ${alerta['precio_competidor']:.2f} vs Campero: ${alerta['precio_campero']:.2f}")
        
        # Enviar alerta a Telegram
        mensaje = formatear_alerta_comparacion(alerta)
        enviar_telegram(mensaje)
    
    # =========================================================================
    # ACTUALIZAR HISTORIAL CON PRODUCTOS CATEGORIZADOS
    # =========================================================================
    
    # Guardar el producto más relevante por categoría
    for producto in productos:
        key = f"{nombre} - {producto['categoria_nombre']}"
        
        precio_anterior = None
        if key in historial["competidores"]:
            precio_anterior = historial["competidores"][key].get("precio_actual")
        
        historial = actualizar_precio_historial(
            historial, key, producto["precio"], promociones
        )
        
        # Alerta de cambio de precio (bajó respecto a antes)
        if precio_anterior and producto["precio"] < precio_anterior:
            diferencia = precio_anterior - producto["precio"]
            print(f"   📉 ¡{key} bajó ${diferencia:.2f}!")
            
            mensaje = formatear_alerta(
                key, producto["precio"], precio_anterior, promociones, "PRECIO_BAJO"
            )
            enviar_telegram(mensaje)
    
    return historial


def revisar_todos_los_competidores() -> None:
    """
    Función principal que revisa todos los competidores activos.
    Esta función es llamada por el scheduler cada 4 horas.
    """
    # Verificar horario de operación
    hora_actual = datetime.now().hour
    
    # Lógica simple para rango de horas
    en_horario = False
    if HORA_INICIO < HORA_FIN:
        # Rango normal (ej: 8 a 19)
        if HORA_INICIO <= hora_actual < HORA_FIN:
            en_horario = True
    else:
        # Rango que cruza medianoche (ej: 22 a 06)
        if hora_actual >= HORA_INICIO or hora_actual < HORA_FIN:
            en_horario = True
            
    if not en_horario:
        print("\n" + "=" * 60)
        print(f"💤 MONITOR EN PAUSA - {obtener_timestamp()}")
        print(f"   Hora actual: {hora_actual}:00")
        print(f"   Horario operativo: {HORA_INICIO}:00 - {HORA_FIN}:00")
        print("=" * 60 + "\n")
        return

    print("\n" + "=" * 60)
    print(f"🕐 INICIANDO REVISIÓN - {obtener_timestamp()}")
    print("=" * 60)
    
    # Cargar historial existente
    historial = cargar_historial()
    
    # Contador de competidores procesados
    procesados = 0
    errores = 0
    
    for competidor in COMPETIDORES:
        # Saltar competidores inactivos
        if not competidor.get("activo", True):
            print(f"\n⏭️  Saltando {competidor['nombre']} (inactivo)")
            continue
        
        try:
            historial = revisar_competidor(competidor, historial)
            procesados += 1
            
        except Exception as e:
            print(f"\n❌ Error al revisar {competidor['nombre']}: {str(e)}")
            errores += 1
            # El script continúa con el siguiente competidor
            continue
        
        # Pausa entre peticiones para evitar bloqueos
        pausa_aleatoria()
    
    # Guardar historial actualizado
    if guardar_historial(historial):
        print(f"\n💾 Historial guardado en {ARCHIVO_HISTORIAL}")
    
    # Resumen
    print("\n" + "-" * 60)
    print(f"📊 RESUMEN: {procesados} procesados, {errores} errores")
    print(f"⏰ Próxima revisión en {INTERVALO_HORAS} horas")
    print("=" * 60 + "\n")


# =============================================================================
# SCHEDULER - AUTOMATIZACIÓN CONFIGURABLE
# =============================================================================

def iniciar_scheduler() -> None:
    """
    Inicia el scheduler para ejecutar la revisión según INTERVALO_HORAS.
    """
    print("\n" + "=" * 60)
    print("🚀 MONITOR DE PRECIOS - INICIADO")
    print("=" * 60)
    print(f"⏰ Revisiones programadas cada {INTERVALO_HORAS} hora(s)")
    print(f"📍 Competidores configurados: {len([c for c in COMPETIDORES if c.get('activo', True)])}")
    print(f"📁 Archivo de historial: {ARCHIVO_HISTORIAL}")
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("✅ Notificaciones de Telegram: CONFIGURADAS")
    else:
        print("⚠️  Notificaciones de Telegram: NO CONFIGURADAS")
    
    print("=" * 60)
    
    # Ejecutar inmediatamente al iniciar
    revisar_todos_los_competidores()
    
    # Programar ejecución según intervalo configurado
    schedule.every(INTERVALO_HORAS).hours.do(revisar_todos_los_competidores)
    
    # Loop principal
    print("\n🔄 Scheduler activo. Presiona Ctrl+C para detener.\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitor detenido por el usuario.")


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    iniciar_scheduler()
