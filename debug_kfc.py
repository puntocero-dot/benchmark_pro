from playwright.sync_api import sync_playwright
import time

def capture_debug_info():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Headers para evitar bloqueo
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        print("Navegando a KFC...")
        page.goto('https://www.kfc.com.sv/categorias', wait_until='networkidle', timeout=60000)
        time.sleep(5)
        page.screenshot(path='kfc_debug.png')
        with open('kfc_debug.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        print("KFC capturado.")
        
        print("Navegando a Campestre...")
        page.goto('https://pollocampestre.com.sv/menu-ref/2', wait_until='networkidle', timeout=60000)
        time.sleep(5)
        page.screenshot(path='campestre_debug.png')
        with open('campestre_debug.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        print("Campestre capturado.")
        
        browser.close()

if __name__ == "__main__":
    capture_debug_info()
