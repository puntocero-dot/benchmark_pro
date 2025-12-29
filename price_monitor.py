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

# Archivo para persistencia de datos
ARCHIVO_HISTORIAL = "precios_historial.json"

# Keywords para detectar promociones (case-insensitive)
KEYWORDS_PROMOCION = ["off", "promo", "descuento", "oferta", "2x1", "gratis", "especial"]

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
        # Esto es un fallback para sitios con estructura variable
        texto_completo = soup.get_text()
        patron_precio = r"\$\s*(\d+[.,]\d{2})"
        coincidencias = re.findall(patron_precio, texto_completo)
        
        if coincidencias:
            # Retornar el primer precio encontrado
            return float(coincidencias[0].replace(",", "."))
        
        return None
        
    except Exception as e:
        print(f"   ⚠️  Error al extraer precio: {str(e)}")
        return None


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


# =============================================================================
# LÓGICA PRINCIPAL DE MONITOREO
# =============================================================================

def revisar_competidor(competidor: Dict[str, Any], historial: Dict[str, Any]) -> Dict[str, Any]:
    """
    Revisa un competidor individual y genera alertas si corresponde.
    
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
    
    # Extraer precio
    precio = extraer_precio(html, selector)
    
    if precio is None:
        print(f"   ⚠️  No se encontró precio en {nombre}")
        print(f"   💡 Tip: Verifica el selector CSS o activa Playwright")
        return historial
    
    print(f"   💰 Precio encontrado: ${precio:.2f}")
    
    # Detectar promociones
    promociones = detectar_promociones(html)
    
    if promociones:
        print(f"   🏷️  Promociones detectadas: {', '.join(promociones)}")
    
    # Obtener precio anterior
    precio_anterior = None
    if nombre in historial["competidores"]:
        precio_anterior = historial["competidores"][nombre].get("precio_actual")
    
    # Actualizar historial
    historial = actualizar_precio_historial(historial, nombre, precio, promociones)
    
    # =========================================================================
    # LÓGICA DE ALERTAS
    # =========================================================================
    
    alerta_enviada = False
    
    # Alerta 1: Precio menor al anterior
    if precio_anterior and precio < precio_anterior:
        print(f"   🚨 ¡ALERTA! Precio bajó de ${precio_anterior:.2f} a ${precio:.2f}")
        
        mensaje = formatear_alerta(
            nombre, precio, precio_anterior, promociones, "PRECIO_BAJO"
        )
        enviar_telegram(mensaje)
        alerta_enviada = True
    
    # Alerta 2: Promoción detectada (solo si no se envió alerta de precio)
    if promociones and not alerta_enviada:
        print(f"   🎯 ¡PROMOCIÓN DETECTADA!")
        
        mensaje = formatear_alerta(
            nombre, precio, precio_anterior, promociones, "PROMOCIÓN"
        )
        enviar_telegram(mensaje)
    
    return historial


def revisar_todos_los_competidores() -> None:
    """
    Función principal que revisa todos los competidores activos.
    Esta función es llamada por el scheduler cada 4 horas.
    """
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
    print(f"⏰ Próxima revisión en 4 horas")
    print("=" * 60 + "\n")


# =============================================================================
# SCHEDULER - AUTOMATIZACIÓN CADA 4 HORAS
# =============================================================================

def iniciar_scheduler() -> None:
    """
    Inicia el scheduler para ejecutar la revisión cada 4 horas.
    """
    print("\n" + "=" * 60)
    print("🚀 MONITOR DE PRECIOS - INICIADO")
    print("=" * 60)
    print(f"⏰ Revisiones programadas cada 4 horas")
    print(f"📍 Competidores configurados: {len([c for c in COMPETIDORES if c.get('activo', True)])}")
    print(f"📁 Archivo de historial: {ARCHIVO_HISTORIAL}")
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("✅ Notificaciones de Telegram: CONFIGURADAS")
    else:
        print("⚠️  Notificaciones de Telegram: NO CONFIGURADAS")
    
    print("=" * 60)
    
    # Ejecutar inmediatamente al iniciar
    revisar_todos_los_competidores()
    
    # Programar ejecución cada 4 horas
    schedule.every(4).hours.do(revisar_todos_los_competidores)
    
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
