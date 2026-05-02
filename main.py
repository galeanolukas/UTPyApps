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

# Diccionario para almacenar apps montadas
mounted_apps = {}

def render_template(template_name, **context):
    """Función helper para renderizar templates"""
    template = env.get_template(template_name)
    return template.render(**context)

def parse_app_metadata(app_file_path):
    """Extraer metadatos desde comentarios del archivo principal"""
    metadata = {}
    try:
        with open(app_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("# "):
                    key_value = line[2:].split(":", 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip()
                        value = key_value[1].strip()
                        metadata[key.lower()] = value
                else:
                    break  # Termina cuando encuentra la primera línea que no es comentario
    except Exception as e:
        print(f"Error leyendo metadatos en {app_file_path}: {e}")
    return metadata

def import_module_from_file(module_name, filepath):
    """Importar un módulo desde archivo (estilo MicroKiOS)"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error importando {module_name}: {e}")
        return None

def install_apps(current_app):
    """Instalar y montar todas las apps (estilo MicroKiOS)"""
    if not os.path.exists(APPS_DIR):
        return current_app
    
    excepciones = ["__pycache__", ".DS_Store", "README.md"]
    
    for app_folder in os.listdir(APPS_DIR):
        if app_folder in excepciones:
            continue
            
        app_path = os.path.join(APPS_DIR, app_folder)
        if not os.path.isdir(app_path):
            continue
            
        # Buscar archivo principal (main.py - estilo MicroKiOS)
        app_file = None
        for filename in ["main.py", f"{app_folder}.py", "logic.py"]:
            file_path = os.path.join(app_path, filename)
            if os.path.exists(file_path):
                app_file = file_path
                break
        
        if not app_file:
            continue
            
        try:
            # Importar módulo
            module = import_module_from_file(app_folder, app_file)
            
            # Buscar la aplicación Microdot en el módulo (estilo MicroKiOS)
            sub_app = None
            if module:
                # Primero buscar variable 'app' (estándar MicroKiOS)
                if hasattr(module, 'app') and isinstance(getattr(module, 'app'), Microdot):
                    sub_app = getattr(module, 'app')
                else:
                    # Fallback: buscar cualquier instancia de Microdot
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, Microdot):
                            sub_app = attr
                            break
            
            if sub_app:
                # Montar la app con url_prefix
                current_app.mount(sub_app, url_prefix=f'/_app/{app_folder}')
                mounted_apps[app_folder] = sub_app
                print(f"✅ App {app_folder} montada correctamente")
            else:
                print(f"⚠️ App {app_folder} no define una aplicación Microdot válida")
                
        except Exception as e:
            print(f"❌ Error instalando {app_folder}: {e}")
    
    return current_app

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
@app.route('/eliminar/<nombre>', methods=['POST'])
def eliminar_app(request, nombre):
    """Eliminar una aplicación existente"""
    app_folder = os.path.join(APPS_DIR, nombre)
    
    if not os.path.exists(app_folder):
        return Response("App no encontrada", status_code=404)
    
    try:
        # Eliminar la carpeta de la app recursivamente
        import shutil
        shutil.rmtree(app_folder)
        
        # Eliminar del diccionario de apps montadas si existe
        if nombre in mounted_apps:
            del mounted_apps[nombre]
        
        print(f"✅ App '{nombre}' eliminada correctamente")
        return Response('', status_code=302, headers={'Location': '/'})
        
    except Exception as e:
        print(f"❌ Error eliminando app '{nombre}': {e}")
        return Response(f"Error al eliminar la app: {e}", status_code=500)

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
        
        # Crear view.html usando template externo
        template_content = render_template('app_view.html', 
                                        app_name=nombre, 
                                        app_description=descripcion or 'App creada con UTPYAPPS')
        
        with open(os.path.join(app_folder, 'view.html'), 'w') as f:
            f.write(template_content)
        
        # Crear main.py por defecto con estructura Microdot simplificada
        app_name_clean = nombre.lower().replace(' ', '_')
        main_template = f"""# {nombre} - App Microdot para UTPYAPPS
# Name: {nombre}
# Description: {descripcion or 'App creada con UTPYAPPS'}
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
    \"\"\"Página principal de la app\"\"\"
    template = app_env.get_template('index.html')
    html_content = template.render(
        app_name='{nombre}',
        app_description='{descripcion or "App creada con UTPYAPPS"}',
        app_version='1.0'
    )
    return Response(html_content)

# Agrega tus propios endpoints aquí:
# @app.route('/api/mi_endpoint')
# def mi_endpoint(request):
#     return Response({{
#         'message': 'Hola desde mi endpoint!',
#         'app': '{nombre}'
#     }}, headers={{'Content-Type': 'application/json'}})
"""
        
        with open(os.path.join(app_folder, 'main.py'), 'w') as f:
            f.write(main_template)
        
        # Crear estructura de carpetas para la app
        templates_dir = os.path.join(app_folder, 'templates')
        static_dir = os.path.join(app_folder, 'static')
        os.makedirs(templates_dir, exist_ok=True)
        os.makedirs(static_dir, exist_ok=True)
        
        # Copiar template index.html para la app
        app_index_template = render_template('app_index.html', 
                                           app_name=nombre, 
                                           app_description=descripcion or 'App creada con UTPYAPPS')
        
        with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
            f.write(app_index_template)
        
        return redirect('/')
    
    html_content = render_template('create_app.html')
    return Response(html_content, headers={'Content-Type': 'text/html; charset=utf-8'})

# Sistema de routing: mostrar el view.html de cada app (fallback para apps sin Microdot)
@app.route('/_app/<nombre>')
async def ejecutar_app(request, nombre):
    # Si la app está montada como Microdot, dejar que maneje la ruta
    if nombre in mounted_apps:
        # La app Microdot manejará sus propias rutas
        # Esta ruta solo se ejecuta si no hay ruta específica en la app
        app_data = cargar_app_manifest(nombre)
        return Response(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{app_data.get('name', nombre)} - UTPYAPPS</title>
            <link rel="stylesheet" href="/static/css/w3.css">
            <style>
                body {{ background: linear-gradient(135deg, #2c001e 0%, #5e2750 100%); min-height: 100vh; margin: 0; padding: 0; }}
                .container {{ padding: 40px 20px; text-align: center; }}
                .card {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 16px; padding: 30px; max-width: 600px; margin: 0 auto; }}
                h1 {{ color: #E95420; margin-bottom: 20px; }}
                p {{ color: #AEA79F; margin-bottom: 30px; }}
                .btn {{ background: linear-gradient(135deg, #E95420 0%, #77216F 100%); color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1>{app_data.get('name', nombre)}</h1>
                    <p>{app_data.get('description', 'App Microdot cargada correctamente')}</p>
                    <p style="font-size: 14px; opacity: 0.7;">Esta app tiene endpoints personalizados. Prueba las rutas específicas de la app.</p>
                    <a href="/" class="btn">← Dashboard</a>
                </div>
            </div>
        </body>
        </html>
        """, headers={'Content-Type': 'text/html; charset=utf-8'})
    
    # Fallback: cargar view.html para apps sin Microdot
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
    
    # Instalar apps dinámicamente (estilo MicroKiOS)
    print("📦 Instalando aplicaciones...")
    app = install_apps(app)
    
    print("🚀 Iniciando UTPYAPPS - Meta-lanzador para Ubuntu Touch")
    print(f"🌐 Servidor disponible en: http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
