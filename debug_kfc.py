from playwright.sync_api import sync_playwright
import time

def capture_debug_info():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Headers más completos para evitar bloqueo/hidratación fallida
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"'
        })
        
        print("Navegando a Campestre (/menu-ref/2) para click...")
        page.goto('https://pollocampestre.com.sv/menu-ref/2', wait_until='networkidle', timeout=60000)
        time.sleep(5)
        
        try:
            # Click en el botón de drawer/login
            print("  Intentando abrir drawer/login...")
            # Selector más específico basado en lo que vimos antes
            btn = page.locator("button.drawer-button").first
            btn.wait_for(state="visible", timeout=10000)
            if btn.is_visible():
                btn.click()
                print("  Click realizado en 'Iniciar sesión'. Esperando reacción...")
                time.sleep(3)
                
                # Ver si apareció algo nuevo (textos de modal)
                print("  Buscando opciones tras click...")
                # Buscar botones nuevos visibles
                botones_nuevos = page.locator("button:visible, a:visible").all()
                for b in botones_nuevos[:20]:
                    t = b.inner_text().strip()
                    if t: print(f"    [Post-Click] {t}")
                    
                # Si hay opción 'Ubicación' o 'Dirección'
            else:
                print("  Botón 'Iniciar sesión' no encontrado.")

        except Exception as e:
            print(f"  Error interactuando: {e}")

        # Dump del texto visible
        texto_visible = page.inner_text("body")
        with open('campestre_text.txt', 'w', encoding='utf-8') as f:
            f.write(texto_visible)
            
        page.screenshot(path='campestre_debug.png')
        with open('campestre_debug.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        print("Campestre capturado.")
        
        browser.close()

if __name__ == "__main__":
    capture_debug_info()
