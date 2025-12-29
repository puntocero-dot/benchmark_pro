
import os
import json
import time
import schedule
import copy
from datetime import datetime
from typing import List, Dict

# Config & Core
from price_monitor_v2.config.settings import (
    COMPETITORS, ARCHIVO_HISTORIAL, PRECIOS_REFERENCIA_CAMPERO,
    INTERVALO_HORAS, HORA_INICIO, HORA_FIN
)
from price_monitor_v2.core.network import NetworkManager
from price_monitor_v2.core.notifier import send_telegram_alert
from price_monitor_v2.utils.helpers import detect_promotions
from price_monitor_v2.utils.report_generator import generate_html_report

# Parsers
from price_monitor_v2.parsers.kfc import KFCParser
from price_monitor_v2.parsers.campero import CamperoParser
from price_monitor_v2.parsers.campestre import CampestreParser

PARSER_MAP = {
    "KFCParser": KFCParser,
    "CamperoParser": CamperoParser,
    "CampestreParser": CampestreParser
}

def load_history():
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"competidores": {}}

def save_history(history):
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def compare_prices(products: List[Dict], competitor_name: str, references: Dict):
    """
    Compares extracted products with Reference Prices (Campero).
    """
    # Skip comparison if we are comparing Campero against itself
    if "Campero" in competitor_name:
        return

    for p in products:
        cat = p["categoria"]
        if cat in references:
            ref = references[cat]
            price_campero = ref["precio"]
            price_comp = p["precio"]
            
            if price_comp < price_campero:
                diff = price_campero - price_comp
                pct = (diff / price_campero) * 100
                
                msg = (
                    f"📉 <b>¡{competitor_name} es más barato!</b>\n"
                    f"Categoría: {p['categoria_nombre']}\n"
                    f"Producto: {p['nombre']}\n"
                    f"Precio: ${price_comp:.2f} (Campero: ${price_campero:.2f})\n"
                    f"Ahorro: ${diff:.2f} ({pct:.0f}%)"
                )
                print(f"   [Alert] {competitor_name} cheaper in {cat}")
                send_telegram_alert(msg)

def update_history(history, competitor_name, products, promos):
    """
    Updates history with latest prices.
    """
    if competitor_name not in history["competidores"]:
        history["competidores"][competitor_name] = {"historial_precios": []}
    
    comp_hist = history["competidores"][competitor_name]
    comp_hist["ultima_revision"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comp_hist["productos_detectados"] = len(products)
    comp_hist["productos_actuales"] = products # Persist for Dashboard
    comp_hist["promociones_activas"] = list(promos) # Store Promos
    return history

def run_monitor():
    print(f"\n==============================================")
    print(f"Starting Price Monitor... Time: {datetime.now()}")
    print(f"==============================================")
    
    network = NetworkManager()
    history = load_history()
    
    # Initialize references with fallback
    current_references = copy.deepcopy(PRECIOS_REFERENCIA_CAMPERO)
    
    for comp in COMPETITORS:
        if not comp.get("active"):
            continue
            
        name = comp["name"]
        url = comp["url"]
        parser_cls = PARSER_MAP.get(comp["parser"])
        
        if not parser_cls:
            print(f"Unknown parser for {name}")
            continue
            
        print(f"\n[+] Checking {name}")
        parser = parser_cls(network)
        
        all_products = []
        current_url = url
        page_count = 0
        found_promos = set()
        
        # Pagination Loop
        while current_url and page_count < 5: 
            print(f"   Fetching: {current_url}")
            content = parser.fetch_data(current_url)
            if not content:
                print("   Failed to fetch content")
                break
            
            # Extract Products
            products = parser.extract_products(content)
            all_products.extend(products)
            
            # Extract Promotions
            promos = detect_promotions(content)
            for p in promos:
                found_promos.add(p)

            print(f"   Found {len(products)} products on page {page_count + 1}")
            
            # Check for next page
            next_link = parser.detect_pagination(content)
            if next_link and next_link != current_url:
                current_url = next_link
                page_count += 1
                time.sleep(2)
            else:
                break
        
        # Deduplicate globally
        unique_products = []
        seen = set()
        for p in all_products:
            k = (p["categoria"], p["precio"])
            if k not in seen:
                seen.add(k)
                unique_products.append(p)
        
        print(f"   Total Unique Products: {len(unique_products)}")
        
        # Update References if this is the Reference Competitor
        if comp.get("is_reference") and unique_products:
            print("   [Ref] Updating Reference Prices from Live Data...")
            for p in unique_products:
                cat = p["categoria"]
                # Only update if category matches known reference structure
                if cat in current_references:
                    old_price = current_references[cat]["precio"]
                    new_price = p["precio"]
                    if new_price != old_price:
                        print(f"      {cat}: ${old_price} -> ${new_price}")
                        current_references[cat]["precio"] = new_price

        # Notify Promotions
        if found_promos:
            msg = f"🏷️ <b>Promociones en {name}</b>: {', '.join(found_promos)}"
            print(f"   [Promos] {', '.join(found_promos)}")
            send_telegram_alert(msg)
        
        if unique_products:
            compare_prices(unique_products, name, current_references)
            update_history(history, name, unique_products, found_promos)
            
    save_history(history)
    generate_html_report(history)
    print("\nMonitor Cycle Completed.\n")

if __name__ == "__main__":
    print(f"Service Started. Running every {INTERVALO_HORAS} hours.")
    
    # Run once immediately
    job_func = run_monitor
    job_func()
    
    # Schedule
    schedule.every(INTERVALO_HORAS).hours.do(job_func)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("Service Stopped.")
