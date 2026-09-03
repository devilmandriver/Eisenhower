# Eisenhower Matrix — Android (PWA)

Versión web instalable (Progressive Web App) del [Eisenhower Matrix de escritorio](../main.py). Mismos 4 cuadrantes, etiquetas, notas, fecha límite con paso automático de "Schedule" a "Do First" al vencer, e historial de tareas borradas con opción de reusarlas. Pensada para instalarse en el teléfono desde Chrome, sin pasar por Google Play.

Gestos táctiles:
- **Toca una tarea** → abre el menú (fecha, etiqueta, nota, mover a otro cuadrante, eliminar).
- **Mantén pulsada y arrastra** una tarea → la reordena dentro del cuadrante o la mueve a otro.

Los datos se guardan en `localStorage`, por lo que **son propios de cada dispositivo/navegador**. Usa los botones ⬆ (importar) / ⬇ (exportar) de la barra superior para mover tareas entre el móvil y el escritorio — el JSON tiene el mismo formato que `tasks.json`.

## Probarla rápido en el móvil (misma red WiFi)

1. En este PC, dentro de `webapp/`:
   ```
   python -m http.server 8000
   ```
2. En el móvil (conectado a la misma WiFi que el PC), abre Chrome y visita:
   ```
   http://172.16.0.32:8000
   ```
   (esa es la IP actual del PC en esta red; puede cambiar — compruébala con `ipconfig` si no carga).
3. Menú de Chrome (⋮) → **Añadir a pantalla de inicio**.

Sobre HTTP plano (sin HTTPS) el navegador no ofrece la instalación completa como app (ni caché offline vía Service Worker), pero el acceso directo y el uso normal funcionan igual. Para la instalación "de verdad" (icono standalone, splash screen, funciona sin conexión) hace falta servirla por HTTPS — ver abajo.

## Publicarla con HTTPS (instalación real, sin Play Store)

El repo ya tiene remoto en GitHub (`devilmandriver/Eisenhower`), así que la vía más simple es **GitHub Pages**:

1. Sube esta carpeta (pídemelo cuando quieras y hago el commit/push).
2. En GitHub → repo → **Settings → Pages** → Source: `Deploy from a branch` → Branch: `main`, carpeta `/webapp` (o `/ (root)` si prefieres mover el contenido a `/docs`).
3. Espera 1-2 min y abre la URL que te da GitHub (algo como `https://devilmandriver.github.io/Eisenhower/`) en Chrome del móvil.
4. Chrome mostrará el banner **"Instalar app"** automáticamente (o Menú ⋮ → Instalar aplicación). Queda como app nativa: icono propio, pantalla completa, funciona sin conexión.

## Estructura

```
webapp/
  index.html          UI
  css/styles.css       tema oscuro, igual paleta que el escritorio
  js/app.js            lógica: estado, render, drag&drop, diálogos, import/export
  manifest.webmanifest metadatos de instalación (nombre, iconos, colores)
  service-worker.js    caché de la app para uso offline
  icons/                iconos PNG (generados con gen_icons.py, mismo diseño que icon.ico)
  gen_icons.py          regenera los iconos si cambias colores/tamaños
```
