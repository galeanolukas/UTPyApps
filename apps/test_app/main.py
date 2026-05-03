# test_app - App para UTPyApps
# Name: test_app
# Description: prueba
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
        app_name='test_app',
        app_description='prueba'
    )
    return Response(html_content)

# Agrega tus propios endpoints aquí:
# @app.route('/api/mi_endpoint')
# def mi_endpoint(request):
#     return Response({
#         'message': 'Hola desde mi endpoint!',
#         'app': 'test_app'
#     }, headers={'Content-Type': 'application/json'})
