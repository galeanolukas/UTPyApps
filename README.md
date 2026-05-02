# UTPYAPPS - Meta-Lanzador para Ubuntu Touch

UTPYAPPS es un meta-lanzador que proporciona infraestructura para crear y ejecutar aplicaciones Python Microdot en Ubuntu Touch con una interfaz web unificada. Basado en la arquitectura de MicroKiOS para máxima compatibilidad y escalabilidad.

## 🚀 Características Principales

- **Meta-lanzador**: Sistema centralizado para gestionar múltiples apps Microdot
- **Arquitectura MicroKiOS**: Estructura estándar y probada para aplicaciones
- **Mounting Dinámico**: Apps montadas automáticamente con `url_prefix`
- **Infraestructura completa**: Servidor HTTP, templates, sistema de archivos estáticos
- **Templates Externos**: Sistema Jinja2 con templates reutilizables
- **API REST Automática**: Endpoints JSON para cada aplicación
- **Ubuntu Touch Styling**: Diseño nativo con colores y componentes oficiales
- **Routing Automático**: URLs del tipo `/_app/<nombre>/*`
- **Estructura Estándar**: `main.py`, `templates/`, `static/` por app
- **Metadatos en Comentarios**: Sistema de configuración estilo MicroKiOS

## 📁 Estructura del Proyecto

```
ubpyapps/
├── main.py              # Servidor principal (Microdot + Jinja2)
├── requirements.txt     # Dependencias Python
├── apps/               # Directorio de aplicaciones
│   └── hola_mundo/     # App de ejemplo (estructura MicroKiOS)
│       ├── main.py     # Archivo principal con app Microdot
│       ├── app.json    # Metadatos de la app
│       ├── view.html   # Fallback para apps antiguas
│       ├── templates/  # Templates específicos de la app
│       │   └── index.html
│       └── static/     # Archivos estáticos de la app
├── static/             # Archivos estáticos globales
│   ├── css/
│   │   ├── w3.css     # Framework CSS
│   │   └── common.css  # Estilos adicionales
│   ├── js/
│   │   └── common.js  # Funciones comunes
│   └── logo.png       # Logo por defecto
└── templates/          # Plantillas del sistema
    ├── base_layout.html
    ├── index.html
    ├── create_app.html
    ├── app_view.html   # Para apps antiguas
    └── app_index.html # Template para nuevas apps
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

### Método 1: Interfaz Web (Recomendado)
1. Abre `http://localhost:8080`
2. Haz clic en "Nueva App"
3. Completa el formulario:
   - **Nombre**: Nombre de la aplicación
   - **Descripción**: Breve descripción
4. La app se creará automáticamente con estructura completa

### Método 2: Manualmente (Estructura MicroKiOS)

Crea una carpeta en `apps/` con el nombre de tu app (ej: `mi_app`) y añade estos archivos:

#### 1. `main.py` - Aplicación Microdot Principal
```python
# Mi Aplicación - App Microdot para UTPYAPPS
# Name: Mi Aplicación
# Description: Descripción de mi app
# Author: Tu Nombre
# Version: 1.0

from microdot import Microdot, Response
from jinja2 import Environment, FileSystemLoader
import os

# Crear aplicación Microdot
app = Microdot()
Response.default_content_type = 'text/html'

# Configurar templates para esta app
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
app_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

@app.route('/')
def home(request):
    """Página principal de la app"""
    template = app_env.get_template('index.html')
    html_content = template.render(
        app_name='Mi Aplicación',
        app_description='Descripción de mi app',
        app_version='1.0'
    )
    return Response(html_content)

@app.route('/api/hello')
def api_hello(request):
    """API endpoint de saludo"""
    return Response({
        'message': 'Hola desde mi app!',
        'app': 'Mi Aplicación',
        'version': '1.0',
        'framework': 'Microdot'
    }, headers={'Content-Type': 'application/json'})

@app.route('/api/status')
def api_status(request):
    """API endpoint de estado"""
    return Response({
        'status': 'running',
        'app': 'Mi Aplicación',
        'framework': 'UTPYAPPS',
        'endpoints': ['/', '/api/hello', '/api/status']
    }, headers={'Content-Type': 'application/json'})
```

