# -*- coding: utf-8 -*-
"""
=============================================================================
RUNNER COMBINADO - MONITOR + DASHBOARD
=============================================================================
Ejecuta tanto el monitor de precios como el dashboard web en paralelo.
=============================================================================
"""

import threading
import os
import time

def run_monitor():
    """Ejecuta el monitor de precios en su propio hilo."""
    # Importar aquí para evitar problemas de circular import
    from price_monitor import iniciar_scheduler
    iniciar_scheduler()

def run_dashboard():
    """Ejecuta el dashboard web."""
    from dashboard import app
    port = int(os.getenv("PORT", 5000))
    # Dar tiempo al monitor para iniciar primero
    time.sleep(5)
    print(f"🌐 Dashboard disponible en http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 INICIANDO SISTEMA COMPLETO")
    print("=" * 60)
    print("📊 Monitor de Precios + Dashboard Web")
    print("=" * 60)
    
    # Iniciar monitor en hilo separado
    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    monitor_thread.start()
    
    # Dashboard en hilo principal (para manejar señales correctamente)
    run_dashboard()
