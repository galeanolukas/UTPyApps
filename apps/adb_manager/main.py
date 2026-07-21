# ADB Manager - Gestor de conexión ADB para Ubuntu Touch
# Name: ADB Manager
# Description: Gestor de conexión ADB para dispositivos Ubuntu Touch con interfaz Lomiri
# Author: UTPyApps
# Version: 1.0.0

from microdot import Microdot, Response
from jinja2 import Environment, FileSystemLoader
import os
import subprocess
import json

# Crear aplicación Microdot
app = Microdot()
Response.default_content_type = 'text/html'

# Configurar templates para esta app
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
app_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

class ADBManager:
    """Gestor de comandos ADB para Ubuntu Touch"""
    
    @staticmethod
    def check_adb_available():
        """Verificar si ADB está instalado en el sistema"""
        try:
            result = subprocess.run(['adb', 'version'], 
                                  capture_output=True, text=True, timeout=5)
            return True, result.stdout
        except FileNotFoundError:
            return False, "ADB no está instalado en el sistema"
        except Exception as e:
            return False, f"Error verificando ADB: {str(e)}"
    
    @staticmethod
    def get_devices():
        """Obtener lista de dispositivos conectados"""
        try:
            result = subprocess.run(['adb', 'devices'], 
                                  capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split('\n')
            devices = []
            
            for line in lines[1:]:  # Saltar la primera línea (header)
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        device_id = parts[0].strip()
                        status = parts[1].strip()
                        devices.append({
                            'id': device_id,
                            'status': status,
                            'model': ADBManager.get_device_model(device_id)
                        })
            
            return True, devices
        except Exception as e:
            return False, f"Error obteniendo dispositivos: {str(e)}"
    
    @staticmethod
    def get_device_model(device_id):
        """Obtener modelo del dispositivo"""
        try:
            result = subprocess.run(['adb', '-s', device_id, 'shell', 'getprop', 'ro.product.model'],
                                  capture_output=True, text=True, timeout=5)
            model = result.stdout.strip()
            return model if model else "Desconocido"
        except:
            return "Desconocido"
    
    @staticmethod
    def get_device_info(device_id):
        """Obtener información detallada del dispositivo"""
        try:
            # Obtener información del sistema
            props = {
                'model': 'ro.product.model',
                'manufacturer': 'ro.product.manufacturer',
                'android_version': 'ro.build.version.release',
                'ubuntu_touch_version': 'ro.system.build.version',
                'device_name': 'ro.product.device'
            }
            
            info = {'id': device_id}
            for key, prop in props.items():
                try:
                    result = subprocess.run(['adb', '-s', device_id, 'shell', 'getprop', prop],
                                          capture_output=True, text=True, timeout=5)
                    info[key] = result.stdout.strip() or "No disponible"
                except:
                    info[key] = "No disponible"
            
            return True, info
        except Exception as e:
            return False, f"Error obteniendo info del dispositivo: {str(e)}"
    
    @staticmethod
    def execute_shell_command(device_id, command):
        """Ejecutar comando shell en el dispositivo"""
        try:
            result = subprocess.run(['adb', '-s', device_id, 'shell', command],
                                  capture_output=True, text=True, timeout=30)
            return True, {
                'command': command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        except Exception as e:
            return False, f"Error ejecutando comando: {str(e)}"
    
    @staticmethod
    def install_apk(device_id, apk_path):
        """Instalar APK en el dispositivo"""
        try:
            result = subprocess.run(['adb', '-s', device_id, 'install', apk_path],
                                  capture_output=True, text=True, timeout=120)
            return True, {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        except Exception as e:
            return False, f"Error instalando APK: {str(e)}"
    
    @staticmethod
    def push_file(device_id, local_path, remote_path):
        """Enviar archivo al dispositivo"""
        try:
            result = subprocess.run(['adb', '-s', device_id, 'push', local_path, remote_path],
                                  capture_output=True, text=True, timeout=60)
            return True, {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        except Exception as e:
            return False, f"Error enviando archivo: {str(e)}"
    
    @staticmethod
    def pull_file(device_id, remote_path, local_path):
        """Recibir archivo del dispositivo"""
        try:
            result = subprocess.run(['adb', '-s', device_id, 'pull', remote_path, local_path],
                                  capture_output=True, text=True, timeout=60)
            return True, {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        except Exception as e:
            return False, f"Error recibiendo archivo: {str(e)}"
    
    @staticmethod
    def reboot_device(device_id, mode='system'):
        """Reiniciar dispositivo (system, recovery, bootloader)"""
        try:
            if mode == 'system':
                result = subprocess.run(['adb', '-s', device_id, 'reboot'],
                                      capture_output=True, text=True, timeout=30)
            elif mode == 'recovery':
                result = subprocess.run(['adb', '-s', device_id, 'reboot', 'recovery'],
                                      capture_output=True, text=True, timeout=30)
            elif mode == 'bootloader':
                result = subprocess.run(['adb', '-s', device_id, 'reboot', 'bootloader'],
                                      capture_output=True, text=True, timeout=30)
            else:
                return False, "Modo de reinicio no válido"
            
            return True, f"Dispositivo reiniciado en modo {mode}"
        except Exception as e:
            return False, f"Error reiniciando dispositivo: {str(e)}"
    
    @staticmethod
    def check_python_environment(device_id):
        """Verificar si Python está instalado en el dispositivo"""
        try:
            result = subprocess.run(['adb', '-s', device_id, 'shell', 'which', 'python3'],
                                  capture_output=True, text=True, timeout=10)
            python_exists = result.returncode == 0 and result.stdout.strip()
            
            # Verificar pip
            result_pip = subprocess.run(['adb', '-s', device_id, 'shell', 'which', 'pip3'],
                                      capture_output=True, text=True, timeout=10)
            pip_exists = result_pip.returncode == 0 and result_pip.stdout.strip()
            
            return True, {
                'python_installed': python_exists,
                'python_path': result.stdout.strip() if python_exists else None,
                'pip_installed': pip_exists,
                'pip_path': result_pip.stdout.strip() if pip_exists else None
            }
        except Exception as e:
            return False, f"Error verificando entorno Python: {str(e)}"
    
    @staticmethod
    def create_utpyapps_environment(device_id, sudo_password=None):
        """Crear entorno UTPyApps en el dispositivo Ubuntu Touch"""
        try:
            # Crear directorio base en home del usuario
            base_dir = '~/utpyapps'
            
            commands = [
                f'mkdir -p {base_dir}',
                f'mkdir -p {base_dir}/apps',
                f'mkdir -p {base_dir}/templates',
                f'mkdir -p {base_dir}/static',
                f'mkdir -p {base_dir}/static/css',
                f'mkdir -p {base_dir}/static/js',
                f'mkdir -p {base_dir}/static/images',
            ]
            
            results = []
            for cmd in commands:
                shell_cmd = ['adb', '-s', device_id, 'shell', cmd]
                if sudo_password:
                    shell_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S {cmd}']
                
                result = subprocess.run(shell_cmd, capture_output=True, text=True, timeout=15)
                results.append({
                    'command': cmd,
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr
                })
            
            # Crear archivo main.py básico en el dispositivo
            main_py_content = '''#!/usr/bin/env python3
# UTPyApps - Meta-Lanzador para Ubuntu Touch
# Este archivo se genera automáticamente

from microdot import Microdot, Response
from jinja2 import Environment, FileSystemLoader
import json
import os

app = Microdot()
Response.default_content_type = 'text/html'

# Configurar entorno
BASE_DIR = os.path.expanduser('~/utpyapps')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
APPS_DIR = os.path.join(BASE_DIR, 'apps')

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

@app.route('/')
def home(request):
    """Dashboard principal"""
    apps = []
    if os.path.exists(APPS_DIR):
        for app_folder in os.listdir(APPS_DIR):
            manifest_path = os.path.join(APPS_DIR, app_folder, 'app.json')
            if os.path.exists(manifest_path):
                with open(manifest_path) as f:
                    app_info = json.load(f)
                    if not app_info.get('hidden', False):
                        app_info['folder'] = app_folder
                        apps.append(app_info)
    
    template = env.get_template('index.html')
    return Response(template.render(apps=apps))

@app.route('/static/<path:path>')
async def static_files(request, path):
    """Servir archivos estáticos"""
    from microdot import send_file
    return send_file(STATIC_DIR, path)

if __name__ == '__main__':
    print("🚀 Iniciando UTPyApps en Ubuntu Touch")
    app.run(host='0.0.0.0', port=8080)
'''
            
            # Escribir main.py en el dispositivo
            temp_main = '/tmp/utpyapps_main.py'
            with open(temp_main, 'w') as f:
                f.write(main_py_content)
            
            push_result = subprocess.run(['adb', '-s', device_id, 'push', temp_main, f'{base_dir}/main.py'],
                                       capture_output=True, text=True, timeout=30)
            
            os.remove(temp_main)
            
            # Dar permisos de ejecución
            chmod_cmd = ['adb', '-s', device_id, 'shell', f'chmod +x {base_dir}/main.py']
            if sudo_password:
                chmod_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S chmod +x {base_dir}/main.py']
            
            chmod_result = subprocess.run(chmod_cmd, capture_output=True, text=True, timeout=10)
            
            return True, {
                'message': 'Entorno UTPyApps creado exitosamente',
                'directory': base_dir,
                'setup_results': results,
                'main_py_pushed': push_result.returncode == 0,
                'chmod_result': chmod_result.returncode == 0
            }
        except Exception as e:
            return False, f"Error creando entorno: {str(e)}"
    
    @staticmethod
    def copy_app_to_device(device_id, app_name, local_apps_dir, sudo_password=None):
        """Copiar una app desde el sistema local al dispositivo"""
        try:
            local_app_path = os.path.join(local_apps_dir, app_name)
            
            if not os.path.exists(local_app_path):
                return False, f"App {app_name} no existe en el sistema local"
            
            remote_app_path = f'~/utpyapps/apps/{app_name}'
            
            # Crear directorio remoto
            mkdir_cmd = ['adb', '-s', device_id, 'shell', f'mkdir -p {remote_app_path}']
            if sudo_password:
                mkdir_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S mkdir -p {remote_app_path}']
            
            mkdir_result = subprocess.run(mkdir_cmd, capture_output=True, text=True, timeout=15)
            
            if mkdir_result.returncode != 0:
                return False, f"Error creando directorio remoto: {mkdir_result.stderr}"
            
            # Copiar archivos de la app
            copied_files = []
            for root, dirs, files in os.walk(local_app_path):
                for file in files:
                    if file.endswith('.pyc') or file.startswith('.'):
                        continue
                    
                    local_file = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file, local_app_path)
                    remote_file = f'{remote_app_path}/{relative_path}'
                    
                    # Crear directorios remotos si es necesario
                    remote_dir = os.path.dirname(remote_file)
                    mkdir_dir_cmd = ['adb', '-s', device_id, 'shell', f'mkdir -p {remote_dir}']
                    if sudo_password:
                        mkdir_dir_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S mkdir -p {remote_dir}']
                    
                    subprocess.run(mkdir_dir_cmd, capture_output=True, text=True, timeout=10)
                    
                    # Copiar archivo
                    push_result = subprocess.run(['adb', '-s', device_id, 'push', local_file, remote_file],
                                               capture_output=True, text=True, timeout=30)
                    
                    copied_files.append({
                        'file': relative_path,
                        'success': push_result.returncode == 0,
                        'output': push_result.stdout
                    })
            
            return True, {
                'message': f'App {app_name} copiada exitosamente',
                'app_name': app_name,
                'remote_path': remote_app_path,
                'copied_files': copied_files,
                'total_files': len(copied_files)
            }
        except Exception as e:
            return False, f"Error copiando app: {str(e)}"
    
    @staticmethod
    def start_utpyapps_on_device(device_id):
        """Iniciar UTPyApps en el dispositivo"""
        try:
            # Verificar si el proceso ya está corriendo
            check_result = subprocess.run(['adb', '-s', device_id, 'shell', 'pgrep', '-f', 'utpyapps/main.py'],
                                        capture_output=True, text=True, timeout=10)
            
            if check_result.returncode == 0 and check_result.stdout.strip():
                return True, {
                    'message': 'UTPyApps ya está corriendo en el dispositivo',
                    'pid': check_result.stdout.strip()
                }
            
            # Iniciar UTPyApps en background
            start_result = subprocess.run(['adb', '-s', device_id, 'shell', 'cd ~/utpyapps && nohup python3 main.py > utpyapps.log 2>&1 &'],
                                        capture_output=True, text=True, timeout=15)
            
            return True, {
                'message': 'UTPyApps iniciado en el dispositivo',
                'command': 'cd ~/utpyapps && nohup python3 main.py > utpyapps.log 2>&1 &',
                'success': start_result.returncode == 0
            }
        except Exception as e:
            return False, f"Error iniciando UTPyApps: {str(e)}"
    
    @staticmethod
    def stop_utpyapps_on_device(device_id):
        """Detener UTPyApps en el dispositivo"""
        try:
            # Matar el proceso
            kill_result = subprocess.run(['adb', '-s', device_id, 'shell', 'pkill', '-f', 'utpyapps/main.py'],
                                       capture_output=True, text=True, timeout=10)
            
            return True, {
                'message': 'UTPyApps detenido en el dispositivo',
                'success': kill_result.returncode == 0
            }
        except Exception as e:
            return False, f"Error deteniendo UTPyApps: {str(e)}"
    
    @staticmethod
    def get_utpyapps_logs(device_id):
        """Obtener logs de UTPyApps del dispositivo"""
        try:
            result = subprocess.run(['adb', '-s', device_id, 'shell', 'cat', '~/utpyapps/utpyapps.log'],
                                  capture_output=True, text=True, timeout=10)
            
            return True, {
                'logs': result.stdout,
                'error': result.stderr
            }
        except Exception as e:
            return False, f"Error obteniendo logs: {str(e)}"
    
    @staticmethod
    def open_morph_browser(device_id, url=None):
        """Abrir morph-browser en el dispositivo con URL opcional"""
        try:
            if url:
                # Abrir con URL específica
                result = subprocess.run(['adb', '-s', device_id, 'shell', 'xdg-open', url],
                                      capture_output=True, text=True, timeout=15)
            else:
                # Abrir morph-browser sin URL específica
                result = subprocess.run(['adb', '-s', device_id, 'shell', 'morph-browser'],
                                      capture_output=True, text=True, timeout=15)
            
            return True, {
                'message': f'Morph-browser abierto' + (f' con URL: {url}' if url else ''),
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except Exception as e:
            return False, f"Error abriendo morph-browser: {str(e)}"
    
    @staticmethod
    def open_lomiri_terminal(device_id, command=None):
        """Abrir lomiri-terminal-app en el dispositivo con comando opcional"""
        try:
            if command:
                # Abrir terminal con comando específico
                result = subprocess.run(['adb', '-s', device_id, 'shell', 'lomiri-terminal-app', command],
                                      capture_output=True, text=True, timeout=15)
            else:
                # Abrir terminal sin comando específico
                result = subprocess.run(['adb', '-s', device_id, 'shell', 'lomiri-terminal-app'],
                                      capture_output=True, text=True, timeout=15)
            
            return True, {
                'message': f'Lomiri Terminal abierto' + (f' con comando: {command}' if command else ''),
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except Exception as e:
            return False, f"Error abriendo lomiri-terminal-app: {str(e)}"
    
    @staticmethod
    def get_device_ip(device_id):
        """Obtener dirección IP del dispositivo"""
        try:
            # Obtener IP desde configuración de red
            result = subprocess.run(['adb', '-s', device_id, 'shell', 'ip', 'addr', 'show', 'wlan0'],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                # Fallback: usar eth0
                result = subprocess.run(['adb', '-s', device_id, 'shell', 'ip', 'addr', 'show', 'eth0'],
                                      capture_output=True, text=True, timeout=10)
            
            # Extraer IP del output
            import re
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if ip_match:
                return True, ip_match.group(1)
            else:
                return False, "No se pudo obtener la dirección IP"
        except Exception as e:
            return False, f"Error obteniendo IP: {str(e)}"
    
    @staticmethod
    def install_pip(device_id, sudo_password=None):
        """Instalar pip en el dispositivo usando apt-get, ensurepip, get-pip.py o --break-system-packages"""
        try:
            # Método 1: Usar apt-get para instalar python3-pip (recomendado para Ubuntu Touch)
            print("Intentando instalar pip usando apt-get...")
            apt_cmd = ['adb', '-s', device_id, 'shell', 'apt-get', 'update']
            if sudo_password:
                apt_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S apt-get update']
            
            update_result = subprocess.run(apt_cmd, capture_output=True, text=True, timeout=120)
            
            if update_result.returncode == 0:
                install_cmd = ['adb', '-s', device_id, 'shell', 'apt-get', 'install', '-y', 'python3-pip']
                if sudo_password:
                    install_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S apt-get install -y python3-pip']
                
                install_result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=180)
                
                if install_result.returncode == 0:
                    return True, {
                        'message': 'pip instalado exitosamente usando apt-get',
                        'output': install_result.stdout,
                        'method': 'apt-get'
                    }
            
            # Método 2: Intentar instalar pip usando ensurepip
            print("apt-get falló, intentando con ensurepip...")
            cmd = ['adb', '-s', device_id, 'shell', 'python3', '-m', 'ensurepip', '--upgrade']
            if sudo_password:
                cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S python3 -m ensurepip --upgrade']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return True, {
                    'message': 'pip instalado exitosamente usando ensurepip',
                    'output': result.stdout,
                    'method': 'ensurepip'
                }
            
            # Método 3: Descargar get-pip.py usando wget y ejecutarlo
            print("ensurepip falló, intentando con get-pip.py usando wget...")
            download_cmd = ['adb', '-s', device_id, 'shell', 'wget', 'https://bootstrap.pypa.io/get-pip.py', '-O', '/tmp/get-pip.py']
            if sudo_password:
                download_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py']
            
            download_result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=30)
            
            if download_result.returncode == 0:
                install_cmd = ['adb', '-s', device_id, 'shell', 'python3', '/tmp/get-pip.py']
                if sudo_password:
                    install_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S python3 /tmp/get-pip.py']
                
                install_result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=60)
                
                # Limpiar archivo temporal
                subprocess.run(['adb', '-s', device_id, 'shell', 'rm', '/tmp/get-pip.py'],
                              capture_output=True, text=True, timeout=10)
                
                if install_result.returncode == 0:
                    return True, {
                        'message': 'pip instalado exitosamente usando get-pip.py',
                        'output': install_result.stdout,
                        'method': 'get-pip.py'
                    }
            
            # Método 4: Usar get-pip.py con --break-system-packages (último recurso)
            print("get-pip.py falló, intentando con --break-system-packages...")
            download_cmd = ['adb', '-s', device_id, 'shell', 'wget', 'https://bootstrap.pypa.io/get-pip.py', '-O', '/tmp/get-pip.py']
            if sudo_password:
                download_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py']
            
            download_result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=30)
            
            if download_result.returncode == 0:
                install_cmd = ['adb', '-s', device_id, 'shell', 'python3', '/tmp/get-pip.py', '--break-system-packages']
                if sudo_password:
                    install_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S python3 /tmp/get-pip.py --break-system-packages']
                
                install_result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=60)
                
                # Limpiar archivo temporal
                subprocess.run(['adb', '-s', device_id, 'shell', 'rm', '/tmp/get-pip.py'],
                              capture_output=True, text=True, timeout=10)
                
                if install_result.returncode == 0:
                    return True, {
                        'message': 'pip instalado exitosamente usando get-pip.py con --break-system-packages',
                        'output': install_result.stdout,
                        'method': 'get-pip.py-break-system'
                    }
            
            return False, "No se pudo instalar pip. Métodos intentados: apt-get, ensurepip, get-pip.py, get-pip.py --break-system-packages. Recomendación: Usa python3 -m venv para crear un entorno virtual directamente."
                
        except Exception as e:
            return False, f"Error instalando pip: {str(e)}"
    
    @staticmethod
    def install_virtualenv(device_id, sudo_password=None):
        """Instalar virtualenv en el dispositivo usando pip"""
        try:
            # Verificar si pip está instalado
            pip_check = subprocess.run(['adb', '-s', device_id, 'shell', 'which', 'pip3'],
                                     capture_output=True, text=True, timeout=10)
            
            if pip_check.returncode != 0:
                return False, "pip3 no está instalado. Instala pip primero."
            
            # Instalar virtualenv usando pip
            cmd = ['adb', '-s', device_id, 'shell', 'pip3', 'install', 'virtualenv']
            if sudo_password:
                cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S pip3 install virtualenv']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return True, {
                    'message': 'virtualenv instalado exitosamente',
                    'output': result.stdout
                }
            else:
                return False, f"Error instalando virtualenv: {result.stderr}"
                
        except Exception as e:
            return False, f"Error instalando virtualenv: {str(e)}"
    
    @staticmethod
    def create_virtualenv(device_id, env_path='~/utpyapps/venv', sudo_password=None):
        """Crear entorno virtual en el dispositivo usando python3 -m venv --without-pip (Ubuntu Touch)"""
        try:
            # Método 1: Usar python3 -m venv --without-pip (recomendado para Ubuntu Touch con FS de sólo lectura)
            print("Intentando crear entorno virtual usando python3 -m venv --without-pip...")
            cmd = ['adb', '-s', device_id, 'shell', 'python3', '-m', 'venv', '--without-pip', env_path]
            if sudo_password:
                cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S python3 -m venv --without-pip {env_path}']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return True, {
                    'message': f'Entorno virtual creado en {env_path} usando python3 -m venv --without-pip',
                    'output': result.stdout,
                    'env_path': env_path,
                    'method': 'venv-without-pip'
                }
            
            # Método 2: Usar python3 -m venv normal (si python3-venv está instalado)
            print("python3 -m venv --without-pip falló, intentando con python3 -m venv normal...")
            cmd = ['adb', '-s', device_id, 'shell', 'python3', '-m', 'venv', env_path]
            if sudo_password:
                cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S python3 -m venv {env_path}']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return True, {
                    'message': f'Entorno virtual creado en {env_path} usando python3 -m venv',
                    'output': result.stdout,
                    'env_path': env_path,
                    'method': 'venv'
                }
            
            # Método 3: Usar virtualenv (requiere pip)
            print("python3 -m venv falló, intentando con virtualenv...")
            venv_check = subprocess.run(['adb', '-s', device_id, 'shell', 'which', 'virtualenv'],
                                      capture_output=True, text=True, timeout=10)
            
            if venv_check.returncode != 0:
                return False, "No se pudo crear el entorno virtual. Ubuntu Touch requiere python3-venv pero el sistema de archivos es de sólo lectura. Solución: El entorno virtual debe crearse en el home del usuario y pip debe instalarse manualmente dentro del venv."
            
            # Crear entorno virtual
            cmd = ['adb', '-s', device_id, 'shell', 'virtualenv', env_path]
            if sudo_password:
                cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S virtualenv {env_path}']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return True, {
                    'message': f'Entorno virtual creado en {env_path} usando virtualenv',
                    'output': result.stdout,
                    'env_path': env_path,
                    'method': 'virtualenv'
                }
            else:
                return False, f"Error creando entorno virtual: {result.stderr}"
                
        except Exception as e:
            return False, f"Error creando entorno virtual: {str(e)}"
    
    @staticmethod
    def install_package_in_venv(device_id, package, env_path='~/utpyapps/venv', sudo_password=None):
        """Instalar paquete en el entorno virtual"""
        try:
            # Instalar paquete usando pip del entorno virtual
            cmd = ['adb', '-s', device_id, 'shell', f'{env_path}/bin/pip', 'install', package]
            if sudo_password:
                cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S {env_path}/bin/pip install {package}']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return True, {
                    'message': f'{package} instalado exitosamente en el entorno virtual',
                    'output': result.stdout
                }
            else:
                return False, f"Error instalando {package}: {result.stderr}"
                
        except Exception as e:
            return False, f"Error instalando paquete: {str(e)}"
    
    @staticmethod
    def install_pip_in_venv(device_id, env_path='~/utpyapps/venv', sudo_password=None):
        """Instalar pip dentro de un entorno virtual existente (para Ubuntu Touch)"""
        try:
            # Descargar get-pip.py usando wget
            download_cmd = ['adb', '-s', device_id, 'shell', 'wget', 'https://bootstrap.pypa.io/get-pip.py', '-O', '/tmp/get-pip.py']
            if sudo_password:
                download_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py']
            
            download_result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=30)
            
            if download_result.returncode != 0:
                return False, "Error descargando get-pip.py"
            
            # Instalar pip dentro del venv usando get-pip.py
            install_cmd = ['adb', '-s', device_id, 'shell', f'{env_path}/bin/python3', '/tmp/get-pip.py']
            if sudo_password:
                install_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S {env_path}/bin/python3 /tmp/get-pip.py']
            
            install_result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=60)
            
            # Limpiar archivo temporal
            subprocess.run(['adb', '-s', device_id, 'shell', 'rm', '/tmp/get-pip.py'],
                          capture_output=True, text=True, timeout=10)
            
            if install_result.returncode == 0:
                return True, {
                    'message': f'pip instalado exitosamente en el entorno virtual {env_path}',
                    'output': install_result.stdout
                }
            else:
                return False, f"Error instalando pip en el venv: {install_result.stderr}"
                
        except Exception as e:
            return False, f"Error instalando pip en venv: {str(e)}"