#### 2. `templates/index.html` - Template Jinja2
```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }} - UTPYAPPS</title>
    <link rel="stylesheet" href="/static/css/w3.css">
    <link rel="stylesheet" href="/static/css/common.css">
    <script src="/static/js/common.js"></script>
    <style>
        body {
            background: linear-gradient(135deg, #2c001e 0%, #5e2750 100%);
            min-height: 100vh;
            margin: 0;
            padding: 0;
        }
        .topbar {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
        }
        .footer {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
        }
        .main-content {
            padding-top: 80px;
            padding-bottom: 60px;
            min-height: 100vh;
        }
        .small-text {
            font-size: 10px;
            color: #AEA79F;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <!-- Topbar Transparente -->
    <div class="topbar">
        <div class="w3-container w3-padding-8">
            <div class="w3-row">
                <div class="w3-col s6">
                    <span style="color: #E95420; font-size: 14px; font-weight: 500;">{{ app_name }}</span>
                </div>
                <div class="w3-col s6 w3-right-align">
                    <a href="/" class="w3-text-white" style="font-size: 12px; text-decoration: none;">← Dashboard</a>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <main class="main-content w3-container">
        <div class="w3-row-padding" style="margin: 0 -8px;">
            <div class="w3-col l8 m10 s12" style="padding: 8px;">
                <div class="w3-card w3-round-large" style="background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 16px;">
                    <div style="background: linear-gradient(135deg, rgba(233, 84, 32, 0.8) 0%, rgba(119, 33, 111, 0.8) 100%); color: white; padding: 10px 16px; margin: -16px -16px 12px -16px; font-size: 14px; font-weight: 500; border-radius: 12px 12px 0 0; display: flex; align-items: center; justify-content: space-between;">
                        <span>{{ app_name }}</span>
                        <div style="width: 32px; height: 32px; background: rgba(255, 255, 255, 0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                            <img src="/static/logo.png" alt="App" style="width: 20px; height: 20px; object-fit: contain;">
                        </div>
                    </div>
                    <div class="w3-padding" style="padding: 16px;">
                        <div class="w3-center" style="padding: 24px 0;">
                            <div style="font-size: 42px; margin-bottom: 12px;">🚀</div>
                            <h3 style="color: white; margin-bottom: 8px; font-size: 20px;">{{ app_name }}</h3>
                            <p style="color: #AEA79F; font-size: 13px; margin: 0;">{{ app_description }}</p>
                        </div>
                        
                        <!-- Ejemplo de variables Jinja2 -->
                        <div style="margin-top: 20px;">
                            <p style="color: white; font-size: 12px;">
                                <strong>Versión:</strong> {{ app_version }}<br>
                                <strong>Estado:</strong> Activo
                            </p>
                        </div>
                        
                        <!-- Ejemplo de condición Jinja2 -->
                        {% if app_features %}
                        <div style="margin-top: 16px;">
                            <p style="color: #AEA79F; font-size: 11px; margin: 8px 0;">Características:</p>
                            {% for feature in app_features %}
                            <div style="background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 8px; margin-bottom: 4px;">
                                <span style="color: #E95420; font-size: 11px;">✓</span> {{ feature }}
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                        
                        <div style="margin-top: 20px;">
                            <button onclick="saludar()" class="w3-btn w3-round-large w3-block" style="background: linear-gradient(135deg, #E95420 0%, #77216F 100%); color: white; font-size: 13px; padding: 10px;">
                                👋 Saludar
                            </button>
                        </div>
                        
                        <div id="mensaje" style="margin-top: 12px; display: none;">
                            <div class="w3-round-large" style="background: rgba(233, 84, 32, 0.2); border: 1px solid rgba(233, 84, 32, 0.3); padding: 12px;">
                                <p id="texto-mensaje" style="color: white; font-size: 13px; margin: 0;"></p>
                            </div>
                        </div>
                        
                        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                            <p style="color: #AEA79F; font-size: 11px; margin: 8px 0;">API Endpoints disponibles:</p>
                            <div style="background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 12px;">
                                <code style="color: #E95420; font-size: 11px;">GET /api/hello</code><br>
                                <code style="color: #E95420; font-size: 11px;">GET /api/status</code>
                            </div>
                        </div>
                        
                        <div style="margin-top: 12px;">
                            <a href="/" class="w3-btn w3-round-large w3-block" style="background: rgba(255, 255, 255, 0.1); color: #AEA79F; font-size: 12px; padding: 8px; text-decoration: none;">
                                ← Dashboard
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- Footer Transparente -->
    <div class="footer">
        <div class="w3-container w3-padding-8">
            <div class="w3-center">
                <span class="small-text">© 2026 UTPYAPPS • Ubuntu Touch</span>
            </div>
        </div>
    </div>

    <script>
        function saludar() {
            fetch('/api/hello')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('texto-mensaje').textContent = data.message;
                    document.getElementById('mensaje').style.display = 'block';
                })
                .catch(error => {
                    document.getElementById('texto-mensaje').textContent = 'Error: ' + error.message;
                    document.getElementById('mensaje').style.display = 'block';
                });
        }
    </script>
</body>
</html>
```

