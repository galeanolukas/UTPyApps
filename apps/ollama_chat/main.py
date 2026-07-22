# Ollama Chat - Chat con modelos de IA usando Ollama
# Name: Ollama Chat
# Description: Chat con modelos de IA usando Ollama en Ubuntu Touch
# Author: UTPyApps
# Version: 1.0.0

from microdot import Microdot, Response
from jinja2 import Environment, FileSystemLoader
import os
import subprocess
import json

try:
    from ollama import Client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

app = Microdot()
Response.default_content_type = 'text/html'

# Configurar templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
app_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# Configuración de Ollama
OLLAMA_HOST = 'localhost:11434'
if OLLAMA_AVAILABLE:
    ollama_client = Client(host=OLLAMA_HOST)

@app.route('/')
@app.route('/index.html')
def home(request):
    """Página principal del chat"""
    template = app_env.get_template('index.html')
    html_content = template.render(
        app_name='Ollama Chat',
        app_description='Chat con modelos de IA usando Ollama'
    )
    return Response(html_content)

@app.route('/api/status')
def api_status(request):
    """Verificar estado de Ollama"""
    if not OLLAMA_AVAILABLE:
        return Response({
            'status': 'error',
            'message': 'Librería ollama no instalada'
        }, headers={'Content-Type': 'application/json'})
    
    try:
        models = ollama_client.list()
        return Response({
            'status': 'running',
            'models': models.get('models', [])
        }, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({
            'status': 'not_running',
            'message': str(e)
        }, headers={'Content-Type': 'application/json'})

@app.route('/api/models')
def api_models(request):
    """Listar modelos disponibles"""
    if not OLLAMA_AVAILABLE:
        return Response({
            'error': 'Librería ollama no instalada'
        }, status_code=500, headers={'Content-Type': 'application/json'})
    
    try:
        models = ollama_client.list()
        return Response(models, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({
            'error': str(e)
        }, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/chat', methods=['POST'])
def api_chat(request):
    """Enviar mensaje al modelo"""
    if not OLLAMA_AVAILABLE:
        return Response({
            'error': 'Librería ollama no instalada'
        }, status_code=500, headers={'Content-Type': 'application/json'})
    
    try:
        data = request.json
        model = data.get('model', 'phi')
        message = data.get('message', '')
        history = data.get('history', [])
        
        # Construir contexto del chat
        messages = []
        for msg in history:
            messages.append({
                'role': msg.get('role', 'user'),
                'content': msg.get('content', '')
            })
        messages.append({
            'role': 'user',
            'content': message
        })
        
        # Usar librería ollama de Python
        response = ollama_client.chat(
            model=model,
            messages=messages
        )
        
        return Response({
            'response': response.get('message', {}).get('content', ''),
            'model': model
        }, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({
            'error': str(e)
        }, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/install', methods=['POST'])
def api_install(request):
    """Instalar Ollama (local o en dispositivo)"""
    try:
        data = request.json
        device_id = data.get('device_id')
        
        if device_id:
            # Instalar en dispositivo vía ADB
            # Paso 1: Detectar arquitectura del dispositivo
            arch_cmd = ['adb', '-s', device_id, 'shell', 'uname -m']
            arch_result = subprocess.run(arch_cmd, capture_output=True, text=True, timeout=10)
            arch = arch_result.stdout.strip()
            
            # Paso 2: Descargar binario de Ollama según arquitectura
            if arch == 'aarch64':
                ollama_url = 'https://ollama.com/download/ollama-linux-arm64'
            elif arch == 'x86_64':
                ollama_url = 'https://ollama.com/download/ollama-linux-amd64'
            else:
                return Response({
                    'error': f'Arquitectura no soportada: {arch}. Ollama requiere aarch64 o x86_64'
                }, status_code=400, headers={'Content-Type': 'application/json'})
            
            # Paso 3: Descargar binario en el dispositivo
            download_cmd = [
                'adb', '-s', device_id, 'shell',
                f'curl -L {ollama_url} -o /tmp/ollama'
            ]
            download_result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=300)
            
            if download_result.returncode != 0:
                return Response({
                    'success': False,
                    'error': 'Error descargando Ollama',
                    'output': download_result.stdout,
                    'stderr': download_result.stderr
                }, headers={'Content-Type': 'application/json'})
            
            # Paso 4: Dar permisos de ejecución
            chmod_cmd = ['adb', '-s', device_id, 'shell', 'chmod +x /tmp/ollama']
            chmod_result = subprocess.run(chmod_cmd, capture_output=True, text=True, timeout=10)
            
            # Paso 5: Mover a /usr/local/bin
            move_cmd = ['adb', '-s', device_id, 'shell', 'sudo mv /tmp/ollama /usr/local/bin/ollama']
            move_result = subprocess.run(move_cmd, capture_output=True, text=True, timeout=10)
            
            return Response({
                'success': True,
                'architecture': arch,
                'output': f'Ollama instalado para {arch}',
                'download_output': download_result.stdout,
                'chmod_output': chmod_result.stdout,
                'move_output': move_result.stdout
            }, headers={'Content-Type': 'application/json'})
        else:
            # Instalar localmente (Linux/Mac)
            install_cmd = ['curl', '-fsSL', 'https://ollama.com/install.sh', '|', 'sh']
            result = subprocess.run('curl -fsSL https://ollama.com/install.sh | sh', shell=True, capture_output=True, text=True, timeout=300)
            
            return Response({
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({
            'error': str(e)
        }, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/pull', methods=['POST'])
def api_pull(request):
    """Descargar un modelo"""
    if not OLLAMA_AVAILABLE:
        return Response({
            'error': 'Librería ollama no instalada'
        }, status_code=500, headers={'Content-Type': 'application/json'})
    
    try:
        data = request.json
        model = data.get('model')
        
        if not model:
            return Response({
                'error': 'model requerido'
            }, status_code=400, headers={'Content-Type': 'application/json'})
        
        # Usar librería ollama para descargar modelo
        ollama_client.pull(model)
        
        return Response({
            'success': True,
            'model': model
        }, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({
            'error': str(e)
        }, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/start', methods=['POST'])
def api_start(request):
    """Iniciar Ollama (local o en dispositivo)"""
    try:
        data = request.json
        device_id = data.get('device_id')
        
        if device_id:
            # Iniciar Ollama en el dispositivo (método nativo de Linux)
            start_cmd = [
                'adb', '-s', device_id, 'shell',
                'nohup ollama serve > /tmp/ollama.log 2>&1 &'
            ]
            result = subprocess.run(start_cmd, capture_output=True, text=True, timeout=10)
            
            return Response({
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }, headers={'Content-Type': 'application/json'})
        else:
            # Iniciar Ollama localmente
            start_cmd = ['nohup', 'ollama', 'serve', '>', '/tmp/ollama.log', '2>&1', '&']
            result = subprocess.run('nohup ollama serve > /tmp/ollama.log 2>&1 &', shell=True, capture_output=True, text=True, timeout=10)
            
            return Response({
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({
            'error': str(e)
        }, status_code=500, headers={'Content-Type': 'application/json'})
