from microdot import Microdot, Response, redirect
from microdot.cors import CORS
from jinja2 import Environment, FileSystemLoader
import json
import os
import importlib.util
import mimetypes

app = Microdot()
CORS(app, allowed_origins="*", allow_credentials=True)
Response.default_content_type = 'text/html'

# Configurar entorno Jinja2
env = Environment(loader=FileSystemLoader('templates'))

# Directorio de apps
APPS_DIR = os.path.join(os.path.dirname(__file__), 'apps')

def render_template(template_name, **context):
    """Función helper para renderizar templates"""
    template = env.get_template(template_name)
    return template.render(**context)

@app.route('/static/<path:path>')
async def static_files(request, path):
    """Servir archivos estáticos desde ./static"""
    static_root = os.path.abspath('static')
    requested_path = os.path.abspath(os.path.join(static_root, path))

    # Prevent path traversal
    if not (requested_path == static_root or requested_path.startswith(static_root + os.sep)):
        return Response('Not found', status_code=404)

    if not os.path.isfile(requested_path):
        return Response('Not found', status_code=404)

    content_type, _ = mimetypes.guess_type(requested_path)
    if not content_type:
        content_type = 'application/octet-stream'

    with open(requested_path, 'rb') as f:
        content = f.read()

    return Response(content, headers={'Content-Type': content_type})

# Cargar apps instaladas
def cargar_apps():
    apps = []
    if os.path.exists(APPS_DIR):
        for app_folder in os.listdir(APPS_DIR):
            manifest_path = os.path.join(APPS_DIR, app_folder, 'app.json')
            if os.path.exists(manifest_path):
                with open(manifest_path) as f:
                    app_info = json.load(f)
                    app_info['folder'] = app_folder
                    apps.append(app_info)
    return apps

def cargar_app_manifest(nombre):
    manifest_path = os.path.join(APPS_DIR, nombre, 'app.json')
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            return json.load(f)
    return None

# Dashboard principal
@app.route('/')
async def index(request):
    apps = cargar_apps()
    html_content = render_template('index.html', apps=apps)
    return Response(html_content, headers={'Content-Type': 'text/html; charset=utf-8'})

# Ver detalles de una app
@app.route('/app/<nombre>')
async def ver_app(request, nombre):
    app_data = cargar_app_manifest(nombre)
    html_content = render_template('app_detail.html', app=app_data)
    return Response(html_content, headers={'Content-Type': 'text/html; charset=utf-8'})

# API para ejecutar lógica de apps
@app.route('/_api/apps/<nombre>/<endpoint>', methods=['POST', 'GET'])
async def api_app(request, nombre, endpoint):
    # Cargar dinámicamente el logic.py de la app
    logic_path = os.path.join(APPS_DIR, nombre, 'logic.py')
    if os.path.exists(logic_path):
        spec = importlib.util.spec_from_file_location(f"{nombre}_logic", logic_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, 'endpoints') and endpoint in module.endpoints:
            return module.endpoints[endpoint](request)
    
    return Response(json={'error': 'Endpoint no encontrado'}, status_code=404)

# Crear nueva app desde el dashboard
@app.route('/crear', methods=['GET', 'POST'])
async def crear_app(request):
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        
        # Crear estructura básica
        app_folder = os.path.join(APPS_DIR, nombre.lower().replace(' ', '_'))
        os.makedirs(app_folder)
        
        # Crear app.json
        app_manifest = {
            'name': nombre,
            'description': descripcion,
            'author': 'Usuario',
            'version': '1.0'
        }
        with open(os.path.join(app_folder, 'app.json'), 'w') as f:
            json.dump(app_manifest, f)
        
        # Crear view.html por defecto
        view_template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app.name }} - UTPYAPPS</title>
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
                        <h2>{{ app.name }}</h2>
                    </header>
                    <div class="w3-container w3-padding">
                        <p>{{ app.description }}</p>
                        <p>¡Tu app está lista para desarrollar!</p>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>
</html>"""
        
        with open(os.path.join(app_folder, 'view.html'), 'w') as f:
            f.write(view_template)
        
        return redirect('/')
    
    html_content = render_template('create_app.html')
    return Response(html_content, headers={'Content-Type': 'text/html; charset=utf-8'})

# Sistema de routing: mostrar el view.html de cada app
@app.route('/_app/<nombre>')
async def ejecutar_app(request, nombre):
    app_data = cargar_app_manifest(nombre)
    view_path = os.path.join(APPS_DIR, nombre, 'view.html')
    
    if os.path.exists(view_path):
        with open(view_path) as f:
            template_content = f.read()
        # Reemplazar variables simples manualmente
        if app_data:
            print(f"DEBUG: app_data = {app_data}")  # Debug
            template_content = template_content.replace('APP_NAME', app_data.get('name', nombre))
            template_content = template_content.replace('APP_DESCRIPTION', app_data.get('description', ''))
            template_content = template_content.replace('APP_AUTHOR', app_data.get('author', ''))
            template_content = template_content.replace('APP_VERSION', app_data.get('version', '1.0'))
            print(f"DEBUG: After replacement, title contains: {template_content[template_content.find('<title>'):template_content.find('</title>')+8]}")  # Debug
        return Response(template_content, headers={'Content-Type': 'text/html; charset=utf-8'})
    return Response("App no encontrada", status_code=404)

if __name__ == '__main__':
    # Crear directorio apps si no existe
    os.makedirs(APPS_DIR, exist_ok=True)
    print("🚀 Iniciando UTPYAPPS - Meta-lanzador para Ubuntu Touch")
    print(f"🌐 Servidor disponible en: http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
