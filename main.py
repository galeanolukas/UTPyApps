from microdot import Microdot, Response, redirect
from microdot.cors import CORS
from jinja2 import Environment, FileSystemLoader
import json
import os
import importlib.util
import mimetypes
import subprocess
import sys

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

def install_app_dependencies(app_folder, requirements):
    """Instalar dependencias de una app usando pip"""
    if not requirements or len(requirements) == 0:
        return True, "No dependencies required"
    
    try:
        # Crear requirements.txt temporal
        requirements_file = os.path.join(app_folder, 'requirements.txt')
        with open(requirements_file, 'w') as f:
            f.write('\n'.join(requirements))
        
        print(f"📦 Instalando dependencias para app: {os.path.basename(app_folder)}")
        
        # Instalar dependencias con pip
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', requirements_file
        ], capture_output=True, text=True, check=True)
        
        print(f"✅ Dependencias instaladas: {len(requirements)} paquetes")
        if result.stdout:
            print(f"📋 Output: {result.stdout}")
        
        # Eliminar requirements.txt temporal
        os.remove(requirements_file)
        
        return True, f"Dependencies installed: {len(requirements)} packages"
        
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ Error installing dependencies: {e.stderr}"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"❌ Error installing dependencies: {e}"
        print(error_msg)
        return False, error_msg

def check_package_installed(package_name):
    """Verificar si un paquete está instalado"""
    try:
        # Limpiar nombre del paquete (remover version y extras)
        clean_name = package_name.split('>=')[0].split('==')[0].split('<=')[0].split('~=')[0]
        __import__(clean_name)
        return True
    except ImportError:
        return False

def install_app_dependencies_smart(app_folder, requirements):
    """Instalar solo las dependencias que no están presentes"""
    if not requirements or len(requirements) == 0:
        return True, "No dependencies required"
    
    missing_deps = []
    for req in requirements:
        package_name = req.split('>=')[0].split('==')[0].split('<=')[0].split('~=')[0]
        if not check_package_installed(package_name):
            missing_deps.append(req)
    
    if not missing_deps:
        print(f"✅ Todas las dependencias ya están instaladas")
        return True, "All dependencies already installed"
    
    return install_app_dependencies(app_folder, missing_deps)

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
            # Cargar manifest y verificar dependencias
            manifest = cargar_app_manifest(app_path)
            if manifest and 'requirements' in manifest:
                success, msg = install_app_dependencies_smart(app_path, manifest['requirements'])
                if not success:
                    print(f"⚠️ App {app_folder}: {msg}")
                    continue  # No montar la app si falla la instalación
            
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

def install_single_app(current_app, app_folder):
    """Instalar y montar una app específica dinámicamente"""
    if app_folder in mounted_apps:
        print(f"⚠️ App {app_folder} ya está montada")
        return current_app
    
    app_path = os.path.join(APPS_DIR, app_folder)
    if not os.path.isdir(app_path):
        print(f"❌ App {app_folder} no existe")
        return current_app
    
    try:
        # Buscar archivo principal (main.py - estilo MicroKiOS)
        app_file = None
        for filename in ["main.py", f"{app_folder}.py", "logic.py"]:
            file_path = os.path.join(app_path, filename)
            if os.path.exists(file_path):
                app_file = file_path
                break
        
        if not app_file:
            print(f"❌ App {app_folder} no tiene archivo principal")
            return current_app
        
        # Cargar manifest y verificar dependencias
        manifest = cargar_app_manifest(app_path)
        if manifest and 'requirements' in manifest:
            success, msg = install_app_dependencies_smart(app_path, manifest['requirements'])
            if not success:
                print(f"⚠️ App {app_folder}: {msg}")
                return current_app
        
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
            print(f"✅ App {app_folder} montada dinámicamente")
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

# Code Editor Routes
@app.route('/editor/<app_name>')
def editor_page(request, app_name):
    """Página del editor de código para una app"""
    app_path = os.path.join(APPS_DIR, app_name)
    
    if not os.path.exists(app_path):
        return Response("App no encontrada", status_code=404)
    
    html_content = render_template('editor.html', app_name=app_name)
    return Response(html_content)

@app.route('/api/editor/<app_name>/files')
def get_app_files(request, app_name):
    """Obtener lista de archivos de una app para el editor"""
    app_path = os.path.join(APPS_DIR, app_name)
    
    if not os.path.exists(app_path):
        return Response(json.dumps({'error': 'App no encontrada'}), status_code=404, headers={'Content-Type': 'application/json'})
    
    files = []
    
    # Recorrer directorio de la app
    for root, dirs, filenames in os.walk(app_path):
        for filename in filenames:
            # Ignorar archivos ocultos y compilados
            if filename.startswith('.') or filename.endswith('.pyc'):
                continue
                
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, app_path)
            
            try:
                # Obtener información del archivo
                stat = os.stat(file_path)
                files.append({
                    'name': relative_path,
                    'path': file_path,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'type': 'file'
                })
            except Exception as e:
                print(f"Error getting file info for {file_path}: {e}")
                continue
    
    return Response(json.dumps(files), headers={'Content-Type': 'application/json'})

