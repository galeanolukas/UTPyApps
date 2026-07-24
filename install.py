#!/usr/bin/env python3
"""
UTPyApps Multiplatform Installer
Este script instala UTPyApps en Linux, Windows y Ubuntu Touch usando Python3 y requests
"""

import os
import sys
import subprocess
import json
import shutil
import platform
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ Error: requests no está instalado")
    print("📦 Instalando requests...")
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# Configuración
INSTALL_DIR = Path.home() / "utpyapps"
REPO_URL = "https://raw.githubusercontent.com/galeanolukas/UTPyApps/main"
REPO_API_URL = "https://api.github.com/repos/galeanolukas/UTPyApps/contents"
BRANCH = "main"

def print_step(message, emoji="📋"):
    print(f"{emoji} {message}")

def print_success(message, emoji="✅"):
    print(f"{emoji} {message}")

def print_error(message, emoji="❌"):
    print(f"{emoji} {message}")

def print_warning(message, emoji="⚠️"):
    print(f"{emoji} {message}")

def detect_platform():
    """Detectar el sistema operativo"""
    system = platform.system().lower()
    if system == "linux":
        # Verificar si es Ubuntu Touch
        if os.path.exists("/usr/bin/lomiri-app-launch") or os.path.exists("/usr/bin/unity8"):
            return "ubuntu_touch"
        return "linux"
    elif system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    else:
        return "unknown"

def check_python():
    """Verificar Python3"""
    print_step("Verificando Python3...")
    version = sys.version
    print_success(f"Python3 encontrado: {version}")
    return True

def check_pip():
    """No verificar pip del sistema - se instalará dentro del venv"""
    print_step("Omitiendo verificación de pip del sistema...")
    print_success("pip se instalará dentro del entorno virtual")
    return True