#### 3. `static/` - Archivos Estáticos (Opcional)
- `css/` - Hojas de estilo específicas
- `js/` - Scripts JavaScript
- `images/` - Imágenes de la app

### 🎨 Uso de Jinja2 en Templates

Jinja2 te permite crear templates dinámicos con variables, condiciones y bucles:

#### Variables
```html
<!-- Variables simples -->
<h1>{{ app_name }}</h1>
<p>{{ app_description }}</p>

<!-- Variables con filtros -->
<p>Fecha: {{ current_date | date('Y-m-d') }}</p>
<p>Texto en mayúsculas: {{ app_name | upper }}</p>
```

#### Condiciones
```html
{% if user_logged_in %}
    <p>Bienvenido {{ username }}</p>
{% else %}
    <p>Por favor inicia sesión</p>
{% endif %}

{% if app_features %}
    <h3>Características:</h3>
    <ul>
        {% for feature in app_features %}
        <li>{{ feature }}</li>
        {% endfor %}
    </ul>
{% endif %}
```

#### Bucles
```html
<!-- Lista de elementos -->
<ul>
{% for item in items %}
    <li>{{ item.name }} - ${{ item.price }}</li>
{% empty %}
    <li>No hay elementos disponibles</li>
{% endfor %}
</ul>

<!-- Bucle con índice -->
{% for i, feature in enumerate(app_features) %}
    <p>{{ i + 1 }}. {{ feature }}</p>
{% endfor %}
```

#### Estructuras Avanzadas
```html
<!-- Include de templates -->
{% include 'header.html' %}

<!-- Herencia de templates -->
{% extends 'base_layout.html' %}

{% block content %}
    <!-- Contenido específico -->
{% endblock %}

<!-- Macros (funciones reutilizables) -->
{% macro button(text, url) %}
<a href="{{ url }}" class="w3-btn">{{ text }}</a>
{% endmacro %}

{{ button('Inicio', '/') }}
{{ button('Acerca', '/about') }}
```

#### Ejemplo Completo en main.py
```python
@app.route('/')
def home(request):
    """Página principal con Jinja2"""
    template = app_env.get_template('index.html')
    
    # Datos dinámicos para el template
    context = {
        'app_name': 'Mi App',
        'app_description': 'Descripción dinámica',
        'app_version': '2.0',
        'current_date': datetime.now(),
        'user_logged_in': True,
        'username': 'Juan',
        'app_features': [
            'Microdot Framework',
            'Templates Jinja2',
            'Ubuntu Touch Style',
            'API Endpoints'
        ],
        'items': [
            {'name': 'Producto A', 'price': 100},
            {'name': 'Producto B', 'price': 200}
        ]
    }
    
    html_content = template.render(**context)
    return Response(html_content)
```

## � Sistema de Dependencias

UTPYAPPS soporta gestión automática de dependencias para cada app individualmente.

### Estructura app.json con Requirements
```json
{
  "name": "Mi App",
  "description": "Descripción de mi app",
  "author": "Mi Nombre",
  "version": "1.0.0",
  "requirements": [
    "microdot>=0.2.0",
    "jinja2>=3.0.0",
    "requests>=2.25.0",
    "pandas>=1.3.0"
  ]
}
```

### Instalación Automática
Cuando se inicia UTPYAPPS, el sistema:
1. **Lee** el campo `requirements` de cada `app.json`
2. **Verifica** qué paquetes ya están instalados
3. **Instala** solo las dependencias faltantes con `pip`
4. **Monta** la app solo si las dependencias se instalaron correctamente

### Formatos de Requirements Soportados
```json
{
  "requirements": [
    "requests>=2.25.0",      // Versión mínima
    "pandas==1.3.0",         // Versión exacta
    "numpy~=1.21.0",         // Versión compatible
    "flask>=2.0,<3.0",       // Rango de versiones
    "beautifulsoup4"         // Cualquier versión
  ]
}
```

### Funciones del Sistema
- **`install_app_dependencies()`**: Instala todas las dependencias
- **`install_app_dependencies_smart()`**: Instala solo las faltantes
- **`check_package_installed()`**: Verifica si un paquete está disponible