@app.route('/api/editor/<app_name>/file')
def get_file_content(request, app_name):
    """Obtener contenido de un archivo para el editor"""
    app_path = os.path.join(APPS_DIR, app_name)
    
    # Obtener filename de los query params
    filename = request.args.get('filename')
    if not filename:
        return Response(json.dumps({'error': 'Filename requerido'}), status_code=400, headers={'Content-Type': 'application/json'})
    
    # Decodificar el filename para manejar correctamente las rutas con /
    from urllib.parse import unquote
    filename = unquote(filename)
    
    # Construir la ruta completa del archivo
    file_path = os.path.join(app_path, filename)
    
    # Validar que el archivo esté dentro del directorio de la app (seguridad)
    try:
        common_path = os.path.commonpath([app_path])
        file_common_path = os.path.commonpath([app_path, file_path])
        if common_path != file_common_path:
            return Response(json.dumps({'error': 'Acceso no permitido'}), status_code=403, headers={'Content-Type': 'application/json'})
    except ValueError:
        return Response(json.dumps({'error': 'Ruta inválida'}), status_code=400, headers={'Content-Type': 'application/json'})
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return Response(json.dumps({'error': 'Archivo no encontrado'}), status_code=404, headers={'Content-Type': 'application/json'})
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content, headers={'Content-Type': 'text/plain'})
    except UnicodeDecodeError:
        # Para archivos binarios
        return Response(json.dumps({'error': 'Archivo binario no soportado'}), status_code=400, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response(json.dumps({'error': f'Error leyendo archivo: {e}'}), status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/editor/<app_name>/file', methods=['POST'])
def save_file_content(request, app_name):
    """Guardar contenido de un archivo desde el editor"""
    app_path = os.path.join(APPS_DIR, app_name)
    
    # Validar que la app existe
    if not os.path.exists(app_path):
        return Response(json.dumps({'error': 'App no encontrada'}), status_code=404, headers={'Content-Type': 'application/json'})
    
    # Obtener filename de los query params
    filename = request.args.get('filename')
    if not filename:
        return Response(json.dumps({'error': 'Filename requerido'}), status_code=400, headers={'Content-Type': 'application/json'})
    
    # Decodificar el filename para manejar correctamente las rutas con /
    from urllib.parse import unquote
    filename = unquote(filename)
    
    # Construir la ruta completa del archivo
    file_path = os.path.join(app_path, filename)
    
    # Validar que el archivo está dentro del directorio de la app (seguridad)
    try:
        common_path = os.path.commonpath([app_path])
        file_common_path = os.path.commonpath([app_path, file_path])
        if common_path != file_common_path:
            return Response(json.dumps({'error': 'Acceso no permitido'}), status_code=403, headers={'Content-Type': 'application/json'})
    except ValueError:
        return Response(json.dumps({'error': 'Ruta inválida'}), status_code=400, headers={'Content-Type': 'application/json'})
    
    try:
        content = request.json.get('content', '')
        
        # Crear directorio si no existe (para archivos en subdirectorios)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Archivo guardado: {app_name}/{filename}")
        return Response(json.dumps({'success': True, 'message': 'Archivo guardado correctamente'}), headers={'Content-Type': 'application/json'})
        
    except Exception as e:
        print(f"❌ Error guardando archivo {filename}: {e}")
        return Response(json.dumps({'error': f'Error guardando archivo: {e}'}), status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/editor/<app_name>/file', methods=['DELETE'])
def delete_file(request, app_name):
    """Eliminar un archivo desde el editor"""
    app_path = os.path.join(APPS_DIR, app_name)
    
    # Validar que la app existe
    if not os.path.exists(app_path):
        return Response(json.dumps({'error': 'App no encontrada'}), status_code=404, headers={'Content-Type': 'application/json'})
    
    # Obtener filename de los query params
    filename = request.args.get('filename')
    if not filename:
        return Response(json.dumps({'error': 'Filename requerido'}), status_code=400, headers={'Content-Type': 'application/json'})
    
    # Decodificar el filename para manejar correctamente las rutas con /
    from urllib.parse import unquote
    filename = unquote(filename)
    
    # Construir la ruta completa del archivo
    file_path = os.path.join(app_path, filename)
    
    # Validar que el archivo está dentro del directorio de la app (seguridad)
    try:
        common_path = os.path.commonpath([app_path])
        file_common_path = os.path.commonpath([app_path, file_path])
        if common_path != file_common_path:
            return Response(json.dumps({'error': 'Acceso no permitido'}), status_code=403, headers={'Content-Type': 'application/json'})
    except ValueError:
        return Response(json.dumps({'error': 'Ruta inválida'}), status_code=400, headers={'Content-Type': 'application/json'})
    
    # Validar que el archivo existe
    if not os.path.exists(file_path):
        return Response(json.dumps({'error': 'Archivo no encontrado'}), status_code=404, headers={'Content-Type': 'application/json'})
    
    # No permitir eliminar archivos esenciales
    essential_files = ['main.py', 'app.json']
    if filename in essential_files:
        return Response(json.dumps({'error': f'No se puede eliminar el archivo esencial: {filename}'}), status_code=403, headers={'Content-Type': 'application/json'})
    
    try:
        os.remove(file_path)
        print(f"✅ Archivo eliminado: {app_name}/{filename}")
        return Response(json.dumps({'success': True, 'message': 'Archivo eliminado correctamente'}), headers={'Content-Type': 'application/json'})
        
    except Exception as e:
        print(f"❌ Error eliminando archivo {filename}: {e}")
        return Response(json.dumps({'error': f'Error eliminando archivo: {e}'}), status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/crear', methods=['GET', 'POST'])
async def crear_app(request):
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        
        # Crear estructura básica
        app_folder = os.path.join(APPS_DIR, nombre.lower().replace(' ', '_'))
        os.makedirs(app_folder)
        
        # Crear app.json simple
        app_manifest = {
            'name': nombre,
            'description': descripcion,
            'author': 'Usuario',
            'version': '1.0'
        }
        with open(os.path.join(app_folder, 'app.json'), 'w') as f:
            json.dump(app_manifest, f, indent=2)
        
        # Crear main.py simple
        app_name_clean = nombre.lower().replace(' ', '_')
        main_template = f"""# {nombre} - App para UTPyApps
# Name: {nombre}
# Description: {descripcion or 'App creada con UTPyApps'}
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
        app_description='{descripcion or "App creada con UTPyApps"}'
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
        os.makedirs(templates_dir, exist_ok=True)
        
        # Crear index.html básico y genérico
        index_template = """<!DOCTYPE html>
<html>
<head>
    <title>{{ app_name }}</title>
    <link rel="stylesheet" href="/static/w3.css">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        .notice {
            background: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
            color: #0c5460;
        }
        .code-info {
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ app_name }}</h1>
            <p>{{ app_description }}</p>
        </div>
        
        <div class="notice">
            <strong>🚀 ¡Bienvenido a tu nueva app!</strong><br>
            Ahora puedes editar el código para construir tu aplicación personalizada.
        </div>
        
        <div class="code-info">
            <h3>📝 Editar Código</h3>
            <p>Puedes editar los siguientes archivos para personalizar tu app:</p>
            <ul>
                <li><strong>main.py</strong> - Lógica principal y endpoints</li>
                <li><strong>templates/index.html</strong> - Interfaz de usuario</li>
                <li><strong>app.json</strong> - Configuración de la app</li>
            </ul>
            <p>Usa el editor de código de UTPyApps para modificar estos archivos.</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="/" class="w3-btn w3-blue w3-round-large">← Volver al Dashboard</a>
        </div>
    </div>
</body>
</html>"""
        
        with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
            f.write(index_template)
        
        # Montar dinámicamente la nueva app
        app_folder_name = nombre.lower().replace(' ', '_')
        install_single_app(app, app_folder_name)
        
        return redirect('/')
    
    html_content = render_template('create_app.html')
    return Response(html_content, headers={'Content-Type': 'text/html; charset=utf-8'})

# Sistema de routing: SOLO para apps sin Microdot (fallback)
# NOTA: Las apps Microdot montadas manejan sus propias rutas automáticamente
@app.route('/_app/<nombre>')
async def ejecutar_app_fallback(request, nombre):
    """Fallback SOLO para apps sin Microdot (view.html)"""
    # Si la app está montada como Microdot, NO hacer nada
    # Las apps montadas manejan sus rutas automáticamente
    if nombre in mounted_apps:
        # La app está montada, pero esta ruta solo se ejecuta si no tiene ruta raíz
        # Esto es un fallback, no debería ejecutarse normalmente
        pass
    
    # Fallback: cargar view.html para apps sin Microdot
    app_data = cargar_app_manifest(nombre)
    view_path = os.path.join(APPS_DIR, nombre, 'view.html')
    
    if os.path.exists(view_path):
        with open(view_path) as f:
            template_content = f.read()
        # Reemplazar variables simples manualmente
        if app_data:
            template_content = template_content.replace('APP_NAME', app_data.get('name', nombre))
            template_content = template_content.replace('APP_DESCRIPTION', app_data.get('description', ''))
            template_content = template_content.replace('APP_AUTHOR', app_data.get('author', ''))
            template_content = template_content.replace('APP_VERSION', app_data.get('version', '1.0'))
        return Response(template_content, headers={'Content-Type': 'text/html; charset=utf-8'})
    
    # Si no hay view.html, mostrar mensaje de error
    return Response(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>App no encontrada</title>
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
                <h1>App no encontrada</h1>
                <p>La app '{nombre}' no existe o no tiene una página principal configurada.</p>
                <a href="/" class="btn">← Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """, headers={'Content-Type': 'text/html; charset=utf-8'})

if __name__ == '__main__':
    # Crear directorio apps si no existe
    os.makedirs(APPS_DIR, exist_ok=True)
    
    # Instalar apps dinámicamente (estilo MicroKiOS)
    print("📦 Instalando aplicaciones...")
    app = install_apps(app)
    
    print("🚀 Iniciando UTPyApps - Meta-lanzador para Ubuntu Touch")
    print(f"🌐 Servidor disponible en: http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
