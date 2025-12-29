# -*- coding: utf-8 -*-
"""
=============================================================================
DASHBOARD WEB - MONITOR DE PRECIOS
=============================================================================
Servidor web simple para visualizar el estado del monitor de precios.
Usa Flask para servir una interfaz web con los datos del historial.
=============================================================================
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify

# Configuración
ARCHIVO_HISTORIAL = "precios_historial.json"
PORT = int(os.getenv("PORT", 5000))

app = Flask(__name__)

# Template HTML del dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor de Precios - Dashboard</title>
    <style>
        :root {
            --bg-primary: #0f0f23;
            --bg-secondary: #1a1a2e;
            --bg-card: #16213e;
            --accent: #e94560;
            --accent-secondary: #0f3460;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --success: #00d26a;
            --warning: #ffc107;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: var(--bg-card);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(233, 69, 96, 0.1);
        }
        
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, var(--accent), #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: var(--bg-secondary);
            border-radius: 50px;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .status-dot.active { background: var(--success); }
        .status-dot.inactive { background: var(--warning); }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }
        
        .card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s, box-shadow 0.3s;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(233, 69, 96, 0.2);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .card-title {
            font-size: 1.3rem;
            font-weight: 600;
        }
        
        .card-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .badge-active {
            background: rgba(0, 210, 106, 0.2);
            color: var(--success);
        }
        
        .badge-inactive {
            background: rgba(255, 193, 7, 0.2);
            color: var(--warning);
        }
        
        .price-display {
            text-align: center;
            padding: 20px 0;
        }
        
        .price-current {
            font-size: 3rem;
            font-weight: 700;
            color: var(--accent);
        }
        
        .price-previous {
            color: var(--text-secondary);
            font-size: 1rem;
            margin-top: 5px;
        }
        
        .price-change {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            margin-top: 10px;
            font-weight: 600;
        }
        
        .change-down {
            background: rgba(0, 210, 106, 0.2);
            color: var(--success);
        }
        
        .change-up {
            background: rgba(233, 69, 96, 0.2);
            color: var(--accent);
        }
        
        .card-footer {
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        
        .promos {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 15px;
        }
        
        .promo-tag {
            background: linear-gradient(135deg, var(--accent), #ff6b6b);
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .no-data {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
        }
        
        .no-data-icon {
            font-size: 4rem;
            margin-bottom: 20px;
        }
        
        .refresh-btn {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 30px;
            background: var(--accent);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 600;
            transition: background 0.3s;
        }
        
        .refresh-btn:hover {
            background: #ff6b6b;
        }
        
        footer {
            text-align: center;
            padding: 30px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        @media (max-width: 600px) {
            h1 { font-size: 1.8rem; }
            .price-current { font-size: 2.5rem; }
            .cards-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Monitor de Precios</h1>
            <p class="subtitle">Seguimiento de competidores en El Salvador</p>
            <div class="status-bar">
                <div class="status-item">
                    <span class="status-dot active"></span>
                    <span>Sistema Activo</span>
                </div>
                <div class="status-item">
                    <span>⏰ Cada 4 horas</span>
                </div>
                <div class="status-item">
                    <span>📅 {{ ultima_actualizacion or 'Sin datos' }}</span>
                </div>
            </div>
        </header>
        
        {% if competidores %}
        <div class="cards-grid">
            {% for nombre, datos in competidores.items() %}
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">{{ nombre }}</h2>
                    <span class="card-badge badge-active">Activo</span>
                </div>
                
                <div class="price-display">
                    {% if datos.precio_actual %}
                    <div class="price-current">${{ "%.2f"|format(datos.precio_actual) }}</div>
                    {% if datos.precio_anterior %}
                    <div class="price-previous">Anterior: ${{ "%.2f"|format(datos.precio_anterior) }}</div>
                    {% set diff = datos.precio_anterior - datos.precio_actual %}
                    {% if diff > 0 %}
                    <span class="price-change change-down">↓ ${{ "%.2f"|format(diff) }} menos</span>
                    {% elif diff < 0 %}
                    <span class="price-change change-up">↑ ${{ "%.2f"|format(-diff) }} más</span>
                    {% endif %}
                    {% endif %}
                    {% else %}
                    <div class="price-current">--</div>
                    <div class="price-previous">Sin precio detectado</div>
                    {% endif %}
                </div>
                
                {% if datos.promociones %}
                <div class="promos">
                    {% for promo in datos.promociones %}
                    <span class="promo-tag">🏷️ {{ promo }}</span>
                    {% endfor %}
                </div>
                {% endif %}
                
                <div class="card-footer">
                    🕐 Última revisión: {{ datos.ultima_revision or 'Nunca' }}
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="no-data">
            <div class="no-data-icon">📊</div>
            <h2>Sin datos aún</h2>
            <p>El monitor no ha recolectado datos todavía.</p>
            <a href="/" class="refresh-btn">🔄 Actualizar</a>
        </div>
        {% endif %}
        
        <footer>
            <p>Monitor de Precios v1.0 | El Salvador</p>
            <p>KFC • Pollo Campestre • Pollo Campero</p>
        </footer>
    </div>
    
    <script>
        // Auto-refresh cada 5 minutos
        setTimeout(() => location.reload(), 300000);
    </script>
</body>
</html>
"""


def cargar_historial():
    """Carga el historial de precios desde el archivo JSON."""
    try:
        if os.path.exists(ARCHIVO_HISTORIAL):
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {"competidores": {}, "ultima_actualizacion": None}


@app.route("/")
def dashboard():
    """Página principal del dashboard."""
    historial = cargar_historial()
    return render_template_string(
        DASHBOARD_HTML,
        competidores=historial.get("competidores", {}),
        ultima_actualizacion=historial.get("ultima_actualizacion")
    )


@app.route("/api/status")
def api_status():
    """Endpoint JSON con el estado actual."""
    historial = cargar_historial()
    return jsonify({
        "status": "ok",
        "ultima_actualizacion": historial.get("ultima_actualizacion"),
        "competidores": historial.get("competidores", {}),
        "total_competidores": len(historial.get("competidores", {}))
    })


@app.route("/health")
def health():
    """Health check para Railway/monitoreo."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


if __name__ == "__main__":
    print(f"🌐 Dashboard iniciando en http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
