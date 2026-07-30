# ADB Manager - Gestor de conexión ADB para Ubuntu Touch
# Name: ADB Manager
# Description: Gestor de conexión ADB para dispositivos Ubuntu Touch con interfaz Lomiri
# Author: UTPyApps
# Version: 1.0.0

from microdot import Microdot, Response
from microdot.websocket import with_websocket
from jinja2 import Environment, FileSystemLoader
import os
import subprocess
import json
import asyncio
from PIL import Image
import base64

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
            
            # Copiar main.py local directamente al dispositivo
            local_main = os.path.join(os.path.dirname(__file__), '../../main.py')
            push_result = subprocess.run(['adb', '-s', device_id, 'push', local_main, f'{base_dir}/main.py'],
                                       capture_output=True, text=True, timeout=30)
            
            # Dar permisos de ejecución
            chmod_cmd = ['adb', '-s', device_id, 'shell', f'chmod +x {base_dir}/main.py']
            if sudo_password:
                chmod_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S chmod +x {base_dir}/main.py']
            
            chmod_result = subprocess.run(chmod_cmd, capture_output=True, text=True, timeout=10)
            
            # Copiar script utpyapps.sh al dispositivo si existe
            local_utpyapps_sh = os.path.join(os.path.dirname(__file__), '..', '..', 'utpyapps.sh')
            if os.path.exists(local_utpyapps_sh):
                push_sh_result = subprocess.run(['adb', '-s', device_id, 'push', local_utpyapps_sh, f'{base_dir}/utpyapps.sh'],
                                               capture_output=True, text=True, timeout=30)
                
                # Dar permisos de ejecución
                chmod_sh_cmd = ['adb', '-s', device_id, 'shell', f'chmod +x {base_dir}/utpyapps.sh']
                if sudo_password:
                    chmod_sh_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S chmod +x {base_dir}/utpyapps.sh']
                
                subprocess.run(chmod_sh_cmd, capture_output=True, text=True, timeout=10)
                print(f"[UTPYAPPS_ENV] Script utpyapps.sh copiado al dispositivo")
            else:
                print(f"[UTPYAPPS_ENV] Script utpyapps.sh no encontrado en {local_utpyapps_sh}")
            
            # Copiar requirements.txt al dispositivo si existe
            local_requirements = os.path.join(os.path.dirname(__file__), '..', '..', 'requirements.txt')
            print(f"[UTPYAPPS_ENV] Ruta local requirements.txt: {local_requirements}")
            print(f"[UTPYAPPS_ENV] requirements.txt existe localmente: {os.path.exists(local_requirements)}")
            
            if os.path.exists(local_requirements):
                # Leer contenido local para verificar
                with open(local_requirements, 'r') as f:
                    local_content = f.read()
                print(f"[UTPYAPPS_ENV] Contenido local requirements.txt:\n{local_content}")
                
                push_req_result = subprocess.run(['adb', '-s', device_id, 'push', local_requirements, f'{base_dir}/requirements.txt'],
                                                capture_output=True, text=True, timeout=30)
                print(f"[UTPYAPPS_ENV] Push result: returncode={push_req_result.returncode}")
                print(f"[UTPYAPPS_ENV] Push stdout: {push_req_result.stdout}")
                print(f"[UTPYAPPS_ENV] Push stderr: {push_req_result.stderr}")
                
                # Verificar que se copió correctamente
                verify_cmd = ['adb', '-s', device_id, 'shell', f'cat {base_dir}/requirements.txt']
                verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
                print(f"[UTPYAPPS_ENV] Contenido en dispositivo:\n{verify_result.stdout}")
                
                # Crear venv en el dispositivo si no existe
                venv_path = f'{base_dir}/venv'
                check_venv = subprocess.run(['adb', '-s', device_id, 'shell', f'test -d {venv_path}'],
                                          capture_output=True, text=True, timeout=10)
                
                if check_venv.returncode != 0:
                    print(f"[UTPYAPPS_ENV] Creando venv en {venv_path}...")
                    venv_cmd = ['adb', '-s', device_id, 'shell', f'python3 -m venv --without-pip {venv_path}']
                    if sudo_password:
                        venv_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S python3 -m venv --without-pip {venv_path}']
                    
                    venv_result = subprocess.run(venv_cmd, capture_output=True, text=True, timeout=60)
                    print(f"[UTPYAPPS_ENV] venv creado: returncode={venv_result.returncode}")
                    
                    # Instalar pip en el venv
                    print(f"[UTPYAPPS_ENV] Instalando pip en venv...")
                    pip_install_cmd = ['adb', '-s', device_id, 'shell', f'wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py && {venv_path}/bin/python3 /tmp/get-pip.py']
                    if sudo_password:
                        pip_install_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S bash -c "wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py && {venv_path}/bin/python3 /tmp/get-pip.py"']
                    
                    pip_install_result = subprocess.run(pip_install_cmd, capture_output=True, text=True, timeout=120)
                    print(f"[UTPYAPPS_ENV] pip instalado en venv: returncode={pip_install_result.returncode}")
                
                # Instalar dependencias en el venv
                print(f"[UTPYAPPS_ENV] Instalando dependencias en venv...")
                install_cmd = ['adb', '-s', device_id, 'shell', f'cd {base_dir} && {venv_path}/bin/pip install -r requirements.txt']
                if sudo_password:
                    install_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S {venv_path}/bin/pip install -r {base_dir}/requirements.txt']
                
                install_result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
                print(f"[UTPYAPPS_ENV] Instalación de dependencias: returncode={install_result.returncode}")
                if install_result.returncode != 0:
                    print(f"[UTPYAPPS_ENV] Error instalando dependencias: {install_result.stderr}")
            else:
                print(f"[UTPYAPPS_ENV] requirements.txt no encontrado en {local_requirements}")
            
            # Crear servicio Upstart para auto-inicio
            upstart_config = '''description "UTPyApps Server"
author "UTPyApps"

start on started lomiri
stop on shutdown

script
    cd /home/phablet/utpyapps
    exec ./utpyapps.sh
end script
'''
            
            upstart_path = '/home/phablet/.config/upstart/utpyapps.conf'
            create_upstart_dir = subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', '/home/phablet/.config/upstart'],
                                               capture_output=True, text=True, timeout=10)
            
            if create_upstart_dir.returncode == 0:
                # Crear archivo upstart temporal
                temp_upstart = '/tmp/utpyapps.conf'
                with open(temp_upstart, 'w') as f:
                    f.write(upstart_config)
                
                # Copiar al dispositivo
                push_upstart = subprocess.run(['adb', '-s', device_id, 'push', temp_upstart, upstart_path],
                                              capture_output=True, text=True, timeout=30)
                
                os.remove(temp_upstart)
                
                if push_upstart.returncode == 0:
                    print(f"[UTPYAPPS_ENV] Servicio Upstart creado en {upstart_path}")
                else:
                    print(f"[UTPYAPPS_ENV] Error creando servicio Upstart: {push_upstart.stderr}")
            else:
                print(f"[UTPYAPPS_ENV] Error creando directorio upstart")
            
            return True, {
                'message': 'Entorno UTPyApps creado exitosamente',
                'directory': base_dir,
                'setup_results': results,
                'main_py_pushed': push_result.returncode == 0,
                'chmod_result': chmod_result.returncode == 0,
                'utpyapps_sh_copied': os.path.exists(local_utpyapps_sh),
                'requirements_installed': os.path.exists(local_requirements),
                'upstart_created': create_upstart_dir.returncode == 0 and push_upstart.returncode == 0
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
            
            # Iniciar UTPyApps automáticamente después de copiar la app
            try:
                # Verificar si existe utpyapps.sh en el dispositivo
                check_script = subprocess.run(['adb', '-s', device_id, 'shell', 'test', '-f', '~/utpyapps/utpyapps.sh'],
                                            capture_output=True, text=True, timeout=10)
                
                if check_script.returncode == 0:
                    # Usar utpyapps.sh para iniciar
                    start_cmd = ['adb', '-s', device_id, 'shell', 'cd ~/utpyapps && ./utpyapps.sh']
                    subprocess.run(start_cmd, capture_output=True, text=True, timeout=15)
                    print(f"[COPY_APP] UTPyApps iniciado con utpyapps.sh")
                else:
                    # Iniciar directamente con python3
                    start_cmd = ['adb', '-s', device_id, 'shell', 'cd ~/utpyapps && nohup python3 main.py > utpyapps.log 2>&1 &']
                    subprocess.run(start_cmd, capture_output=True, text=True, timeout=15)
                    print(f"[COPY_APP] UTPyApps iniciado directamente con python3")
            except Exception as e:
                print(f"[COPY_APP] Advertencia: No se pudo iniciar UTPyApps automáticamente: {e}")
            
            return True, {
                'message': f'App {app_name} copiada exitosamente y UTPyApps iniciado',
                'app_name': app_name,
                'remote_path': remote_app_path,
                'copied_files': copied_files,
                'total_files': len(copied_files),
                'utpyapps_started': True
            }
        except Exception as e:
            return False, f"Error copiando app: {str(e)}"
    
    @staticmethod
    def start_utpyapps_on_device(device_id):
        """Iniciar UTPyApps en el dispositivo usando utpyapps.sh si existe"""
        try:
            # Verificar si ya está corriendo usando .utpyapps.pid
            check_pid = subprocess.run(['adb', '-s', device_id, 'shell', 'test', '-f', '~/utpyapps/.utpyapps.pid'],
                                      capture_output=True, text=True, timeout=10)
            
            if check_pid.returncode == 0:
                # Leer el PID del archivo
                cat_pid = subprocess.run(['adb', '-s', device_id, 'shell', 'cat', '~/utpyapps/.utpyapps.pid'],
                                       capture_output=True, text=True, timeout=10)
                pid = cat_pid.stdout.strip() if cat_pid.returncode == 0 else None
                
                # Verificar si el proceso está vivo
                if pid:
                    check_process = subprocess.run(['adb', '-s', device_id, 'shell', f'kill -0 {pid} 2>/dev/null'],
                                                capture_output=True, text=True, timeout=10)
                    if check_process.returncode == 0:
                        return True, {
                            'message': 'UTPyApps ya está corriendo en el dispositivo',
                            'pid': pid,
                            'running': True
                        }
            
            # Verificar si existe utpyapps.sh
            check_script = subprocess.run(['adb', '-s', device_id, 'shell', 'test', '-f', '~/utpyapps/utpyapps.sh'],
                                        capture_output=True, text=True, timeout=10)
            
            if check_script.returncode == 0:
                # Usar utpyapps.sh para iniciar (en background para no bloquear)
                start_result = subprocess.run(['adb', '-s', device_id, 'shell', 'cd ~/utpyapps && nohup ./utpyapps.sh > /dev/null 2>&1 &'],
                                            capture_output=True, text=True, timeout=15)
                return True, {
                    'message': 'UTPyApps iniciado con utpyapps.sh',
                    'method': 'utpyapps.sh',
                    'success': start_result.returncode == 0,
                    'running': True
                }
            else:
                # Iniciar directamente con python3
                start_result = subprocess.run(['adb', '-s', device_id, 'shell', 'cd ~/utpyapps && nohup python3 main.py > utpyapps.log 2>&1 &'],
                                            capture_output=True, text=True, timeout=15)
                return True, {
                    'message': 'UTPyApps iniciado directamente con python3',
                    'method': 'python3',
                    'success': start_result.returncode == 0,
                    'running': True
                }
        except Exception as e:
            return False, f"Error iniciando UTPyApps: {str(e)}"
    
    @staticmethod
    def stop_utpyapps_on_device(device_id):
        """Detener UTPyApps en el dispositivo"""
        try:
            # Intentar usar utpyapps.sh --stop si existe
            check_script = subprocess.run(['adb', '-s', device_id, 'shell', 'test', '-f', '~/utpyapps/utpyapps.sh'],
                                        capture_output=True, text=True, timeout=10)
            
            if check_script.returncode == 0:
                # Usar utpyapps.sh --stop
                stop_result = subprocess.run(['adb', '-s', device_id, 'shell', 'cd ~/utpyapps && ./utpyapps.sh --stop'],
                                           capture_output=True, text=True, timeout=15)
                return True, {
                    'message': 'UTPyApps detenido con utpyapps.sh --stop',
                    'method': 'utpyapps.sh',
                    'success': stop_result.returncode == 0,
                    'running': False
                }
            else:
                # Matar el proceso directamente
                kill_result = subprocess.run(['adb', '-s', device_id, 'shell', 'pkill', '-f', 'utpyapps/main.py'],
                                           capture_output=True, text=True, timeout=10)
                return True, {
                    'message': 'UTPyApps detenido con pkill',
                    'method': 'pkill',
                    'success': kill_result.returncode == 0,
                    'running': False
                }
        except Exception as e:
            return False, f"Error deteniendo UTPyApps: {str(e)}"
    
    @staticmethod
    def check_upstart_service(device_id):
        """Verificar si el servicio Upstart está instalado y su estado"""
        try:
            upstart_path = '/home/phablet/.config/upstart/utpyapps.conf'
            
            # Verificar si el archivo de configuración existe
            check_config = subprocess.run(['adb', '-s', device_id, 'shell', f'test -f {upstart_path} && echo "exists" || echo "not_exists"'],
                                        capture_output=True, text=True, timeout=10)
            
            if check_config.returncode == 0 and 'exists' in check_config.stdout:
                # Verificar si el servicio está activo
                check_status = subprocess.run(['adb', '-s', device_id, 'shell', 'initctl status utpyapps'],
                                            capture_output=True, text=True, timeout=10)
                
                is_running = 'running' in check_status.stdout.lower() or 'start' in check_status.stdout.lower()
                
                return True, {
                    'installed': True,
                    'running': is_running,
                    'status': check_status.stdout.strip(),
                    'path': upstart_path
                }
            else:
                return True, {
                    'installed': False,
                    'running': False,
                    'status': 'Servicio Upstart no instalado',
                    'path': upstart_path
                }
        except Exception as e:
            return False, f"Error verificando servicio Upstart: {str(e)}"
    
    @staticmethod
    def enable_upstart_service(device_id):
        """Habilitar el servicio Upstart para auto-inicio"""
        try:
            upstart_path = '/home/phablet/.config/upstart/utpyapps.conf'
            
            # Verificar si ya existe
            check_config = subprocess.run(['adb', '-s', device_id, 'shell', f'test -f {upstart_path} && echo "exists" || echo "not_exists"'],
                                        capture_output=True, text=True, timeout=10)
            
            if check_config.returncode == 0 and 'exists' in check_config.stdout:
                # Reiniciar el servicio
                restart_result = subprocess.run(['adb', '-s', device_id, 'shell', 'initctl restart utpyapps'],
                                              capture_output=True, text=True, timeout=15)
                
                return True, {
                    'message': 'Servicio Upstart reiniciado',
                    'success': restart_result.returncode == 0,
                    'output': restart_result.stdout.strip()
                }
            else:
                # Crear el servicio Upstart
                upstart_config = '''description "UTPyApps Server"
author "UTPyApps"

start on started lomiri
stop on shutdown

script
    cd /home/phablet/utpyapps
    exec ./utpyapps.sh
end script
'''
                
                # Crear directorio
                create_dir = subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', '/home/phablet/.config/upstart'],
                                          capture_output=True, text=True, timeout=10)
                
                if create_dir.returncode != 0:
                    return False, "Error creando directorio upstart"
                
                # Crear archivo temporal
                temp_upstart = '/tmp/utpyapps.conf'
                with open(temp_upstart, 'w') as f:
                    f.write(upstart_config)
                
                # Copiar al dispositivo
                push_result = subprocess.run(['adb', '-s', device_id, 'push', temp_upstart, upstart_path],
                                           capture_output=True, text=True, timeout=30)
                
                os.remove(temp_upstart)
                
                if push_result.returncode == 0:
                    # Iniciar el servicio
                    start_result = subprocess.run(['adb', '-s', device_id, 'shell', 'initctl start utpyapps'],
                                                capture_output=True, text=True, timeout=15)
                    
                    return True, {
                        'message': 'Servicio Upstart creado e iniciado',
                        'success': True,
                        'output': start_result.stdout.strip()
                    }
                else:
                    return False, f"Error copiando archivo upstart: {push_result.stderr}"
        except Exception as e:
            return False, f"Error habilitando servicio Upstart: {str(e)}"
    
    @staticmethod
    def disable_upstart_service(device_id):
        """Deshabilitar el servicio Upstart"""
        try:
            upstart_path = '/home/phablet/.config/upstart/utpyapps.conf'
            
            # Detener el servicio si está corriendo
            stop_result = subprocess.run(['adb', '-s', device_id, 'shell', 'initctl stop utpyapps'],
                                       capture_output=True, text=True, timeout=15)
            
            # Eliminar el archivo de configuración
            remove_result = subprocess.run(['adb', '-s', device_id, 'shell', f'rm -f {upstart_path}'],
                                         capture_output=True, text=True, timeout=10)
            
            return True, {
                'message': 'Servicio Upstart deshabilitado',
                'stop_success': stop_result.returncode == 0,
                'remove_success': remove_result.returncode == 0
            }
        except Exception as e:
            return False, f"Error deshabilitando servicio Upstart: {str(e)}"
    
    @staticmethod
    def check_utpyapps_status(device_id):
        """Verificar si UTPyApps está corriendo en el dispositivo usando .utpyapps.pid"""
        try:
            # Verificar si existe el archivo .utpyapps.pid
            check_pid = subprocess.run(['adb', '-s', device_id, 'shell', 'test', '-f', '~/utpyapps/.utpyapps.pid'],
                                      capture_output=True, text=True, timeout=10)
            
            if check_pid.returncode == 0:
                # Leer el PID del archivo
                cat_pid = subprocess.run(['adb', '-s', device_id, 'shell', 'cat', '~/utpyapps/.utpyapps.pid'],
                                       capture_output=True, text=True, timeout=10)
                pid = cat_pid.stdout.strip() if cat_pid.returncode == 0 else None
                
                # Verificar si el proceso está vivo
                if pid:
                    check_process = subprocess.run(['adb', '-s', device_id, 'shell', f'kill -0 {pid} 2>/dev/null'],
                                                capture_output=True, text=True, timeout=10)
                    if check_process.returncode == 0:
                        return True, {
                            'running': True,
                            'pid': pid,
                            'message': 'UTPyApps está corriendo',
                            'method': '.utpyapps.pid'
                        }
                
                # Si el archivo existe pero el proceso no está vivo, considerarlo detenido
                return True, {
                    'running': False,
                    'pid': None,
                    'message': 'UTPyApps no está corriendo (archivo PID obsoleto)',
                    'method': '.utpyapps.pid'
                }
            else:
                return True, {
                    'running': False,
                    'pid': None,
                    'message': 'UTPyApps no está corriendo',
                    'method': '.utpyapps.pid'
                }
        except Exception as e:
            return False, f"Error verificando estado: {str(e)}"
    
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
                # Usar lomiri-url-dispatcher directamente (maneja el entorno internamente)
                result = subprocess.run(['adb', '-s', device_id, 'shell', 'lomiri-url-dispatcher', url],
                                      capture_output=True, text=True, timeout=15)
                
                # Si falla, intentar con lomiri-app-launch --desktop-file-hint
                if result.returncode != 0:
                    result = subprocess.run(['adb', '-s', device_id, 'shell', 
                                          'lomiri-app-launch', '--desktop-file-hint=/usr/share/applications/morph-browser.desktop', url],
                                          capture_output=True, text=True, timeout=15)
            else:
                # Abrir morph-browser usando lomiri-app-launch
                result = subprocess.run(['adb', '-s', device_id, 'shell', 
                                      'lomiri-app-launch', '--desktop-file-hint=/usr/share/applications/morph-browser.desktop'],
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
    def enable_wifi_display(device_id, sudo_password=None):
        """Habilitar pantalla WiFi (Miracast) en Ubuntu Touch"""
        try:
            # Preparar comando base con o sin password
            def build_sudo_cmd(cmd):
                if sudo_password:
                    return f'echo {sudo_password} | sudo -S {cmd}'
                return f'sudo {cmd}'
            
            # Paso 1: Configurar propiedades del sistema
            print("[WIFI_DISPLAY] Configurando propiedades del sistema...")
            setprop1_cmd = build_sudo_cmd('setprop ubuntu.widi.supported 1')
            setprop1_result = subprocess.run(['adb', '-s', device_id, 'shell', setprop1_cmd],
                                            capture_output=True, text=True, timeout=10)
            setprop2_cmd = build_sudo_cmd('setprop wifi.interface wlan0')
            setprop2_result = subprocess.run(['adb', '-s', device_id, 'shell', setprop2_cmd],
                                            capture_output=True, text=True, timeout=10)
            
            # Paso 2: Iniciar servicio aethercast con systemctl
            print("[WIFI_DISPLAY] Iniciando servicio aethercast...")
            start_cmd = build_sudo_cmd('systemctl start aethercast')
            start_result = subprocess.run(['adb', '-s', device_id, 'shell', start_cmd],
                                        capture_output=True, text=True, timeout=15)
            
            # Paso 3: Verificar estado del servicio
            print("[WIFI_DISPLAY] Verificando estado del servicio...")
            status_cmd = build_sudo_cmd('systemctl status aethercast')
            status_result = subprocess.run(['adb', '-s', device_id, 'shell', status_cmd],
                                         capture_output=True, text=True, timeout=10)
            
            is_running = 'active (running)' in status_result.stdout
            
            return True, {
                'message': 'Pantalla WiFi configurada' if is_running else 'Pantalla WiFi configurada pero servicio no iniciado',
                'setprop1_success': setprop1_result.returncode == 0,
                'setprop2_success': setprop2_result.returncode == 0,
                'service_started': start_result.returncode == 0,
                'service_running': is_running,
                'status_output': status_result.stdout,
                'status_error': status_result.stderr
            }
        except Exception as e:
            return False, f"Error habilitando pantalla WiFi: {str(e)}"
    
    @staticmethod
    def open_lomiri_terminal(device_id, command=None):
        """Abrir lomiri-terminal-app en el dispositivo con comando opcional"""
        try:
            if command:
                # Abrir terminal con comando específico usando lomiri-app-launch
                result = subprocess.run(['adb', '-s', device_id, 'shell', 
                                      'lomiri-app-launch', '--desktop-file-hint=/usr/share/applications/lomiri-terminal-app.desktop', command],
                                      capture_output=True, text=True, timeout=15)
            else:
                # Abrir terminal sin comando específico usando lomiri-app-launch
                result = subprocess.run(['adb', '-s', device_id, 'shell', 
                                      'lomiri-app-launch', '--desktop-file-hint=/usr/share/applications/lomiri-terminal-app.desktop'],
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
    
    @staticmethod
    def check_environment_status(device_id):
        """Verificar el estado del entorno de desarrollo en el dispositivo con múltiples métodos"""
        try:
            env_path = '/home/phablet/utpyapps'
            venv_path = '/home/phablet/utpyapps/venv'
            
            results = []
            
            def adb_test(test_cmd):
                """Ejecutar test en dispositivo y retornar True/False"""
                try:
                    full_cmd = ['adb', '-s', device_id, 'shell', test_cmd]
                    r = subprocess.run(full_cmd, capture_output=True, text=True, timeout=10)
                    # Usar returncode directamente: 0 = existe, 1 = no existe
                    exists = r.returncode == 0
                    print(f"[ENV CHECK] cmd='{test_cmd}' rc={r.returncode} stdout='{r.stdout.strip()}' stderr='{r.stderr.strip()}' exists={exists}")
                    return exists
                except Exception as e:
                    print(f"[ENV CHECK] cmd='{test_cmd}' ERROR: {e}")
                    return False
            
            def adb_python_test(code):
                """Ejecutar código Python en dispositivo para verificación más confiable"""
                try:
                    full_cmd = ['adb', '-s', device_id, 'shell', f'python3 -c "{code}"']
                    r = subprocess.run(full_cmd, capture_output=True, text=True, timeout=10)
                    # Si returncode es 0 y la salida contiene "True", existe
                    if r.returncode == 0 and 'True' in r.stdout:
                        print(f"[ENV CHECK PYTHON] code='{code}' result=True")
                        return True
                    print(f"[ENV CHECK PYTHON] code='{code}' result=False rc={r.returncode} stdout='{r.stdout.strip()}'")
                    return False
                except Exception as e:
                    print(f"[ENV CHECK PYTHON] code='{code}' ERROR: {e}")
                    return False
            
            def adb_ls_test(path):
                """Usar ls para verificar existencia (método alternativo)"""
                try:
                    full_cmd = ['adb', '-s', device_id, 'shell', f'ls -d {path} 2>/dev/null']
                    r = subprocess.run(full_cmd, capture_output=True, text=True, timeout=10)
                    # Si la salida contiene la ruta, existe
                    exists = r.returncode == 0 and path in r.stdout
                    print(f"[ENV CHECK LS] path='{path}' rc={r.returncode} stdout='{r.stdout.strip()}' exists={exists}")
                    return exists
                except Exception as e:
                    print(f"[ENV CHECK LS] path='{path}' ERROR: {e}")
                    return False
            
            # Etapa 1: Verificar directorio principal (múltiples métodos)
            stage1_test1 = adb_test(f'test -d {env_path}')
            stage1_test2 = adb_ls_test(env_path)
            stage1_test3 = adb_python_test(f'import os; print(os.path.isdir("{env_path}"))')
            # Usar consenso: si al menos 2 métodos dicen que existe, existe
            stage1_exists = sum([stage1_test1, stage1_test2, stage1_test3]) >= 2
            results.append({
                'stage': 1,
                'description': 'Directorio principal /home/phablet/utpyapps',
                'status': 'completed' if stage1_exists else 'pending',
                'exists': stage1_exists,
                'methods': {'test': stage1_test1, 'ls': stage1_test2, 'python': stage1_test3}
            })
            
            # Si el directorio principal no existe, no verificar el resto
            if not stage1_exists:
                return True, {
                    'message': 'Directorio principal no encontrado',
                    'completed': 0,
                    'total': 6,
                    'percentage': 0,
                    'is_complete': False,
                    'results': results
                }
            
            # Etapa 2: Verificar directorios copiados
            dirs_to_check = ['apps', 'static', 'templates']
            stage2_complete = True
            for dir_name in dirs_to_check:
                dir_path = f'{env_path}/{dir_name}'
                if not adb_test(f'test -d {dir_path}'):
                    stage2_complete = False
            results.append({
                'stage': 2,
                'description': 'Directorios copiados (apps, static, templates)',
                'status': 'completed' if stage2_complete else 'pending',
                'exists': stage2_complete
            })
            
            # Etapa 3: Verificar entorno virtual
            stage3_exists = adb_test(f'test -d {venv_path}')
            results.append({
                'stage': 3,
                'description': 'Entorno virtual creado',
                'status': 'completed' if stage3_exists else 'pending',
                'exists': stage3_exists
            })
            
            # Etapa 4: Verificar pip instalado
            stage4_exists = adb_test(f'test -f {venv_path}/bin/pip')
            results.append({
                'stage': 4,
                'description': 'Pip instalado en el entorno virtual',
                'status': 'completed' if stage4_exists else 'pending',
                'exists': stage4_exists
            })
            
            # Etapa 5: Verificar requirements.txt
            stage5_exists = adb_test(f'test -f {env_path}/requirements.txt')
            results.append({
                'stage': 5,
                'description': 'Requirements.txt generado',
                'status': 'completed' if stage5_exists else 'pending',
                'exists': stage5_exists
            })
            
            # Etapa 6: Verificar main.py
            stage6_exists = adb_test(f'test -f {env_path}/main.py')
            results.append({
                'stage': 6,
                'description': 'Main.py con sistema de montado dinámico',
                'status': 'completed' if stage6_exists else 'pending',
                'exists': stage6_exists
            })
            
            # Calcular porcentaje de completado
            completed = sum(1 for r in results if r['status'] == 'completed')
            total = len(results)
            percentage = int((completed / total) * 100)
            
            return True, {
                'message': 'Estado del entorno verificado',
                'completed': completed,
                'total': total,
                'percentage': percentage,
                'is_complete': completed == total,
                'results': results
            }
        except Exception as e:
            print(f"[ENV CHECK] Error general: {e}")
            return False, f"Error verificando entorno: {str(e)}"
    
    @staticmethod
    def setup_environment(device_id, sudo_password=None, local_apps_dir=None):
        """Configurar entorno de desarrollo automáticamente copiando estructura local
        
        Etapas:
        1. Crear directorio principal /home/phablet/utpyapps (sin sudo, en home del usuario)
        2. Copiar directorios desde sistema local (apps, static, templates)
        3. Crear entorno virtual con python3 -m venv --without-pip (sin sudo)
        4. Instalar pip dentro del venv y luego instalar requirements (sin sudo)
        5. Copiar main.py completo con sistema de montado dinámico
        6. Generar requirements.txt dinámico desde app.json de todas las apps
        7. Generar archivos .desktop para el launcher de Ubuntu Touch
        8. Crear servicio Upstart para auto-inicio al boot
        """
        try:
            results = []
            env_path = '/home/phablet/utpyapps'
            venv_path = '/home/phablet/utpyapps/venv'
            
            # Si no se especifica local_apps_dir, usar el directorio raíz del proyecto
            if not local_apps_dir:
                local_apps_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Etapa 1: Crear directorio principal (sin sudo, funciona en home del usuario)
            stage1_cmd = ['adb', '-s', device_id, 'shell', f'mkdir -p {env_path}']
            stage1_result = subprocess.run(stage1_cmd, capture_output=True, text=True, timeout=30)
            results.append({
                'stage': 1,
                'description': 'Crear directorio principal /home/phablet/utpyapps',
                'command': f'mkdir -p {env_path}',
                'success': stage1_result.returncode == 0,
                'output': stage1_result.stdout,
                'error': stage1_result.stderr
            })
            
            if stage1_result.returncode != 0:
                return False, {
                    'message': 'Error en etapa 1: No se pudo crear el directorio principal',
                    'failed_stage': 1,
                    'error': stage1_result.stderr,
                    'results': results
                }
            
            # Etapa 2: Copiar directorios desde sistema local
            dirs_to_copy = ['apps', 'static', 'templates']
            
            for dir_name in dirs_to_copy:
                local_dir = os.path.join(local_apps_dir, dir_name)
                if os.path.exists(local_dir):
                    # Copiar directorio completo usando adb push
                    push_cmd = ['adb', '-s', device_id, 'push', local_dir, f'{env_path}/{dir_name}']
                    push_result = subprocess.run(push_cmd, capture_output=True, text=True, timeout=60)
                    
                    results.append({
                        'stage': 2,
                        'description': f'Copiar directorio {dir_name} al dispositivo',
                        'command': f'push {local_dir} a {env_path}/{dir_name}',
                        'success': push_result.returncode == 0,
                        'output': push_result.stdout,
                        'error': push_result.stderr
                    })
            
            # Etapa 3: Crear entorno virtual con python3 nativo (sin sudo)
            stage3_cmd = ['adb', '-s', device_id, 'shell', f'python3 -m venv --without-pip {venv_path}']
            stage3_result = subprocess.run(stage3_cmd, capture_output=True, text=True, timeout=60)
            results.append({
                'stage': 3,
                'description': 'Crear entorno virtual con python3 -m venv --without-pip',
                'command': f'python3 -m venv --without-pip {venv_path}',
                'success': stage3_result.returncode == 0,
                'output': stage3_result.stdout,
                'error': stage3_result.stderr
            })
            
            if stage3_result.returncode != 0:
                return False, {
                    'message': 'Error en etapa 3: No se pudo crear el entorno virtual',
                    'failed_stage': 3,
                    'error': stage3_result.stderr,
                    'results': results
                }
            
            # Etapa 4: Descargar get-pip.py (sin sudo, /tmp es escribible)
            download_cmd = ['adb', '-s', device_id, 'shell', 'wget', 'https://bootstrap.pypa.io/get-pip.py', '-O', '/tmp/get-pip.py']
            download_result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=30)
            
            if download_result.returncode != 0:
                return False, {
                    'message': 'Error en etapa 4: No se pudo descargar get-pip.py',
                    'failed_stage': 4,
                    'error': download_result.stderr,
                    'results': results
                }
            
            # Etapa 5: Instalar pip dentro del venv (sin sudo)
            install_pip_cmd = ['adb', '-s', device_id, 'shell', f'{venv_path}/bin/python3', '/tmp/get-pip.py']
            install_pip_result = subprocess.run(install_pip_cmd, capture_output=True, text=True, timeout=60)
            
            # Limpiar archivo temporal
            subprocess.run(['adb', '-s', device_id, 'shell', 'rm', '/tmp/get-pip.py'],
                          capture_output=True, text=True, timeout=10)
            
            if install_pip_result.returncode != 0:
                return False, {
                    'message': 'Error en etapa 5: No se pudo instalar pip en el venv',
                    'failed_stage': 5,
                    'error': install_pip_result.stderr,
                    'results': results
                }
            
            results.append({
                'stage': 5,
                'description': 'Instalar pip dentro del entorno virtual',
                'command': f'{venv_path}/bin/python3 /tmp/get-pip.py',
                'success': install_pip_result.returncode == 0,
                'output': install_pip_result.stdout,
                'error': install_pip_result.stderr
            })
            
            # Etapa 6: Copiar requirements.txt del proyecto local
            local_requirements = os.path.join(os.path.dirname(__file__), '..', '..', 'requirements.txt')
            package_count = 0
            
            if os.path.exists(local_requirements):
                # Copiar requirements.txt del proyecto
                push_reqs_result = subprocess.run(['adb', '-s', device_id, 'push', local_requirements, f'{env_path}/requirements.txt'],
                                                  capture_output=True, text=True, timeout=30)
                
                # Contar paquetes
                with open(local_requirements, 'r') as f:
                    packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                package_count = len(packages)
                
                results.append({
                    'stage': 6,
                    'description': f'Copiar requirements.txt con {package_count} paquetes',
                    'command': f'push requirements.txt a {env_path}/requirements.txt',
                    'success': push_reqs_result.returncode == 0,
                    'output': push_reqs_result.stdout,
                    'error': push_reqs_result.stderr
                })
            else:
                # Fallback: generar requirements.txt dinámico desde app.json
                local_apps_path = os.path.join(local_apps_dir, 'apps')
                all_requirements = set()
                
                if os.path.exists(local_apps_path):
                    for app_folder in os.listdir(local_apps_path):
                        app_json_path = os.path.join(local_apps_path, app_folder, 'app.json')
                        if os.path.exists(app_json_path):
                            try:
                                with open(app_json_path) as f:
                                    app_data = json.load(f)
                                    if 'requirements' in app_data:
                                        all_requirements.update(app_data['requirements'])
                            except Exception as e:
                                print(f"Error leyendo {app_json_path}: {e}")
                
                # Agregar requirements básicos
                all_requirements.update(['microdot', 'jinja2'])
                package_count = len(all_requirements)
                
                # Crear requirements.txt temporal
                temp_reqs = '/tmp/utpyapps_requirements.txt'
                with open(temp_reqs, 'w') as f:
                    f.write('\n'.join(sorted(all_requirements)))
                
                # Copiar requirements.txt al dispositivo
                push_reqs_result = subprocess.run(['adb', '-s', device_id, 'push', temp_reqs, f'{env_path}/requirements.txt'],
                                                  capture_output=True, text=True, timeout=30)
                
                os.remove(temp_reqs)
                
                results.append({
                    'stage': 6,
                    'description': f'Generar requirements.txt con {package_count} paquetes (fallback)',
                    'command': f'push requirements.txt a {env_path}/requirements.txt',
                    'success': push_reqs_result.returncode == 0,
                    'output': push_reqs_result.stdout,
                    'error': push_reqs_result.stderr
                })
            
            # Etapa 7: Instalar requirements desde requirements.txt
            install_reqs_cmd = ['adb', '-s', device_id, 'shell', f'{venv_path}/bin/pip', 'install', '-r', f'{env_path}/requirements.txt']
            install_reqs_result = subprocess.run(install_reqs_cmd, capture_output=True, text=True, timeout=180)
            
            results.append({
                'stage': 7,
                'description': f'Instalar {package_count} paquetes desde requirements.txt',
                'command': f'{venv_path}/bin/pip install -r {env_path}/requirements.txt',
                'success': install_reqs_result.returncode == 0,
                'output': install_reqs_result.stdout,
                'error': install_reqs_result.stderr
            })
            
            # Etapa 8: Copiar main.py local directamente al dispositivo
            local_main = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'main.py')
            push_result = subprocess.run(['adb', '-s', device_id, 'push', local_main, f'{env_path}/main.py'],
                                       capture_output=True, text=True, timeout=30)
            
            results.append({
                'stage': 8,
                'description': 'Crear main.py con sistema de montado dinámico',
                'command': f'push main.py a {env_path}/main.py',
                'success': push_result.returncode == 0,
                'output': push_result.stdout,
                'error': push_result.stderr
            })
            
            # Etapa 9: Copiar utpyapps.sh (lanzador)
            local_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utpyapps.sh')
            if os.path.exists(local_script):
                push_script = subprocess.run(['adb', '-s', device_id, 'push', local_script, f'{env_path}/utpyapps.sh'],
                                             capture_output=True, text=True, timeout=30)
                # Permisos de ejecucion
                chmod_script = subprocess.run(['adb', '-s', device_id, 'shell', f'chmod +x {env_path}/utpyapps.sh'],
                                              capture_output=True, text=True, timeout=10)
                results.append({
                    'stage': 9,
                    'description': 'Copiar utpyapps.sh (lanzador)',
                    'command': f'push utpyapps.sh a {env_path}/utpyapps.sh',
                    'success': push_script.returncode == 0,
                    'output': push_script.stdout,
                    'error': push_script.stderr
                })
            
            # Etapa 10: Generar archivos .desktop para el launcher
            desktop_success, desktop_result = ADBManager.generate_desktop_files(device_id, local_apps_dir)
            results.append({
                'stage': 10,
                'description': 'Generar archivos .desktop para el launcher de Ubuntu Touch',
                'command': 'generate_desktop_files',
                'success': desktop_success,
                'output': str(desktop_result) if desktop_success else desktop_result,
                'error': desktop_result if not desktop_success else None
            })
            
            # Etapa 11: Crear servicio Upstart para auto-inicio
            upstart_config = '''description "UTPyApps Server"
author "UTPyApps"

start on started lomiri
stop on shutdown

script
    cd /home/phablet/utpyapps
    exec ./utpyapps.sh
end script
'''
            
            upstart_path = '/home/phablet/.config/upstart/utpyapps.conf'
            create_upstart_dir = subprocess.run(['adb', '-s', device_id, 'shell', 'mkdir', '-p', '/home/phablet/.config/upstart'],
                                               capture_output=True, text=True, timeout=10)
            
            upstart_success = False
            upstart_result = None
            
            if create_upstart_dir.returncode == 0:
                # Crear archivo upstart temporal
                temp_upstart = '/tmp/utpyapps.conf'
                with open(temp_upstart, 'w') as f:
                    f.write(upstart_config)
                
                # Copiar al dispositivo
                push_upstart = subprocess.run(['adb', '-s', device_id, 'push', temp_upstart, upstart_path],
                                              capture_output=True, text=True, timeout=30)
                
                os.remove(temp_upstart)
                
                if push_upstart.returncode == 0:
                    upstart_success = True
                    upstart_result = f'Servicio Upstart creado en {upstart_path}'
                else:
                    upstart_result = f'Error creando servicio Upstart: {push_upstart.stderr}'
            else:
                upstart_result = 'Error creando directorio upstart'
            
            results.append({
                'stage': 11,
                'description': 'Crear servicio Upstart para auto-inicio',
                'command': f'crear {upstart_path}',
                'success': upstart_success,
                'output': upstart_result if upstart_success else None,
                'error': upstart_result if not upstart_success else None
            })
            
            return True, {
                'message': 'Entorno configurado exitosamente con estructura copiada desde local',
                'env_path': env_path,
                'venv_path': venv_path,
                'python_path': f'{venv_path}/bin/python3',
                'pip_path': f'{venv_path}/bin/pip',
                'requirements_count': package_count,
                'results': results
            }
        except Exception as e:
            return False, f"Error configurando entorno: {str(e)}"
    
    @staticmethod
    def generate_desktop_files(device_id, local_apps_dir=None):
        """Generar archivos .desktop para las apps en el launcher de Ubuntu Touch"""
        try:
            apps_dir = '/home/phablet/utpyapps/apps'
            desktop_dir = '/home/phablet/.local/share/applications'
            icon_dir = '/home/phablet/.local/share/icons'
            
            results = []
            
            # Crear directorios necesarios
            mkdir_cmd = ['adb', '-s', device_id, 'shell', f'mkdir -p {desktop_dir} {icon_dir}']
            subprocess.run(mkdir_cmd, capture_output=True, text=True, timeout=10)
            
            # Verificar que el directorio de apps existe en el dispositivo
            check_apps_cmd = ['adb', '-s', device_id, 'shell', f'test -d {apps_dir}']
            check_result = subprocess.run(check_apps_cmd, capture_output=True, text=True, timeout=10)
            
            if check_result.returncode != 0:
                return False, "Directorio de apps no encontrado en el dispositivo"
            
            # Listar apps en el dispositivo
            ls_apps_cmd = ['adb', '-s', device_id, 'shell', f'ls {apps_dir}']
            ls_result = subprocess.run(ls_apps_cmd, capture_output=True, text=True, timeout=10)
            
            if ls_result.returncode != 0:
                return False, "Error listando apps en el dispositivo"
            
            app_folders = ls_result.stdout.strip().split('\n')
            
            for app_folder in app_folders:
                if not app_folder or app_folder.startswith('.'):
                    continue
                
                # Verificar que tenga app.json
                manifest_path = f'{apps_dir}/{app_folder}/app.json'
                check_manifest_cmd = ['adb', '-s', device_id, 'shell', f'test -f {manifest_path}']
                check_manifest_result = subprocess.run(check_manifest_cmd, capture_output=True, text=True, timeout=10)
                
                if check_manifest_result.returncode != 0:
                    continue
                
                # Leer el contenido de app.json desde el dispositivo
                cat_manifest_cmd = ['adb', '-s', device_id, 'shell', f'cat {manifest_path}']
                cat_result = subprocess.run(cat_manifest_cmd, capture_output=True, text=True, timeout=10)
                
                if cat_result.returncode != 0:
                    continue
                
                try:
                    manifest = json.loads(cat_result.stdout)
                except json.JSONDecodeError:
                    continue
                
                if manifest.get('hidden', False):
                    continue
                
                app_name = manifest.get('name', app_folder)
                app_description = manifest.get('description', '')
                app_icon = manifest.get('icon', '')
                
                # Generar contenido del .desktop
                desktop_content = f'''[Desktop Entry]
Version=1.0
Name={app_name}
Comment={app_description}
Exec=morph-browser --new-window http://localhost:8080/_app/{app_folder}/
Icon=utpyapps-{app_folder}
Terminal=false
Type=Application
Categories=Utility;
X-Lomiri-Touch=true
'''
                # Crear archivo temporal
                temp_desktop = f'/tmp/utpyapps_{app_folder}.desktop'
                with open(temp_desktop, 'w') as f:
                    f.write(desktop_content)
                
                # Push al dispositivo
                desktop_file = f'{desktop_dir}/utpyapps-{app_folder}.desktop'
                push_cmd = ['adb', '-s', device_id, 'push', temp_desktop, desktop_file]
                push_result = subprocess.run(push_cmd, capture_output=True, text=True, timeout=30)
                
                os.remove(temp_desktop)
                
                # Copiar icono si existe en el dispositivo
                if app_icon:
                    remote_icon_source = f'{apps_dir}/{app_folder}/static/{app_icon}'
                    check_icon_cmd = ['adb', '-s', device_id, 'shell', f'test -f {remote_icon_source}']
                    check_icon_result = subprocess.run(check_icon_cmd, capture_output=True, text=True, timeout=10)
                    
                    if check_icon_result.returncode == 0:
                        remote_icon_dest = f'{icon_dir}/utpyapps-{app_folder}.png'
                        # Usar adb shell cp para copiar el icono dentro del dispositivo
                        cp_icon_cmd = ['adb', '-s', device_id, 'shell', f'cp {remote_icon_source} {remote_icon_dest}']
                        icon_result = subprocess.run(cp_icon_cmd, capture_output=True, text=True, timeout=30)
                
                results.append({
                    'app': app_folder,
                    'name': app_name,
                    'desktop_file': desktop_file,
                    'success': push_result.returncode == 0
                })
            
            # Crear launcher principal para UTPyApps
            utpyapps_desktop_content = '''[Desktop Entry]
Version=1.0
Name=UTPyApps
Comment=Meta-lanzador para Ubuntu Touch
Exec=bash /home/phablet/utpyapps/utpyapps.sh
Icon=utpyapps
Terminal=false
Type=Application
Categories=Utility;
X-Lomiri-Touch=true
'''
            temp_utpyapps = '/tmp/utpyapps.desktop'
            with open(temp_utpyapps, 'w') as f:
                f.write(utpyapps_desktop_content)
            
            utpyapps_desktop_file = f'{desktop_dir}/utpyapps.desktop'
            push_utpyapps_cmd = ['adb', '-s', device_id, 'push', temp_utpyapps, utpyapps_desktop_file]
            push_utpyapps_result = subprocess.run(push_utpyapps_cmd, capture_output=True, text=True, timeout=30)
            
            os.remove(temp_utpyapps)
            
            # Copiar iconos de UTPyApps al dispositivo (PNG y SVG)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_png = os.path.join(project_root, 'static', 'images', 'UTPyApps.png')
            icon_svg = os.path.join(project_root, 'static', 'images', 'UTPyApps.svg')
            
            icon_copied = False
            if os.path.exists(icon_png):
                remote_icon_png = f'{icon_dir}/utpyapps.png'
                push_icon_cmd = ['adb', '-s', device_id, 'push', icon_png, remote_icon_png]
                icon_result = subprocess.run(push_icon_cmd, capture_output=True, text=True, timeout=30)
                icon_copied = icon_result.returncode == 0
            
            if os.path.exists(icon_svg):
                remote_icon_svg = f'{icon_dir}/utpyapps.svg'
                push_svg_cmd = ['adb', '-s', device_id, 'push', icon_svg, remote_icon_svg]
                svg_result = subprocess.run(push_svg_cmd, capture_output=True, text=True, timeout=30)
                icon_copied = icon_copied or svg_result.returncode == 0
            
            results.append({
                'app': 'utpyapps',
                'name': 'UTPyApps',
                'desktop_file': utpyapps_desktop_file,
                'success': push_utpyapps_result.returncode == 0,
                'icon_copied': icon_copied
            })
            
            # Reiniciar unity8 para que el launcher detecte los nuevos archivos .desktop
            restart_cmd = ['adb', '-s', device_id, 'shell', 'initctl restart unity8']
            restart_result = subprocess.run(restart_cmd, capture_output=True, text=True, timeout=30)
            results.append({
                'action': 'restart_unity8',
                'success': restart_result.returncode == 0,
                'result': restart_result.stdout
            })
            
            return True, {
                'message': f'Archivos .desktop generados para {len(results)-1} apps. Unity8 reiniciado para actualizar el launcher.',
                'results': results
            }
        except Exception as e:
            return False, f"Error generando archivos .desktop: {str(e)}"
    
    @staticmethod
    def remove_utpyapps(device_id, sudo_password=None):
        """Eliminar completamente UTPyApps del dispositivo (directorio y archivos .desktop)"""
        try:
            base_dir = '/home/phablet/utpyapps'
            desktop_dir = '/home/phablet/.local/share/applications'
            icon_dir = '/home/phablet/.local/share/icons'
            
            results = []
            
            # Eliminar directorio utpyapps
            rm_cmd = ['adb', '-s', device_id, 'shell', f'rm -rf {base_dir}']
            if sudo_password:
                rm_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S rm -rf {base_dir}']
            rm_result = subprocess.run(rm_cmd, capture_output=True, text=True, timeout=30)
            results.append({
                'action': 'remove_utpyapps_dir',
                'success': rm_result.returncode == 0,
                'result': rm_result.stdout
            })
            
            # Eliminar archivos .desktop de UTPyApps (incluyendo el principal)
            rm_desktop_cmd = ['adb', '-s', device_id, 'shell', f'rm -f {desktop_dir}/utpyapps-*.desktop {desktop_dir}/utpyapps.desktop']
            if sudo_password:
                rm_desktop_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S rm -f {desktop_dir}/utpyapps-*.desktop {desktop_dir}/utpyapps.desktop']
            rm_desktop_result = subprocess.run(rm_desktop_cmd, capture_output=True, text=True, timeout=30)
            results.append({
                'action': 'remove_desktop_files',
                'success': rm_desktop_result.returncode == 0,
                'result': rm_desktop_result.stdout
            })
            
            # Eliminar iconos de UTPyApps (incluyendo los iconos principales PNG y SVG)
            rm_icons_cmd = ['adb', '-s', device_id, 'shell', f'rm -f {icon_dir}/utpyapps-*.png {icon_dir}/utpyapps.png {icon_dir}/utpyapps.svg']
            if sudo_password:
                rm_icons_cmd = ['adb', '-s', device_id, 'shell', f'echo {sudo_password} | sudo -S rm -f {icon_dir}/utpyapps-*.png {icon_dir}/utpyapps.png {icon_dir}/utpyapps.svg']
            rm_icons_result = subprocess.run(rm_icons_cmd, capture_output=True, text=True, timeout=30)
            results.append({
                'action': 'remove_icons',
                'success': rm_icons_result.returncode == 0,
                'result': rm_icons_result.stdout
            })
            
            return True, {
                'message': 'UTPyApps eliminado completamente del dispositivo',
                'results': results
            }
        except Exception as e:
            return False, f"Error eliminando UTPyApps: {str(e)}"
    
    @staticmethod
    def take_screenshot(device_id, output_path=None):
        """Tomar captura de pantalla del dispositivo Ubuntu Touch"""
        try:
            import tempfile
            import time
            from PIL import Image
            import numpy as np
            
            if not output_path:
                output_path = os.path.join(tempfile.gettempdir(), 'screenshot.png')
            
            # Rutas en el dispositivo
            device_bgra = '/tmp/screenshot.bgra'
            
            print(f"[SCREENSHOT] Iniciando captura para dispositivo {device_id}")
            
            # Intentar encender la pantalla usando DBus
            try:
                # Simular actividad del usuario para encender la pantalla
                wake_cmd = ['adb', '-s', device_id, 'shell', 
                           'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/32011/bus gdbus call --session --dest com.lomiri.Shell --object-path /ScreenSaver --method org.freedesktop.ScreenSaver.SimulateUserActivity']
                subprocess.run(wake_cmd, capture_output=True, timeout=10)
                print(f"[SCREENSHOT] Intentando encender pantalla")
                time.sleep(1)  # Esperar a que la pantalla se encienda
            except Exception as e:
                print(f"[SCREENSHOT] Advertencia: No se pudo encender pantalla: {e}")
            
            # Obtener información del display para dimensiones
            query_cmd = ['adb', '-s', device_id, 'shell', 
                        'MIR_SOCKET=/run/mir_socket mirscreencast --query']
            query_result = subprocess.run(query_cmd, capture_output=True, text=True, timeout=10)
            print(f"[SCREENSHOT] Query output: {query_result.stdout}")
            
            # Parsear dimensiones del output
            width, height = 1080, 2340  # Valores por defecto
            if query_result.returncode == 0:
                for line in query_result.stdout.split('\n'):
                    if 'Output size:' in line:
                        try:
                            size_str = line.split('Output size:')[1].strip()
                            width, height = map(int, size_str.split('x'))
                            print(f"[SCREENSHOT] Dimensiones detectadas: {width}x{height}")
                        except:
                            pass
            
            # Capturar pantalla usando mirscreencast --stdout (formato RGBA)
            capture_cmd = ['adb', '-s', device_id, 'exec-out', 
                          f'MIR_SOCKET=/run/mir_socket mirscreencast -m /run/mir_socket --stdout --cap-interval 1 -s {width} {height} -n 1']
            print(f"[SCREENSHOT] Ejecutando: {' '.join(capture_cmd)}")
            capture_result = subprocess.run(capture_cmd, capture_output=True, timeout=30)
            
            if capture_result.returncode != 0:
                print(f"[SCREENSHOT] Error en captura: return code {capture_result.returncode}")
                return False, f"Error capturando pantalla: return code {capture_result.returncode}"
            
            rgba_data = capture_result.stdout
            print(f"[SCREENSHOT] Datos RGBA recibidos: {len(rgba_data)} bytes")
            
            expected_size = width * height * 4  # RGBA = 4 bytes por pixel
            if len(rgba_data) != expected_size:
                print(f"[SCREENSHOT] WARNING: Tamaño recibido ({len(rgba_data)}) != esperado ({expected_size})")
            
            # Convertir RGBA a PNG usando PIL
            try:
                # Crear imagen desde bytes RGBA
                img = Image.frombytes('RGBA', (width, height), rgba_data, 'raw', 'RGBA')
                
                # Convertir a RGB (descartar alpha)
                img_rgb = img.convert('RGB')
                
                # Guardar como PNG
                img_rgb.save(output_path, 'PNG')
                print(f"[SCREENSHOT] PNG guardado en: {output_path}")
                
                return True, {
                    'message': 'Captura de pantalla tomada exitosamente',
                    'path': output_path,
                    'width': width,
                    'height': height
                }
            except Exception as e:
                return False, f"Error procesando imagen: {str(e)}"
        except Exception as e:
            return False, f"Error en captura de pantalla: {str(e)}"
    
    @staticmethod
    def check_venv_status(device_id, venv_path='/home/phablet/.ubtool/venv'):
        """Verificar estado del entorno virtual global"""
        try:
            # Verificar si el directorio del venv existe
            check_cmd = f"test -d {venv_path} && echo 'exists' || echo 'not_exists'"
            result = subprocess.run(['adb', '-s', device_id, 'shell', check_cmd], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and 'exists' in result.stdout:
                # Verificar si python está disponible en el venv
                python_check = f"test -f {venv_path}/bin/python && echo 'ready' || echo 'incomplete'"
                python_result = subprocess.run(['adb', '-s', device_id, 'shell', python_check], 
                                             capture_output=True, text=True, timeout=10)
                
                # Verificar si pip está disponible en el venv
                pip_check = f"test -f {venv_path}/bin/pip && echo 'ready' || echo 'incomplete'"
                pip_result = subprocess.run(['adb', '-s', device_id, 'shell', pip_check], 
                                          capture_output=True, text=True, timeout=10)
                
                if python_result.returncode == 0 and 'ready' in python_result.stdout and \
                   pip_result.returncode == 0 and 'ready' in pip_result.stdout:
                    return True, {
                        'status': 'ready',
                        'message': 'Entorno global listo para usar',
                        'venv_path': venv_path,
                        'python_path': f'{venv_path}/bin/python',
                        'pip_path': f'{venv_path}/bin/pip'
                    }
                else:
                    return True, {
                        'status': 'incomplete',
                        'message': 'Entorno global incompleto',
                        'venv_path': venv_path,
                        'python_path': f'{venv_path}/bin/python',
                        'pip_path': f'{venv_path}/bin/pip'
                    }
            else:
                return True, {
                    'status': 'not_created',
                    'message': 'Entorno global no creado',
                    'venv_path': venv_path,
                    'python_path': 'N/A',
                    'pip_path': 'N/A'
                }
        except Exception as e:
            return False, f"Error verificando estado del venv: {str(e)}"
    
    @staticmethod
    def list_venv_packages(device_id, venv_path='/home/phablet/.ubtool/venv'):
        """Listar paquetes instalados en el entorno virtual"""
        try:
            global_venv_python = f"{venv_path}/bin/python"
            
            # List packages usando pip list
            cmd = f"{global_venv_python} -m pip list --format=json"
            result = subprocess.run(['adb', '-s', device_id, 'shell', cmd], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                try:
                    packages_data = json.loads(result.stdout)
                    packages = []
                    
                    for pkg in packages_data:
                        packages.append({
                            'name': pkg.get('name', 'Unknown'),
                            'version': pkg.get('version', 'N/A')
                        })
                    
                    return True, {
                        'packages': packages,
                        'total': len(packages)
                    }
                except json.JSONDecodeError:
                    # Fallback a parsing de texto plano
                    lines = result.stdout.strip().split('\n')
                    packages = []
                    for line in lines:
                        if '==' in line:
                            name, version = line.split('==')
                            packages.append({
                                'name': name.strip(),
                                'version': version.strip() if version else 'N/A'
                            })
                    
                    return True, {
                        'packages': packages,
                        'total': len(packages)
                    }
            else:
                return False, f'Error listando paquetes: {result.stderr}'
        except Exception as e:
            return False, f"Error listando paquetes: {str(e)}"

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
    
    # Verificar estado del entorno si hay dispositivos conectados
    environment_status = None
    if devices and len(devices) > 0:
        first_device = devices[0]
        if isinstance(first_device, dict):
            first_device_id = first_device.get('id')
        else:
            first_device_id = getattr(first_device, 'id', None)
        
        if first_device_id:
            env_success, env_result = ADBManager.check_environment_status(first_device_id)
            if env_success:
                environment_status = env_result
    
    html_content = template.render(
        app_name='ADB Manager',
        app_description='Gestor de conexión ADB para Ubuntu Touch',
        app_version='1.0.0',
        adb_available=adb_available,
        adb_info=adb_info,
        devices=devices,
        environment_status=environment_status
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

@app.route('/ws/device/<device_id>/screen')
@with_websocket
async def screen_stream(request, ws, device_id):
    """WebSocket endpoint para streaming de pantalla del dispositivo"""
    try:
        print(f"[STREAM] Iniciando streaming para dispositivo {device_id}")
        
        # Enviar mensaje de conexión
        await ws.send(json.dumps({'type': 'connected', 'device_id': device_id}))
        
        frame_count = 0
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        screenshot_path = os.path.join(temp_dir, f'screenshot_{device_id}.png')
        
        while True:
            try:
                # Capturar pantalla usando mirscreencast
                success, result = ADBManager.take_screenshot(device_id, screenshot_path)
                
                if success:
                    # Leer el archivo PNG
                    if os.path.exists(screenshot_path):
                        with open(screenshot_path, 'rb') as f:
                            img_bytes = f.read()
                        
                        # Codificar en base64
                        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                        
                        # Obtener dimensiones
                        img = Image.open(screenshot_path)
                        width, height = img.size
                        
                        # Enviar frame via WebSocket
                        await ws.send(json.dumps({
                            'type': 'frame',
                            'frame_number': frame_count,
                            'width': width,
                            'height': height,
                            'image': img_base64
                        }))
                        
                        frame_count += 1
                        
                        # Eliminar archivo temporal
                        os.remove(screenshot_path)
                    else:
                        print(f"[STREAM] Archivo screenshot no encontrado: {screenshot_path}")
                else:
                    print(f"[STREAM] Error capturando pantalla: {result}")
                    await ws.send(json.dumps({'type': 'error', 'message': result}))
                    break
                
                # Esperar antes de la siguiente captura (1 segundo = 1 FPS)
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                print(f"[STREAM] Cliente desconectado del dispositivo {device_id}")
                break
            except Exception as e:
                print(f"[STREAM] Error en streaming: {e}")
                try:
                    await ws.send(json.dumps({'type': 'error', 'message': str(e)}))
                except:
                    pass
                break
                
    except asyncio.CancelledError:
        print(f"[STREAM] Cliente desconectado del dispositivo {device_id}")
    except Exception as e:
        print(f"[STREAM] Error en streaming: {e}")
        try:
            await ws.send(json.dumps({'type': 'error', 'message': str(e)}))
        except:
            pass

@app.route('/api/device/<device_id>/screenshot')
def api_screenshot(request, device_id):
    """API endpoint para capturar pantalla del dispositivo Ubuntu Touch"""
    try:
        # Crear directorio temporal si no existe
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        local_path = os.path.join(temp_dir, f'screenshot_{device_id}.png')
        
        # Capturar pantalla usando mirscreencast
        success, result = ADBManager.take_screenshot(device_id, local_path)
        if not success:
            return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})
        
        return Response({'success': True, 'path': f'/_app/adb_manager/temp/screenshot_{device_id}.png', 
                        'width': result.get('width'), 'height': result.get('height')}, 
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

@app.route('/api/device/<device_id>/upstart-status', methods=['GET'])
def api_upstart_status(request, device_id):
    """API endpoint para verificar estado del servicio Upstart"""
    success, result = ADBManager.check_upstart_service(device_id)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/upstart-enable', methods=['POST'])
def api_upstart_enable(request, device_id):
    """API endpoint para habilitar el servicio Upstart"""
    success, result = ADBManager.enable_upstart_service(device_id)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/upstart-disable', methods=['POST'])
def api_upstart_disable(request, device_id):
    """API endpoint para deshabilitar el servicio Upstart"""
    success, result = ADBManager.disable_upstart_service(device_id)
    if success:
        return Response(result, headers={'Content-Type': 'application/json'})
    else:
        return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/check-utpyapps', methods=['GET'])
def api_check_utpyapps(request, device_id):
    """API endpoint para verificar estado de UTPyApps en dispositivo"""
    success, result = ADBManager.check_utpyapps_status(device_id)
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

@app.route('/api/device/<device_id>/enable-wifi-display', methods=['POST'])
def api_enable_wifi_display(request, device_id):
    """API endpoint para habilitar pantalla WiFi (Miracast)"""
    data = request.json
    sudo_password = data.get('sudo_password')
    
    success, result = ADBManager.enable_wifi_display(device_id, sudo_password)
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

@app.route('/api/device/<device_id>/setup-environment', methods=['POST'])
def api_setup_environment(request, device_id):
    """API endpoint para configurar entorno de desarrollo automáticamente"""
    try:
        data = request.json
        sudo_password = data.get('sudo_password')
        local_apps_dir = data.get('local_apps_dir')
        
        success, result = ADBManager.setup_environment(device_id, sudo_password, local_apps_dir)
        if success:
            return Response(result, headers={'Content-Type': 'application/json'})
        else:
            return Response({'error': result}, status_code=500, headers={'Content-Type': 'application/json'})
    except Exception as e:
        print(f"Error en api_setup_environment: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'Error interno: {str(e)}'}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/check-environment')
def api_check_environment(request, device_id):
    """API endpoint para verificar el estado del entorno de desarrollo"""
    try:
        success, result = ADBManager.check_environment_status(device_id)
        if success:
            return Response(json.dumps(result), headers={'Content-Type': 'application/json'})
        else:
            return Response(json.dumps({'error': result}), status_code=500, headers={'Content-Type': 'application/json'})
    except Exception as e:
        print(f"Error en api_check_environment: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'Error interno: {str(e)}'}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/generate-desktop', methods=['POST'])
def api_generate_desktop(request, device_id):
    """API endpoint para Fase 5: Generar archivos .desktop en el launcher de Ubuntu Touch"""
    try:
        data = request.json
        local_apps_dir = data.get('local_apps_dir', '/media/lukas/ARCHIVOS/GitHub/ubpyapps')
        
        success, result = ADBManager.generate_desktop_files(device_id, local_apps_dir)
        if success:
            return Response(json.dumps({'success': True, 'message': result}), headers={'Content-Type': 'application/json'})
        else:
            return Response(json.dumps({'success': False, 'error': result}), status_code=500, headers={'Content-Type': 'application/json'})
    except Exception as e:
        print(f"Error en api_generate_desktop: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(json.dumps({'success': False, 'error': f'Error interno: {str(e)}'}), status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/device/<device_id>/remove-utpyapps', methods=['POST'])
def api_remove_utpyapps(request, device_id):
    """API endpoint para eliminar completamente UTPyApps del dispositivo"""
    try:
        data = request.json
        sudo_password = data.get('sudo_password')
        
        success, result = ADBManager.remove_utpyapps(device_id, sudo_password)
        if success:
            return Response(json.dumps({'success': True, 'message': result}), headers={'Content-Type': 'application/json'})
        else:
            return Response(json.dumps({'success': False, 'error': result}), status_code=500, headers={'Content-Type': 'application/json'})
    except Exception as e:
        print(f"Error en api_remove_utpyapps: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(json.dumps({'success': False, 'error': f'Error interno: {str(e)}'}), status_code=500, headers={'Content-Type': 'application/json'})
