# Hola Mundo - App Microdot para UTPyApps
# Name: Hola Mundo
# Description: App de ejemplo para demostrar el sistema
# Author: UTPyApps
# Version: 1.0

from microdot import Microdot, Response
from jinja2 import Environment, FileSystemLoader
import os
import json
import random

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
        app_name='Hola Mundo',
        app_description='App de ejemplo para demostrar el sistema UTPyApps con Microdot y Jinja2'
    )
    return Response(html_content)

@app.route('/')
def home_with_slash(request):
    """Página principal de la app (con /)"""
    template = app_env.get_template('index.html')
    html_content = template.render(
        app_name='Hola Mundo',
        app_description='App de ejemplo para demostrar el sistema UTPyApps con Microdot y Jinja2'
    )
    return Response(html_content)

@app.route('/api/hello')
def api_hello(request):
    """API endpoint de saludo"""
    return Response(json.dumps({
        'message': '¡Hola Mundo desde UTPyApps con Microdot!',
        'app': 'hola_mundo',
        'version': '1.0',
        'framework': 'Microdot',
        'timestamp': '2026-05-01'
    }), headers={'Content-Type': 'application/json'})

@app.route('/api/status')
def api_status(request):
    """API endpoint de estado"""
    return Response(json.dumps({
        'status': 'running',
        'app': 'hola_mundo',
        'framework': 'UTPyApps',
        'endpoints': [
            '/',
            '/api/hello',
            '/api/status',
            '/api/saludar'
        ],
        'features': [
            'Microdot web framework',
            'Ubuntu Touch styling',
            'API endpoints',
            'Dynamic mounting',
            'Template system'
        ]
    }), headers={'Content-Type': 'application/json'})

@app.route('/api/saludar')
def api_saludar(request):
    """Endpoint para obtener un saludo aleatorio"""
    mensajes = [
        '¡Hola desde UTPyApps!',
        '¡Bienvenido al meta-lanzador!',
        '¡Tu app funciona perfectamente!',
        '¡Ubuntu Touch + Python = ❤️!',
        '¡Microdot + Jinja2 = 🚀!'
    ]
    
    mensaje = random.choice(mensajes)
    
    return Response(json.dumps({
        'mensaje': mensaje,
        'status': 'success',
        'app': 'hola_mundo'
    }), headers={'Content-Type': 'application/json'})