def download_file(url, dest_path):
    """Descargar un archivo desde URL"""
    try:
        print_step(f"Descargando: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        print_success(f"Descargado: {dest_path.name}")
        return True
    except Exception as e:
        print_error(f"Error descargando {url}: {e}")
        return False

def download_directory(api_url, dest_dir):
    """Descargar un directorio completo desde GitHub usando la API"""
    try:
        response = requests.get(f"{api_url}?ref={BRANCH}", timeout=30)
        response.raise_for_status()
        contents = response.json()
        
        success_count = 0
        total_count = 0
        
        for item in contents:
            total_count += 1
            if item['type'] == 'file':
                download_url = item['download_url']
                dest_path = dest_dir / item['path']
                if download_file(download_url, dest_path):
                    success_count += 1
            elif item['type'] == 'dir':
                # Recursivamente descargar subdirectorios
                sub_api_url = f"{REPO_API_URL}/{item['path']}"
                sub_success, sub_total = download_directory(sub_api_url, dest_dir)
                success_count += sub_success
                total_count += sub_total - 1  # -1 porque ya contamos el directorio
        
        return success_count, total_count
    except Exception as e:
        print_error(f"Error descargando directorio {api_url}: {e}")
        return 0, 0

def download_files():
    """Descargar todos los archivos necesarios"""
    print_step("Descargando archivos desde GitHub...")
    
    # Archivos principales
    files = {
        "main.py": "main.py",
        "utpyapps.sh": "utpyapps.sh",
        "requirements.txt": "requirements.txt",
    }
    
    # Archivos estáticos
    static_files = {
        "static/css/w3.css": "static/css/w3.css",
        "static/css/editor.css": "static/css/editor.css",
        "static/js/common.js": "static/js/common.js",
        "static/js/editor.js": "static/js/editor.js",
        "static/js/ubtool.js": "static/js/ubtool.js",
        "static/images/UTPyApps.png": "static/images/UTPyApps.png",
    }
    
    # Templates
    template_files = {
        "templates/base_layout.html": "templates/base_layout.html",
        "templates/index.html": "templates/index.html",
        "templates/create_app.html": "templates/create_app.html",
        "templates/app_view.html": "templates/app_view.html",
        "templates/app_index.html": "templates/app_index.html",
        "templates/app_detail.html": "templates/app_detail.html",
        "templates/editor.html": "templates/editor.html",
    }
    
    # Locales
    locale_files = {
        "locales/es.json": "locales/es.json",
        "locales/en.json": "locales/en.json",
    }
    
    all_files = {**files, **static_files, **template_files, **locale_files}
    
    success_count = 0
    for remote_path, local_path in all_files.items():
        url = f"{REPO_URL}/{remote_path}"
        dest_path = INSTALL_DIR / local_path
        if download_file(url, dest_path):
            success_count += 1
        else:
            print_error(f"Falló: {remote_path}")
    
    print_success(f"Descargados {success_count}/{len(all_files)} archivos")
    
    # Descargar directorio apps completo usando API
    print_step("Descargando directorio apps desde GitHub...")
    apps_api_url = f"{REPO_API_URL}/apps"
    apps_success, apps_total = download_directory(apps_api_url, INSTALL_DIR)
    print_success(f"Descargados {apps_success}/{apps_total} archivos de apps")
    
    return success_count == len(all_files) and apps_success > 0

def create_virtualenv():
    """Crear entorno virtual de Python"""
    print_step("Creando entorno virtual de Python...")
    try:
        # Detectar plataforma para usar el comando correcto
        platform_type = detect_platform()
        
        if platform_type == "ubuntu_touch":
            # Ubuntu Touch - usar --without-pip
            print_step("Usando --without-pip para Ubuntu Touch...")
            result = subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(INSTALL_DIR / "venv")], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print_success("Entorno virtual creado con --without-pip")
                return True
            
            # Fallback a método normal
            print_step("Intentando con python3 -m venv normal...")
            result = subprocess.run([sys.executable, "-m", "venv", str(INSTALL_DIR / "venv")], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print_success("Entorno virtual creado con método normal")
                return True
        else:
            # Linux/Windows - usar método normal
            result = subprocess.run([sys.executable, "-m", "venv", str(INSTALL_DIR / "venv")], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print_success("Entorno virtual creado")
                return True
        
        print_error(f"Error creando entorno virtual: {result.stderr}")
        return False
    except Exception as e:
        print_error(f"Error creando entorno virtual: {e}")
        return False

def install_dependencies():
    """Instalar dependencias de Python"""
    platform_type = detect_platform()
    
    if platform_type == "ubuntu_touch":
        # Ubuntu Touch - usar get-pip.py
        venv_python = INSTALL_DIR / "venv" / "bin" / "python3"
        requirements_file = INSTALL_DIR / "requirements.txt"
        
        # Etapa 1: Descargar get-pip.py
        print_step("Etapa 1: Descargando get-pip.py...")
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = INSTALL_DIR / "get-pip.py"
        
        if not download_file(get_pip_url, get_pip_path):
            print_error("Error descargando get-pip.py")
            return False
        print_success("get-pip.py descargado")
        
        # Etapa 2: Instalar pip dentro del venv
        print_step("Etapa 2: Instalando pip dentro del venv...")
        result = subprocess.run([str(venv_python), str(get_pip_path)], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print_error(f"Error instalando pip: {result.stderr}")
            return False
        print_success("pip instalado dentro del venv")
        
        # Etapa 3: Instalar dependencias
        print_step("Etapa 3: Instalando dependencias...")
        venv_pip = INSTALL_DIR / "venv" / "bin" / "pip"
        result = subprocess.run([str(venv_pip), "install", "-r", str(requirements_file)], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print_error(f"Error instalando dependencias: {result.stderr}")
            return False
        print_success("Dependencias instaladas")
        return True
    else:
        # Linux/Windows - usar pip del venv directamente
        if platform_type == "windows":
            venv_pip = INSTALL_DIR / "venv" / "Scripts" / "pip.exe"
        else:
            venv_pip = INSTALL_DIR / "venv" / "bin" / "pip"
        
        requirements_file = INSTALL_DIR / "requirements.txt"
        
        print_step("Instalando dependencias...")
        result = subprocess.run([str(venv_pip), "install", "-r", str(requirements_file)], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print_error(f"Error instalando dependencias: {result.stderr}")
            return False
        print_success("Dependencias instaladas")
        return True

def setup_permissions():
    """Configurar permisos de ejecución (solo Linux/Ubuntu Touch)"""
    platform_type = detect_platform()
    
    if platform_type == "windows":
        print_step("Omitiendo configuración de permisos en Windows...")
        return True
    
    print_step("Configurando permisos...")
    utpyapps_sh = INSTALL_DIR / "utpyapps.sh"
    try:
        os.chmod(utpyapps_sh, 0o755)
        print_success("Permisos configurados")
        return True
    except Exception as e:
        print_error(f"Error configurando permisos: {e}")
        return False

def create_utpyapps_dir():
    """Crear directorio .utpyapps para PID"""
    print_step("Creando directorio .utpyapps...")
    utpyapps_dir = Path.home() / ".utpyapps"
    try:
        utpyapps_dir.mkdir(parents=True, exist_ok=True)
        print_success("Directorio .utpyapps creado")
        return True
    except Exception as e:
        print_error(f"Error creando directorio: {e}")
        return False

def create_desktop_file():
    """Crear archivo .desktop para el launcher (solo Ubuntu Touch)"""
    platform_type = detect_platform()
    
    if platform_type != "ubuntu_touch":
        print_step("Omitiendo creación de archivo .desktop (no es Ubuntu Touch)...")
        return True
    
    print_step("Creando archivo .desktop para el launcher...")
    
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    icons_dir = Path.home() / ".local" / "share" / "icons"
    
    try:
        # Crear directorios
        desktop_dir.mkdir(parents=True, exist_ok=True)
        icons_dir.mkdir(parents=True, exist_ok=True)
        
        # Contenido del archivo .desktop
        desktop_content = """[Desktop Entry]
Version=1.0
Name=UTPyApps
Comment=Meta-lanzador Python para Ubuntu Touch
Exec={install_dir}/utpyapps.sh
Icon=utpyapps
Terminal=false
Type=Application
Categories=Utility;
""".format(install_dir=INSTALL_DIR)
        
        desktop_file = desktop_dir / "utpyapps.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        # Copiar icono si existe
        icon_source = INSTALL_DIR / "static" / "images" / "UTPyApps.png"
        icon_dest = icons_dir / "utpyapps.png"
        
        if icon_source.exists():
            shutil.copy(icon_source, icon_dest)
            print_success("Icono copiado")
        else:
            print_warning("Icono no encontrado, usando icono genérico")
        
        # Dar permisos
        os.chmod(desktop_file, 0o644)
        
        print_success("Archivo .desktop creado")
        return True
    except Exception as e:
        print_error(f"Error creando archivo .desktop: {e}")
        return False

def create_autostart_config():
    """Crear configuración de autostart (solo Ubuntu Touch)"""
    platform_type = detect_platform()
    
    if platform_type != "ubuntu_touch":
        print_step("Omitiendo configuración de autostart (no es Ubuntu Touch)...")
        return True
    
    print_step("Creando configuración de autostart...")
    
    upstart_dir = Path.home() / ".config" / "upstart"
    
    try:
        # Crear directorio
        upstart_dir.mkdir(parents=True, exist_ok=True)
        
        # Contenido del archivo upstart
        upstart_content = """description "UTPyApps Server"
author "UTPyApps"

start on started lomiri
stop on shutdown

script
    cd {install_dir}
    exec ./utpyapps.sh
end script
""".format(install_dir=INSTALL_DIR)
        
        upstart_file = upstart_dir / "utpyapps.conf"
        with open(upstart_file, 'w') as f:
            f.write(upstart_content)
        
        # Dar permisos
        os.chmod(upstart_file, 0o644)
        
        print_success("Configuración de autostart creada")
        return True
    except Exception as e:
        print_error(f"Error creando configuración de autostart: {e}")
        return False

def create_windows_shortcut():
    """Crear acceso directo en Windows (solo Windows)"""
    platform_type = detect_platform()
    
    if platform_type != "windows":
        print_step("Omitiendo creación de acceso directo (no es Windows)...")
        return True
    
    print_step("Creando acceso directo en Windows...")
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "UTPyApps.lnk"
        target = str(INSTALL_DIR / "utpyapps.sh")
        
        # Nota: utpyapps.sh es un script bash, en Windows necesitamos usar Git Bash o WSL
        # Por ahora solo creamos un acceso directo al directorio
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.Targetpath = str(INSTALL_DIR)
        shortcut.save()
        
        print_success("Acceso directo creado en el escritorio")
        return True
    except ImportError:
        print_warning("No se pudo crear acceso directo (requiere pywin32)")
        return True
    except Exception as e:
        print_error(f"Error creando acceso directo: {e}")
        return True

def main():
    """Función principal de instalación"""
    print("=" * 60)
    print("🚀 Instalando UTPyApps")
    print("=" * 60)
    print()
    
    # Detectar plataforma
    platform_type = detect_platform()
    print_step(f"Plataforma detectada: {platform_type}")
    print()
    
    # Verificar Python
    if not check_python():
        print_error("Python3 no disponible")
        sys.exit(1)
    
    # Verificar pip
    if not check_pip():
        print_error("pip no disponible")
        sys.exit(1)
    
    # Preparar directorio
    print_step("Preparando directorio de instalación...")
    if INSTALL_DIR.exists():
        print_warning(f"El directorio {INSTALL_DIR} ya existe")
        response = input("¿Deseas continuar? (s/n): ").strip().lower()
        if response != 's':
            print_error("Instalación cancelada")
            sys.exit(1)
        print_step("Eliminando directorio existente...")
        shutil.rmtree(INSTALL_DIR)
    
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    print_success(f"Directorio creado: {INSTALL_DIR}")
    
    # Descargar archivos
    if not download_files():
        print_error("Error descargando archivos")
        sys.exit(1)
    
    # Crear entorno virtual
    if not create_virtualenv():
        print_error("Error creando entorno virtual")
        sys.exit(1)
    
    # Instalar dependencias
    if not install_dependencies():
        print_error("Error instalando dependencias")
        sys.exit(1)
    
    # Configurar permisos
    if not setup_permissions():
        print_error("Error configurando permisos")
        sys.exit(1)
    
    # Crear directorio .utpyapps
    if not create_utpyapps_dir():
        print_error("Error creando directorio .utpyapps")
        sys.exit(1)
    
    # Crear archivo .desktop (Ubuntu Touch)
    if not create_desktop_file():
        print_error("Error creando archivo .desktop")
        sys.exit(1)
    
    # Crear configuración de autostart (Ubuntu Touch)
    if not create_autostart_config():
        print_error("Error creando configuración de autostart")
        sys.exit(1)
    
    # Crear acceso directo (Windows)
    if not create_windows_shortcut():
        print_error("Error creando acceso directo")
        sys.exit(1)
    
    # Instalación completada
    print()
    print("=" * 60)
    print_success("Instalación completada exitosamente!")
    print("=" * 60)
    print()
    
    if platform_type == "ubuntu_touch":
        print("📋 Para ejecutar UTPyApps:")
        print(f"   cd {INSTALL_DIR}")
        print("   ./utpyapps.sh")
        print()
        print("🌐 UTPyApps estará disponible en: http://localhost:8080")
        print()
        print("📱 Acceso launcher: UTPyApps ahora aparece en el launcher de Ubuntu Touch")
        print("🚀 Autostart: UTPyApps se iniciará automáticamente al arrancar el dispositivo")
    elif platform_type == "windows":
        print("📋 Para ejecutar UTPyApps:")
        print(f"   cd {INSTALL_DIR}")
        print("   bash utpyapps.sh")
        print()
        print("🌐 UTPyApps estará disponible en: http://localhost:8080")
        print()
        print("📝 Nota: En Windows necesitas Git Bash o WSL para ejecutar utpyapps.sh")
    else:
        print("📋 Para ejecutar UTPyApps:")
        print(f"   cd {INSTALL_DIR}")
        print("   ./utpyapps.sh")
        print()
        print("🌐 UTPyApps estará disponible en: http://localhost:8080")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_error("Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        sys.exit(1)