@app.route('/')
def home(request):
    """Página principal del gestor ADB"""
    template = app_env.get_template('index.html')
    
    # Verificar disponibilidad de ADB
    adb_available, adb_info = ADBManager.check_adb_available()
    
    # Obtener dispositivos conectados
    devices_success, devices = ADBManager.get_devices()
    if not devices_success:
        devices = []
    
    html_content = template.render(
        app_name='ADB Manager',
        app_description='Gestor de conexión ADB para Ubuntu Touch',
        app_version='1.0.0',
        adb_available=adb_available,
        adb_info=adb_info,
        devices=devices
    )
    return Response(html_content)

@app.route('/api/status')
def api_status(request):
    """API endpoint de estado del sistema ADB"""
    adb_available, adb_info = ADBManager.check_adb_available()
    devices_success, devices = ADBManager.get_devices()
    
    return Response({
        'adb_available': adb_available,
        'adb_info': adb_info,
        'devices': devices if devices_success else [],
        'device_count': len(devices) if devices_success else 0
    }, headers={'Content-Type': 'application/json'})

@app.route('/api/devices')
def api_devices(request):
    """API endpoint para listar dispositivos"""
    success, devices = ADBManager.get_devices()
    if success:
        return Response(devices, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': devices}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/info')
def api_device_info(request, device_id):
    """API endpoint para obtener información detallada de un dispositivo"""
    success, info = ADBManager.get_device_info(device_id)
    if success:
        return Response(info, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': info}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/shell', methods=['POST'])
