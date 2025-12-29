# 🔍 Monitor de Precios de Competidores - El Salvador

Sistema automatizado para monitorear precios de **KFC El Salvador** y **Pollo Campestre** comparándolos con **Pollo Campero**.

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Telegram (Opcional pero recomendado)

1. Abre Telegram y busca `@BotFather`
2. Envía `/newbot` y sigue las instrucciones
3. Guarda el **TOKEN** que te proporciona
4. Para obtener tu **CHAT_ID**:
   - Envía cualquier mensaje a tu bot
   - Visita: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Busca `"chat":{"id":XXXXXXXX}` en la respuesta JSON

5. Crea el archivo `.env`:
```bash
cp .env.example .env
# Edita .env con tus valores
```

### 3. Ejecutar

```bash
python price_monitor.py
```

El script revisará los precios inmediatamente y luego cada 4 horas.

---

## ⚙️ Configuración de Competidores

Edita la lista `COMPETIDORES` en `price_monitor.py`:

```python
COMPETIDORES = [
    {
        "nombre": "KFC El Salvador",
        "url": "https://kfc.com.sv/menu",
        "selector_precio": ".price, .precio",  # Selector CSS
        "usa_playwright": False,  # True para sitios con JavaScript
        "activo": True,
    },
    # Agregar más aquí...
]
```

### Selectores CSS comunes:
- `.precio` - Clase "precio"
- `#price` - ID "price"
- `[data-price]` - Atributo data-price
- `.product-card .price span` - Selector anidado

---

## 🚂 Deploy en Railway

### Opción A: Desde GitHub (Recomendado)

1. **Sube el código a GitHub**:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/TU_USUARIO/benchmark-pro.git
git push -u origin main
```

2. **Crea proyecto en Railway**:
   - Ve a [railway.app](https://railway.app)
   - Click en "New Project" → "Deploy from GitHub repo"
   - Selecciona tu repositorio

3. **Configura variables de entorno** en Railway:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

4. **Configura el start command**:
   - En Settings → Deploy → Start Command:
   ```
   python price_monitor.py
   ```

### Opción B: CLI de Railway

```bash
# Instalar CLI
npm install -g @railway/cli

# Login y deploy
railway login
railway init
railway up
```

---

## 📁 Estructura del Proyecto

```
Benchmark_pro/
├── price_monitor.py     # Script principal
├── requirements.txt     # Dependencias
├── .env.example         # Plantilla de configuración
├── .env                 # Tu configuración (NO commitear)
├── precios_historial.json  # Datos guardados (auto-generado)
├── Procfile             # Para Railway
└── README.md
```

---

## 🔧 Sitios con JavaScript

Si un sitio no carga precios (usa JavaScript dinámico):

1. Instala Playwright:
```bash
pip install playwright
playwright install chromium
```

2. Activa en el competidor:
```python
{
    "nombre": "Sitio con JS",
    "usa_playwright": True,  # ← Cambiar a True
    ...
}
```

3. Descomenta el código en la función `obtener_html_playwright()`.

---

## 📊 Datos Guardados

El archivo `precios_historial.json` contiene:

```json
{
  "competidores": {
    "KFC El Salvador": {
      "precio_anterior": 5.99,
      "precio_actual": 4.99,
      "promociones": ["promo", "descuento"],
      "historial_precios": [...]
    }
  },
  "ultima_actualizacion": "2024-12-28 22:55:00"
}
```

---

## 🎯 Alertas

El sistema envía alertas cuando:

- ✅ El precio **baja** respecto al guardado
- ✅ Se detectan keywords: `off`, `promo`, `descuento`, `oferta`, `2x1`, `gratis`, `especial`

---

## 📝 Licencia

MIT - Uso libre
