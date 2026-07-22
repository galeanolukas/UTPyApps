# Tutorial UTPyApps - Guía de programación
# Name: Tutorial UTPyApps
# Description: Tutorial interactivo para aprender a crear apps con UTPyApps
# Author: UTPyApps
# Version: 1.0.0

from microdot import Microdot, Response
from jinja2 import Environment, FileSystemLoader
import os

app = Microdot()
Response.default_content_type = 'text/html'

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
app_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

@app.route('/')
def home(request):
    """Página principal del tutorial"""
    template = app_env.get_template('index.html')
    html_content = template.render(
        app_name='Tutorial UTPyApps',
        app_description='Aprende a crear apps con UTPyApps'
    )
    return Response(html_content)

@app.route('/api/hello')
def api_hello(request):
    """Ejemplo de endpoint API simple"""
    return Response({
        'message': '¡Hola desde UTPyApps!',
        'framework': 'Microdot',
        'tutorial': 'Este es un ejemplo de endpoint API'
    }, headers={'Content-Type': 'application/json'})

@app.route('/api/calcular', methods=['POST'])
def api_calcular(request):
    """Ejemplo de endpoint con parámetros"""
    try:
        data = request.json
        num1 = data.get('num1', 0)
        num2 = data.get('num2', 0)
        operacion = data.get('operacion', 'sumar')
        
        resultado = 0
        if operacion == 'sumar':
            resultado = num1 + num2
        elif operacion == 'restar':
            resultado = num1 - num2
        elif operacion == 'multiplicar':
            resultado = num1 * num2
        elif operacion == 'dividir':
            resultado = num1 / num2 if num2 != 0 else 'Error: división por cero'
        
        return Response({
            'num1': num1,
            'num2': num2,
            'operacion': operacion,
            'resultado': resultado
        }, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({
            'error': str(e)
        }, status_code=500, headers={'Content-Type': 'application/json'})
