# UTPYAPPS - Meta-Lanzador para Ubuntu Touch

UTPYAPPS es un meta-lanzador que proporciona infraestructura para crear y ejecutar aplicaciones Python en Ubuntu Touch con una interfaz web unificada.

## 🚀 Características Principales

- **Meta-lanzador**: Sistema centralizado para gestionar múltiples apps Python
- **Infraestructura completa**: Servidor HTTP, templates, sistema de archivos
- **API REST simple**: Endpoints para crear/ejecutar apps dinámicamente
- **Estructura mínima**: Cada app requiere solo 3 archivos
- **Estilo unificado**: Todas las apps comparten W3.CSS
- **Routing automático**: URLs del tipo `/_app/<nombre>`
- **Archivos estáticos**: CSS, JS e imágenes compartidos
- **Variables dinámicas**: Reemplazo simple de variables en templates

## 📁 Estructura del Proyecto

```
ubpyapps/
├── main.py              # Servidor principal (Microdot + Jinja2)
├── requirements.txt     # Dependencias Python
├── apps/               # Directorio de aplicaciones
│   └── hola_mundo/     # App de ejemplo
│       ├── app.json    # Configuración de la app
│       ├── view.html   # Interfaz HTML
│       └── logic.py    # Lógica y API endpoints
├── static/             # Archivos estáticos compartidos
│   ├── css/
│   │   └── w3.css     # Framework CSS
│   ├── js/
│   │   ├── common.js  # Funciones comunes
│   │   └── ubtool.js  # Utilidades adicionales
│   └── images/
│       └── ubuntu-touch-logo.svg
└── templates/          # Plantillas del sistema
    ├── base_layout.html
    ├── index.html
    ├── create_app.html
    └── app_detail.html
```

## 🛠️ Instalación y Ejecución

### Requisitos
- Python 3.7+
- pip

### Instalación
```bash
# Clonar el repositorio
git clone <repository-url>
cd ubpyapps

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecución
```bash
python3 main.py
```

El servidor iniciará en: `http://localhost:8080`

## 📱 Crear una Nueva App

### Método 1: Interfaz Web
1. Abre `http://localhost:8080`
2. Haz clic en "Nueva App"
3. Completa el formulario:
   - **Nombre**: Nombre de la aplicación
   - **Descripción**: Breve descripción
   - **Autor**: Tu nombre (opcional)
4. La app se creará automáticamente

### Método 2: Manualmente

Crea una carpeta en `apps/` con el nombre de tu app (ej: `mi_app`) y añade estos 3 archivos:

#### 1. `app.json` - Configuración
```json
{
  "name": "Mi Aplicación",
  "description": "Descripción de mi app",
  "author": "Tu Nombre",
  "version": "1.0.0"
}
```

#### 2. `view.html` - Interfaz
```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APP_NAME - UTPYAPPS</title>
    <link rel="stylesheet" href="/static/css/w3.css">
    <link rel="stylesheet" href="/static/css/common.css">
    <script src="/static/js/common.js"></script>
</head>
<body class="w3-light-grey">
    <!-- Header -->
    <header class="w3-container w3-teal w3-padding-24">
        <div class="w3-row">
            <div class="w3-col s8">
                <h1 class="w3-xxlarge">
                    <img src="/static/images/ubuntu-touch-logo.svg" style="width:40px;height:40px;vertical-align:middle;margin-right:10px;">
                    UTPYAPPS
                </h1>
                <p class="w3-large">Meta-lanzador para aplicaciones Python en Ubuntu Touch</p>
            </div>
            <div class="w3-col s4 w3-right-align">
                <a href="/" class="w3-btn w3-large w3-round-large w3-white w3-text-teal">
                    ← Dashboard
                </a>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="w3-container w3-padding-16">
        <div class="w3-row-padding">
            <div class="w3-col l8 m10 s12">
                <div class="w3-card w3-white w3-round-large w3-padding">
                    <header class="w3-container w3-teal w3-round-large-top">
                        <h2>APP_NAME</h2>
                    </header>
                    <div class="w3-container w3-padding">
                        <p>APP_DESCRIPTION</p>
                        <p>¡Tu app está funcionando!</p>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>
</html>
```

#### 3. `logic.py` - Lógica y API (opcional)
```python
"""
Lógica de la aplicación
Proporciona endpoints para la API
"""

from microdot import Response
import json

# Endpoints disponibles para esta app
endpoints = {}

def mi_endpoint(request):
    """Endpoint de ejemplo"""
    return Response(json={
        'mensaje': 'Hola desde mi app!',
        'status': 'success'
    })

# Registrar el endpoint
endpoints['saludar'] = mi_endpoint
```

## 🔧 Variables de Template

Las apps pueden usar variables especiales que se reemplazan automáticamente:

- `APP_NAME` - Nombre de la app (desde app.json)
- `APP_DESCRIPTION` - Descripción de la app
- `APP_AUTHOR` - Autor de la app
- `APP_VERSION` - Versión de la app

## 🌐 URLs y Routing

- **Dashboard**: `http://localhost:8080/`
- **Crear App**: `http://localhost:8080/crear`
- **App Individual**: `http://localhost:8080/_app/<nombre>`
- **API Endpoints**: `http://localhost:8080/_api/apps/<nombre>/<endpoint>`

## 📚 Ejemplos de Uso

### App Simple (Solo HTML)
Crea solo `app.json` y `view.html` para una app estática con información.

### App con API
Añade `logic.py` para crear endpoints REST:
```python
# Acceso: POST/GET http://localhost:8080/_api/mi_app/saludar
```

### App con JavaScript
Usa los archivos estáticos compartidos:
```html
<script src="/static/js/common.js"></script>
<link rel="stylesheet" href="/static/css/w3.css">
```

## 🎨 Estilo y Diseño

- **W3.CSS**: Framework CSS principal
- **Clases w3-**: Usa clases estándar de W3.CSS
- **Responsive**: Diseño adaptable para móviles
- **Ubuntu Touch**: Optimizado para dispositivos táctiles

## 🔍 Depuración

Para ver mensajes de debug:
```bash
python3 main.py
# Los mensajes aparecerán en la consola
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una feature branch
3. Haz tus cambios
4. Envía un pull request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

## 🚀 Roadmap

- [ ] Sistema de plugins
- [ ] Gestor de paquetes de apps
- [ ] Temas personalizables
- [ ] Soporte para bases de datos
- [ ] Autenticación de usuarios
- [ ] Sistema de actualizaciones automáticas

---

**UTPYAPPS** - Simplificando el desarrollo de apps Python para Ubuntu Touch