def api_shell_command(request, device_id):
    """API endpoint para ejecutar comando shell"""
    data = request.json
    command = data.get('command', '')
    
    if not command:
        return Response({'error': 'Comando requerido'}, status_code=400, headers={'Content-Type': 'application/json'})
    
    success, result = ADBManager.execute_shell_command(device_id, command)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/reboot', methods=['POST'])
def api_reboot(request, device_id):
    """API endpoint para reiniciar dispositivo"""
    data = request.json
    mode = data.get('mode', 'system')
    
    success, result = ADBManager.reboot_device(device_id, mode)
    if success:
        return Response({'success': True, 'message': result}, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/screenshot')
def api_screenshot(request, device_id):
    """API endpoint para capturar pantalla del dispositivo"""
    try:
        # Capturar pantalla
        success, result = ADBManager.execute_shell_command(device_id, 'screencap -p /sdcard/screenshot.png')
        if not success:
            return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})
        
        # Crear directorio temporal si no existe
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        local_path = os.path.join(temp_dir, f'screenshot_{device_id}.png')
        
        # Descargar captura
        success, result = ADBManager.pull_file(device_id, '/sdcard/screenshot.png', local_path)
        if not success:
            return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})
        
        # Limpiar archivo del dispositivo
        ADBManager.execute_shell_command(device_id, 'rm /sdcard/screenshot.png')
        
        return Response({'success': True, 'path': f'/_app/adb_manager/temp/screenshot_{device_id}.png'}, 
                       headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({'error': str(e)}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/check-python')
def api_check_python(request, device_id):
    """API endpoint para verificar entorno Python en dispositivo"""
    success, result = ADBManager.check_python_environment(device_id)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/create-environment', methods=['POST'])
def api_create_environment(request, device_id):
    """API endpoint para crear entorno UTPyApps en dispositivo"""
    data = request.json
    sudo_password = data.get('sudo_password')
    
    success, result = ADBManager.create_utpyapps_environment(device_id, sudo_password)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/copy-app', methods=['POST'])
def api_copy_app(request, device_id):
    """API endpoint para copiar app al dispositivo"""
    data = request.json
    app_name = data.get('app_name')
    sudo_password = data.get('sudo_password')
    
    if not app_name:
        return Response({'error': 'app_name requerido'}, status_code=400, headers={'Content-Type': 'application/json'})
    
    # Obtener directorio local de apps
    local_apps_dir = os.path.join(os.path.dirname(__file__), '..', '..')
    
    success, result = ADBManager.copy_app_to_device(device_id, app_name, local_apps_dir, sudo_password)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/start-utpyapps', methods=['POST'])
def api_start_utpyapps(request, device_id):
    """API endpoint para iniciar UTPyApps en dispositivo"""
    success, result = ADBManager.start_utpyapps_on_device(device_id)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/stop-utpyapps', methods=['POST'])
def api_stop_utpyapps(request, device_id):
    """API endpoint para detener UTPyApps en dispositivo"""
    success, result = ADBManager.stop_utpyapps_on_device(device_id)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/logs')
def api_logs(request, device_id):
    """API endpoint para obtener logs de UTPyApps"""
    success, result = ADBManager.get_utpyapps_logs(device_id)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/apps/local')
def api_local_apps(request):
    """API endpoint para listar apps locales disponibles"""
    try:
        local_apps_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        apps = []
        
        if os.path.exists(local_apps_dir):
            for app_folder in os.listdir(local_apps_dir):
                app_path = os.path.join(local_apps_dir, app_folder)
                if os.path.isdir(app_path):
                    manifest_path = os.path.join(app_path, 'app.json')
                    if os.path.exists(manifest_path):
                        with open(manifest_path) as f:
                            app_info = json.load(f)
                            app_info['folder'] = app_folder
                            apps.append(app_info)
        
        return Response(apps, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({'error': str(e)}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/open-browser', methods=['POST'])
def api_open_browser(request, device_id):
    """API endpoint para abrir morph-browser"""
    data = request.json
    url = data.get('url')
    
    success, result = ADBManager.open_morph_browser(device_id, url)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/open-terminal', methods=['POST'])
def api_open_terminal(request, device_id):
    """API endpoint para abrir lomiri-terminal-app"""
    data = request.json
    command = data.get('command')
    
    success, result = ADBManager.open_lomiri_terminal(device_id, command)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/ip')
def api_device_ip(request, device_id):
    """API endpoint para obtener IP del dispositivo"""
    success, result = ADBManager.get_device_ip(device_id)
    if success:
        return Response({'ip': result}, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/install-pip', methods=['POST'])
def api_install_pip(request, device_id):
    """API endpoint para instalar pip en el dispositivo"""
    data = request.json
    sudo_password = data.get('sudo_password')
    
    success, result = ADBManager.install_pip(device_id, sudo_password)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/install-virtualenv', methods=['POST'])
def api_install_virtualenv(request, device_id):
    """API endpoint para instalar virtualenv en el dispositivo"""
    data = request.json
    sudo_password = data.get('sudo_password')
    
    success, result = ADBManager.install_virtualenv(device_id, sudo_password)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/create-venv', methods=['POST'])
def api_create_venv(request, device_id):
    """API endpoint para crear entorno virtual"""
    data = request.json
    env_path = data.get('env_path', '~/utpyapps/venv')
    sudo_password = data.get('sudo_password')
    
    success, result = ADBManager.create_virtualenv(device_id, env_path, sudo_password)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/install-package', methods=['POST'])
def api_install_package(request, device_id):
    """API endpoint para instalar paquete en entorno virtual"""
    data = request.json
    package = data.get('package')
    env_path = data.get('env_path', '~/utpyapps/venv')
    sudo_password = data.get('sudo_password')
    
    if not package:
        return Response({'error': 'package requerido'}, status_code=400, headers={'Content-Type': 'application/json'})
    
    success, result = ADBManager.install_package_in_venv(device_id, package, env_path, sudo_password)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/install-pip-in-venv', methods=['POST'])
def api_install_pip_in_venv(request, device_id):
    """API endpoint para instalar pip dentro de un entorno virtual"""
    data = request.json
    env_path = data.get('env_path', '~/utpyapps/venv')
    sudo_password = data.get('sudo_password')
    
    success, result = ADBManager.install_pip_in_venv(device_id, env_path, sudo_password)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})
