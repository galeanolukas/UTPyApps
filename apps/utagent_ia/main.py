# UTAgent IA - Agente de IA con capacidades de chat, system prompts y tools
# Name: UTAgent IA
# Description: Agente de IA con capacidades de chat, system prompts y tools para Ubuntu Touch
# Author: UTPyApps
# Version: 1.0.0

from microdot import Microdot, Response
from jinja2 import Environment, FileSystemLoader
import os
import sqlite3
import json
import subprocess
import requests
from datetime import datetime

try:
    from ollama import Client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

app = Microdot()
Response.default_content_type = 'text/html'

# Configurar templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
app_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# Configuración de base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), 'chat.db')

# Configuración de Ollama
OLLAMA_HOST = 'localhost:11434'
if OLLAMA_AVAILABLE:
    ollama_client = Client(host=OLLAMA_HOST)

class OllamaService:
    """Servicio para comunicación con Ollama (basado en ollama_online)"""
    
    def __init__(self, base_url=None, model=None):
        self.base_url = base_url or OLLAMA_HOST
        self.model = model or 'mistral:latest'
        
        if OLLAMA_AVAILABLE:
            self.client = Client(host=self.base_url)
        else:
            self.client = None
    
    def simple_generate(self, prompt, model=None):
        """Generación simple sin streaming"""
        if not OLLAMA_AVAILABLE:
            return "Error: Librería ollama no instalada"
        
        model = model or self.model
        
        try:
            response = self.client.generate(
                model=model,
                prompt=prompt
            )
            return response.get('response', 'No response received')
        except Exception as e:
            return f"Error: {str(e)}"
    
    def stream_generate(self, prompt, model=None):
        """Generación con streaming"""
        if not OLLAMA_AVAILABLE:
            yield "Error: Librería ollama no instalada"
            return
        
        model = model or self.model
        
        try:
            for response in self.client.generate(
                model=model,
                prompt=prompt,
                stream=True
            ):
                if 'response' in response:
                    yield response['response']
                
                if response.get('done', False):
                    break
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def list_models(self):
        """Listar modelos disponibles"""
        if not OLLAMA_AVAILABLE:
            return []
        
        try:
            models = self.client.list()
            # La librería ollama devuelve un objeto con atributo 'models'
            if hasattr(models, 'models'):
                return [{'name': model.model} for model in models.models]
            elif isinstance(models, dict) and 'models' in models:
                return models['models']
            else:
                return []
        except Exception as e:
            print(f"Error listando modelos: {e}")
            return []

# Instancia global del servicio
ollama_service = OllamaService()

# --- Tools del Agente ---

class AgentTools:
    """Herramientas disponibles para el agente de IA"""
    
    @staticmethod
    def web_scrape(url):
        """Extraer contenido de una URL"""
        if not BS4_AVAILABLE:
            return "Error: BeautifulSoup no está instalado"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer texto del body
            text = soup.get_text(separator='\n', strip=True)
            
            # Limitar longitud
            if len(text) > 10000:
                text = text[:10000] + '... (truncado)'
            
            return f"Contenido extraído de {url}:\n\n{text}"
        except Exception as e:
            return f"Error scraping {url}: {str(e)}"
    
    @staticmethod
    def execute_command(command):
        """Ejecutar un comando del sistema (con restricciones)"""
        # Comandos permitidos (lista blanca)
        allowed_commands = ['ls', 'pwd', 'date', 'whoami', 'uname', 'df', 'free', 'top']
        
        command_parts = command.split()
        if not command_parts:
            return "Error: Comando vacío"
        
        base_command = command_parts[0]
        
        if base_command not in allowed_commands:
            return f"Error: Comando '{base_command}' no permitido por seguridad"
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            
            output = result.stdout if result.stdout else result.stderr
            if len(output) > 5000:
                output = output[:5000] + '... (truncado)'
            
            return output
        except subprocess.TimeoutExpired:
            return "Error: Comando excedió tiempo límite"
        except Exception as e:
            return f"Error ejecutando comando: {str(e)}"
    
    @staticmethod
    def get_system_info():
        """Obtener información del sistema"""
        try:
            info = {
                'os': subprocess.run(['uname', '-a'], capture_output=True, text=True).stdout.strip(),
                'cpu': subprocess.run(['uname', '-m'], capture_output=True, text=True).stdout.strip(),
                'memory': subprocess.run(['free', '-h'], capture_output=True, text=True).stdout.strip(),
                'disk': subprocess.run(['df', '-h', '/'], capture_output=True, text=True).stdout.strip(),
            }
            return json.dumps(info, indent=2)
        except Exception as e:
            return f"Error obteniendo info del sistema: {str(e)}"

