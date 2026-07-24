# Ollama Chat - Chat con modelos de IA usando Ollama
# Name: Ollama Chat
# Description: Chat con modelos de IA usando Ollama - Sistema de conversaciones con historial
# Author: UTPyApps
# Version: 2.0.0

from microdot import Microdot, Response
from jinja2 import Environment, FileSystemLoader
import os
import sqlite3
import json
from datetime import datetime

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

def create_conversation(title='Nueva conversación', model='mistral:latest'):
    """Crear una nueva conversación"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO conversations (title, model, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (title, model, now, now))
    
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
        
        conversation_id = create_conversation(title, model)
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
        
        # Guardar mensaje del usuario
        if conversation_id:
            save_message(conversation_id, 'user', message)
        
        # Generar respuesta
        response = ollama_service.simple_generate(message, model)
        
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

# Inicializar base de datos al iniciar
init_db()
