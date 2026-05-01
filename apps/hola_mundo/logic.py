"""
Lógica de la aplicación Hola Mundo
Proporciona endpoints para la API
"""

from microdot import Response
import json

# Endpoints disponibles para esta app
endpoints = {}

def saludar_endpoint(request):
    """Endpoint para obtener un saludo aleatorio"""
    mensajes = [
        '¡Hola desde UTPYAPPS!',
        '¡Bienvenido al meta-lanzador!',
        '¡Tu app funciona perfectamente!',
        '¡Ubuntu Touch + Python = ❤️!'
    ]
    
    import random
    mensaje = random.choice(mensajes)
    
    return Response(json={
        'mensaje': mensaje,
        'status': 'success'
    })

# Registrar el endpoint
endpoints['saludar'] = saludar_endpoint