agent_tools = AgentTools()

# --- Base de Datos ---

def init_db():
    """Inicializar base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de conversaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT 'Nueva conversación',
            model TEXT,
            system_prompt TEXT DEFAULT 'Eres un asistente útil y amigable.',
            temperature REAL DEFAULT 0.7,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Tabla de mensajes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
        )
    ''')
    
    # Tabla de system prompts predefinidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            prompt TEXT,
            is_default BOOLEAN DEFAULT 0
        )
    ''')
    
    # Insertar system prompts predefinidos si no existen
    cursor.execute('SELECT COUNT(*) FROM system_prompts')
    if cursor.fetchone()[0] == 0:
        default_prompts = [
            ('Asistente General', 'Asistente útil y amigable', 'Eres un asistente útil y amigable. Responde de manera clara y concisa.', True),
            ('Soporte Técnico', 'Especialista en soporte técnico', 'Eres un especialista en soporte técnico. Ayuda a resolver problemas técnicos de manera clara y paso a paso.', False),
            ('Programador', 'Experto en programación', 'Eres un experto en programación. Ayuda con código, debugging y mejores prácticas. Proporciona ejemplos de código cuando sea necesario.', False),
            ('Escritor', 'Asistente de escritura', 'Eres un asistente de escritura. Ayuda a redactar, editar y mejorar textos. Mantén un tono profesional y creativo.', False),
            ('Analista de Datos', 'Especialista en análisis de datos', 'Eres un especialista en análisis de datos. Ayuda a interpretar datos, crear visualizaciones y extraer insights.', False),
        ]
        
        for name, description, prompt, is_default in default_prompts:
            cursor.execute('''
                INSERT INTO system_prompts (name, description, prompt, is_default)
                VALUES (?, ?, ?, ?)
            ''', (name, description, prompt, is_default))
    
    conn.commit()
    conn.close()

def get_conversations():
    """Obtener todas las conversaciones"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, 
               (SELECT content FROM messages WHERE conversation_id = c.id ORDER BY timestamp ASC LIMIT 1) as preview
        FROM conversations c
        ORDER BY c.updated_at DESC
    ''')
    
    conversations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return conversations

def create_conversation(title='Nueva conversación', model='mistral:latest', system_prompt=None, temperature=0.7):
    """Crear una nueva conversación"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if system_prompt is None:
        # Obtener el system prompt por defecto
        cursor.execute('SELECT prompt FROM system_prompts WHERE is_default = 1 LIMIT 1')
        result = cursor.fetchone()
        system_prompt = result[0] if result else 'Eres un asistente útil y amigable.'
    
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO conversations (title, model, system_prompt, temperature, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, model, system_prompt, temperature, now, now))
    
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return conversation_id

def get_conversation(conversation_id):
    """Obtener una conversación específica"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,))
    conversation = cursor.fetchone()
    
    if conversation:
        conversation = dict(conversation)
        
        # Obtener mensajes
        cursor.execute('''
            SELECT * FROM messages 
            WHERE conversation_id = ? 
            ORDER BY timestamp ASC
        ''', (conversation_id,))
        
        conversation['messages'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return conversation

def delete_conversation(conversation_id):
    """Eliminar una conversación"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
    
    conn.commit()
    conn.close()

def save_message(conversation_id, role, content):
    """Guardar un mensaje"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO messages (conversation_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (conversation_id, role, content, now))
    
    # Actualizar timestamp de conversación
    cursor.execute('''
        UPDATE conversations SET updated_at = ? WHERE id = ?
    ''', (now, conversation_id))
    
    conn.commit()
    conn.close()

# --- Rutas ---

@app.route('/')
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
        models = ollama_service.list_models()
        return Response({
            'status': 'running',
            'models': models
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
        models = ollama_service.list_models()
        return Response({'models': models}, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({
            'error': str(e)
        }, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/conversations')
def api_conversations(request):
    """Obtener todas las conversaciones"""
    try:
        conversations = get_conversations()
        return Response({'conversations': conversations}, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({'error': str(e)}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/conversations/create', methods=['POST'])
def api_create_conversation(request):
    """Crear una nueva conversación"""
    try:
        data = request.json
        title = data.get('title', 'Nueva conversación')
        model = data.get('model', 'mistral:latest')
        system_prompt = data.get('system_prompt')
        temperature = data.get('temperature', 0.7)
        
        conversation_id = create_conversation(title, model, system_prompt, temperature)
        return Response({
            'success': True,
            'conversation_id': conversation_id
        }, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({'error': str(e)}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/conversations/<int:conversation_id>')
def api_get_conversation(request, conversation_id):
    """Obtener una conversación específica"""
    try:
        conversation = get_conversation(conversation_id)
        if conversation:
            return Response(conversation, headers={'Content-Type': 'application/json'})
        else:
            return Response({'error': 'Conversación no encontrada'}, status_code=404, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({'error': str(e)}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/conversations/<int:conversation_id>/delete', methods=['DELETE'])
def api_delete_conversation(request, conversation_id):
    """Eliminar una conversación"""
    try:
        delete_conversation(conversation_id)
        return Response({'success': True}, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({'error': str(e)}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/messages/save', methods=['POST'])
def api_save_message(request):
    """Guardar un mensaje"""
    try:
        data = request.json
        conversation_id = data.get('conversation_id')
        role = data.get('role')
        content = data.get('content')
        
        save_message(conversation_id, role, content)
        return Response({'success': True}, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({'error': str(e)}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/chat', methods=['POST'])
def api_chat(request):
    """Enviar mensaje al modelo"""
    if not OLLAMA_AVAILABLE:
        return Response({
            'error': 'Librería ollama no instalada'
        }, status_code=500, headers={'Content-Type': 'application/json'})
    
    try:
        data = request.json
        model = data.get('model', 'mistral:latest')
        message = data.get('message', '')
        conversation_id = data.get('conversation_id')
        
        # Obtener system prompt y temperature de la conversación
        system_prompt = None
        temperature = 0.7
        
        if conversation_id:
            conversation = get_conversation(conversation_id)
            if conversation:
                system_prompt = conversation.get('system_prompt')
                temperature = conversation.get('temperature', 0.7)
        
        # Guardar mensaje del usuario
        if conversation_id:
            save_message(conversation_id, 'user', message)
        
        # Construir prompt con system prompt
        full_prompt = message
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUsuario: {message}"
        
        # Generar respuesta
        response = ollama_service.simple_generate(full_prompt, model)
        
        # Guardar respuesta del bot
        if conversation_id:
            save_message(conversation_id, 'bot', response)
        
        return Response({
            'response': response,
            'model': model
        }, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({
            'error': str(e)
        }, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/system-prompts')
def api_system_prompts(request):
    """Obtener todos los system prompts"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM system_prompts ORDER BY is_default DESC, name ASC')
        prompts = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return Response({'prompts': prompts}, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({'error': str(e)}, status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/tools/execute', methods=['POST'])
def api_execute_tool(request):
    """Ejecutar una tool del agente"""
    try:
        data = request.json
        tool_name = data.get('tool')
        params = data.get('params', {})
        
        if tool_name == 'web_scrape':
            url = params.get('url')
            if not url:
                return Response({'error': 'URL requerida'}, status_code=400, headers={'Content-Type': 'application/json'})
            result = agent_tools.web_scrape(url)
        elif tool_name == 'execute_command':
            command = params.get('command')
            if not command:
                return Response({'error': 'Comando requerido'}, status_code=400, headers={'Content-Type': 'application/json'})
            result = agent_tools.execute_command(command)
        elif tool_name == 'get_system_info':
            result = agent_tools.get_system_info()
        else:
            return Response({'error': 'Tool no encontrada'}, status_code=400, headers={'Content-Type': 'application/json'})
        
        return Response({
            'success': True,
            'result': result
        }, headers={'Content-Type': 'application/json'})
    except Exception as e:
        return Response({'error': str(e)}, status_code=500, headers={'Content-Type': 'application/json'})

# Inicializar base de datos al iniciar
init_db()
