# Eisenhower Matrix

Ordena tareas según la matriz de Eisenhower (Urgente/Importante). Dos apps independientes que comparten el mismo formato de datos (`tasks.json`), así que las tareas se pueden pasar de una a otra con exportar/importar:

- **[desktop/](desktop/)** — app de escritorio para Windows (Python + PySide6). Ver [desktop/README.md](desktop/README.md).
- **[docs/](docs/)** — versión web instalable para Android (PWA), publicada en **https://devilmandriver.github.io/Eisenhower/**. Ver [docs/README.md](docs/README.md).

La carpeta se llama `docs/` y no `mobile/` o `app/` por una restricción de GitHub Pages: solo publica desde la raíz del repo o desde una carpeta llamada exactamente `/docs`.

Los cuatro cuadrantes, en ambas apps:
- Urgente & Importante: Hacer ya
- Importante & No urgente: Programar
- Urgente & No importante: Delegar
- Ninguno: Eliminar