### Ejemplo de App con Dependencias
```python
# main.py
import requests  # Se instalará automáticamente si no existe
import pandas as pd  # Se instalará automáticamente si no existe

@app.route('/api/data')
def get_data(request):
    response = requests.get('https://api.example.com/data')
    df = pd.DataFrame(response.json())
    return Response(df.to_json())
```

### Manejo de Errores
- Si una dependencia falla al instalar, la app **no se monta**
- Los errores se muestran en la consola con detalles del problema
- Las otras apps continúan funcionando normalmente

## �🔧 Variables de Template

Las apps pueden usar variables especiales que se reemplazan automáticamente:

- `APP_NAME` - Nombre de la app (desde app.json)
- `APP_DESCRIPTION` - Descripción de la app
- `APP_AUTHOR` - Autor de la app
- `APP_VERSION` - Versión de la app

## 🌐 URLs y Routing

- **Dashboard**: `http://localhost:8080/`
- **Crear App**: `http://localhost:8080/crear`
- **App Microdot**: `http://localhost:8080/_app/<nombre>/`
- **API Endpoints**: `http://localhost:8080/_app/<nombre>/api/<endpoint>`
- **Archivos Estáticos**: `http://localhost:8080/static/<path>`

## 📚 Ejemplos de Uso

### App Microdot Completa (Recomendado)
Crea `main.py`, `templates/index.html` para una app con API REST completa.

### App Simple (Fallback)
Crea solo `app.json` y `view.html` para una app estática (compatibilidad con apps antiguas).

### API Endpoints Automáticos
Cada app Microdot incluye endpoints por defecto:
```python
# GET http://localhost:8080/_app/mi_app/api/hello
# GET http://localhost:8080/_app/mi_app/api/status
```

### JavaScript y AJAX
Usa los endpoints API desde el frontend:
```javascript
fetch('/api/hello')
    .then(response => response.json())
    .then(data => console.log(data));
```

## 🎨 Estilo y Diseño

- **Ubuntu Touch Colors**: Paleta oficial (#E95420, #77216F, #2C001E, #AEA79F)
- **Glassmorphism**: Efectos de transparencia y blur
- **W3.CSS**: Framework CSS base
- **Responsive**: Diseño adaptable para móviles y tablets
- **Componentes Unificados**: Topbar, footer, cards consistentes

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

## 🚀 Características Avanzadas

### Sistema de Montaje Dinámico
- **Auto-detección**: Apps detectadas automáticamente al iniciar
- **Montaje con URL Prefix**: Cada app en su propio namespace
- **Fallback**: Compatibilidad con apps antiguas (solo HTML)
- **Recarga en caliente**: Cambios detectados automáticamente

### Templates Jinja2
- **Variables dinámicas**: `{{ app_name }}`, `{{ app_description }}`
- **Herencia de templates**: Extensión y composición
- **Filtros personalizados**: Formato de datos específico
- **Includes parciales**: Componentes reutilizables

### Sistema de Metadatos
- **Comentarios en código**: Metadatos extraídos desde `main.py`
- **JSON fallback**: `app.json` para configuración adicional
- **Auto-descubrimiento**: Información de versión y autor

## 🚀 Roadmap

- [x] **Arquitectura MicroKiOS** - Estructura estándar implementada
- [x] **Ubuntu Touch Styling** - Diseño nativo completo
- [x] **Mounting Dinámico** - Sistema de apps automático
- [ ] Sistema de plugins y extensiones
- [ ] Gestor de paquetes de apps
- [ ] Temas personalizables adicionales
- [ ] Soporte para bases de datos integradas
- [ ] Autenticación de usuarios y permisos
- [ ] Sistema de actualizaciones automáticas
- [ ] CLI para desarrollo de apps

## 🔧 Troubleshooting

### App no se monta
- Verifica que `main.py` exista y defina la variable `app`
- Revisa los mensajes de error en la consola
- Asegúrate de que la estructura de carpetas sea correcta

### Templates no se renderizan
- Verifica que la carpeta `templates/` exista
- Revisa la sintaxis Jinja2 en los templates
- Comprueba los nombres de variables

### Endpoints API no funcionan
- Asegúrate de que los decoradores `@app.route()` estén correctos
- Verifica que retornen `Response()` con headers JSON
- Revisa la ruta completa incluyendo el prefijo `/_app/<nombre>/`

---

**UTPYAPPS** - Meta-lanzador Python para Ubuntu Touch con arquitectura MicroKiOS
