# apps1 - App para UTPyApps
# Name: apps1
# Description: hola
# Author: Usuario
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
        app_name='apps1',
        app_description='hola'
    )
    return Response(html_content)

# Agrega tus propios endpoints aquí:
# @app.route('/api/mi_endpoint')
# def mi_endpoint(request):
#     return Response({
#         'message': 'Hola desde mi endpoint!',
#         'app': 'apps1'
#     }, headers={'Content-Type': 'application/json'})
