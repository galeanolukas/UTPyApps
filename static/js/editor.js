// UTPyApps Code Editor - CodeMirror 6 Integration
// Ubuntu Touch Theme and Configuration

class UTPyApps_Editor {
    constructor() {
        this.currentFile = null;
        this.currentApp = null;
        this.editor = null;
        this.autoSaveInterval = null;
        this.files = [];
    }

    // Initialize editor with enhanced textarea
    initEditor(container, content = '', language = 'python') {
        // Clear container
        container.innerHTML = '';

        // Create editor container with line numbers
        const editorContainer = document.createElement('div');
        editorContainer.style.display = 'flex';
        editorContainer.style.width = '100%';
        editorContainer.style.height = '100%';
        editorContainer.style.backgroundColor = '#2c001e';
        editorContainer.style.border = 'none';
        editorContainer.style.outline = 'none';

        // Create line numbers
        const lineNumbers = document.createElement('div');
        lineNumbers.style.width = '40px';
        lineNumbers.style.backgroundColor = '#1a0012';
        lineNumbers.style.color = '#666';
        lineNumbers.style.fontFamily = 'monospace';
        lineNumbers.style.fontSize = '14px';
        lineNumbers.style.lineHeight = '1.5';
        lineNumbers.style.padding = '10px 5px';
        lineNumbers.style.textAlign = 'right';
        lineNumbers.style.overflow = 'hidden';
        lineNumbers.style.userSelect = 'none';
        lineNumbers.style.borderRight = '1px solid #444';

        // Create textarea
        const textarea = document.createElement('textarea');
        textarea.style.flex = '1';
        textarea.style.border = 'none';
        textarea.style.outline = 'none';
        textarea.style.backgroundColor = 'transparent';
        textarea.style.color = '#ffffff';
        textarea.style.fontFamily = 'monospace';
        textarea.style.fontSize = '14px';
        textarea.style.lineHeight = '1.5';
        textarea.style.padding = '10px';
        textarea.style.resize = 'none';
        textarea.value = content;
        textarea.style.overflow = 'auto';

        // Store textarea as editor
        this.editor = textarea;
        this.editor.contentDOM = textarea;
        this.editor.lineNumbers = lineNumbers;

        // Add to editor container
        editorContainer.appendChild(lineNumbers);
        editorContainer.appendChild(textarea);

        // Add to main container
        container.appendChild(editorContainer);

        // Update line numbers
        this.updateLineNumbers();

        // Setup content change handler
        textarea.addEventListener('input', () => {
            this.handleContentChange(textarea.value);
            this.updateLineNumbers();
        });

        // Setup scroll sync
        textarea.addEventListener('scroll', () => {
            lineNumbers.scrollTop = textarea.scrollTop;
        });

        // Setup auto-save
        this.setupAutoSave();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    // Update line numbers
    updateLineNumbers() {
        if (!this.editor || !this.editor.lineNumbers) return;
        
        const content = this.editor.value;
        const lines = content.split('\n');
        const lineNumbersHtml = lines.map((_, index) => index + 1).join('<br>');
        this.editor.lineNumbers.innerHTML = lineNumbersHtml;
    }

    // Apply syntax highlighting for different languages
    applySyntaxHighlighting(language) {
        if (!this.editor) return;

        const content = this.editor.value;
        
        // Apply highlighting based on language
        let highlightedText = content;
        
        if (language === 'python') {
            highlightedText = this.highlightPython(content);
        } else if (language === 'html') {
            highlightedText = this.highlightHTML(content);
        } else if (language === 'javascript' || language === 'js') {
            highlightedText = this.highlightJavaScript(content);
        } else if (language === 'json') {
            highlightedText = this.highlightJSON(content);
        }
        
        // For now, we'll keep simple text without complex highlighting
        // In a future version, we could implement proper syntax highlighting
    }

    // Python syntax highlighting
    highlightPython(text) {
        const keywords = ['and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield'];
        const builtins = ['print', 'len', 'str', 'int', 'float', 'list', 'dict', 'tuple', 'set', 'range', 'enumerate', 'zip', 'map', 'filter', 'sum', 'min', 'max', 'abs', 'round'];
        
        let highlighted = text;
        
        // Highlight keywords
        keywords.forEach(keyword => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'g');
            highlighted = highlighted.replace(regex, `<span class="cm-keyword">${keyword}</span>`);
        });
        
        // Highlight builtins
        builtins.forEach(builtin => {
            const regex = new RegExp(`\\b${builtin}\\b`, 'g');
            highlighted = highlighted.replace(regex, `<span class="cm-builtin">${builtin}</span>`);
        });
        
        // Highlight strings
        highlighted = highlighted.replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="cm-string">$&</span>');
        
        // Highlight comments
        highlighted = highlighted.replace(/(#.*$)/gm, '<span class="cm-comment">$1</span>');
        
        // Highlight numbers
        highlighted = highlighted.replace(/\b(\d+)\b/g, '<span class="cm-number">$1</span>');
        
        return highlighted;
    }

    // HTML syntax highlighting
    highlightHTML(text) {
        let highlighted = text;
        
        // Highlight tags
        highlighted = highlighted.replace(/(&lt;\/?)([a-zA-Z][a-zA-Z0-9]*)(.*?)(&gt;)/g, '<span class="cm-tag">$1$2$3$4</span>');
        
        // Highlight attributes
        highlighted = highlighted.replace(/([a-zA-Z-]+)(=)(["'])(.*?)\3/g, '<span class="cm-attribute">$1</span>$2<span class="cm-string">$3$4$3</span>');
        
        return highlighted;
    }

    // JavaScript syntax highlighting
    highlightJavaScript(text) {
        const keywords = ['break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 'default', 'delete', 'do', 'else', 'export', 'extends', 'finally', 'for', 'function', 'if', 'import', 'in', 'instanceof', 'let', 'new', 'return', 'super', 'switch', 'this', 'throw', 'try', 'typeof', 'var', 'void', 'while', 'with', 'yield'];
        
        let highlighted = text;
        
        // Highlight keywords
        keywords.forEach(keyword => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'g');
            highlighted = highlighted.replace(regex, `<span class="cm-keyword">${keyword}</span>`);
        });
        
        // Highlight strings
        highlighted = highlighted.replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="cm-string">$&</span>');
        
        // Highlight comments
        highlighted = highlighted.replace(/(\/\/.*$)/gm, '<span class="cm-comment">$1</span>');
        highlighted = highlighted.replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="cm-comment">$1</span>');
        
        // Highlight numbers
        highlighted = highlighted.replace(/\b(\d+)\b/g, '<span class="cm-number">$1</span>');
        
        return highlighted;
    }

    // JSON syntax highlighting
    highlightJSON(text) {
        let highlighted = text;
        
        try {
            const json = JSON.parse(text);
            highlighted = JSON.stringify(json, null, 2);
            
            // Highlight strings
            highlighted = highlighted.replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="cm-string">$&</span>');
            
            // Highlight numbers
            highlighted = highlighted.replace(/\b(\d+\.?\d*)\b/g, '<span class="cm-number">$1</span>');
            
            // Highlight booleans and null
            highlighted = highlighted.replace(/\b(true|false|null)\b/g, '<span class="cm-keyword">$1</span>');
            
        } catch (e) {
            // If invalid JSON, just return original text
        }
        
        return highlighted;
    }

    // Get language from file extension
    getLanguageFromExtension(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        
        switch (extension) {
            case 'py':
                return 'python';
            case 'js':
            case 'mjs':
                return 'javascript';
            case 'html':
            case 'htm':
                return 'html';
            case 'css':
                return 'css';
            case 'json':
                return 'json';
            case 'xml':
                return 'xml';
            case 'sql':
                return 'sql';
            case 'md':
            case 'markdown':
                return 'markdown';
            case 'sh':
            case 'bash':
                return 'bash';
            case 'ts':
                return 'typescript';
            case 'jsx':
                return 'jsx';
            case 'tsx':
                return 'tsx';
            case 'vue':
                return 'vue';
            case 'php':
                return 'php';
            case 'rb':
                return 'ruby';
            case 'go':
                return 'go';
            case 'rs':
                return 'rust';
            case 'java':
                return 'java';
            case 'c':
            case 'h':
                return 'c';
            case 'cpp':
            case 'cxx':
            case 'cc':
                return 'cpp';
            case 'cs':
                return 'csharp';
            default:
                return 'text';
        }
    }

    // Handle content change
    handleContentChange(content) {
        if (this.currentFile && this.currentApp) {
            // Update save status
            this.updateSaveStatus('modified');
            
            // Apply syntax highlighting
            const language = this.getLanguageFromFilename(this.currentFile);
            this.applySyntaxHighlighting(language);
        }
    }

    // Get language from filename
    getLanguageFromFilename(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'py': return 'python';
            case 'html': return 'html';
            case 'js': return 'javascript';
            case 'json': return 'json';
            case 'css': return 'css';
            default: return 'text';
        }
    }

    // Setup auto-save (COMPLETELY DISABLED)
    setupAutoSave() {
        // Auto-save completely disabled to prevent any file corruption
        // Users must manually save with Ctrl+S or save button
        console.log('Auto-save completely disabled - use Ctrl+S or save button to save manually');
        // Clear any existing interval
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
    }

    // Setup keyboard shortcuts
    setupKeyboardShortcuts() {
        if (!this.editor) return;
        
        const content = this.editor.contentDOM;
        
        content.addEventListener('keydown', (e) => {
            // Ctrl+S or Cmd+S to save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.saveFile();
            }
            
            // Ctrl+O or Cmd+O to open file
            if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
                e.preventDefault();
                this.showFileExplorer();
            }
            
            // Tab key for indentation
            if (e.key === 'Tab') {
                e.preventDefault();
                document.execCommand('insertText', false, '    ');
            }
        });
    }

    // Load file content
    async loadFile(appName, filename) {
        try {
            console.log(`Loading file: ${appName}/${filename}`);
            
            this.currentApp = appName;
            this.currentFile = filename;
            
            // Check if file is an image
            if (this.isImageFile(filename)) {
                // Show image preview - filename already includes relative path (e.g., "static/icon.png")
                const imageUrl = `/_app/${appName}/${filename}`;
                this.showImagePreview(imageUrl, filename);
                
                // Update UI
                this.updateFileInfo(appName, filename);
                this.updateSaveStatus('saved');
                
                return true;
            }
            
            // Load text file content
            const response = await fetch(`/api/editor/${appName}/file?filename=${encodeURIComponent(filename)}`);
            if (response.ok) {
                const content = await response.text();
                console.log(`File content length: ${content.length} chars`);
                console.log(`File content preview: ${content.substring(0, 100)}...`);
                
                // Update editor content
                const language = this.getLanguageFromExtension(filename);
                this.initEditor(document.getElementById('editor'), content, language);
                
                // Update UI
                this.updateFileInfo(appName, filename);
                this.updateSaveStatus('saved');
                
                return true;
            } else {
                console.error(`Failed to load file: ${response.status}`);
            }
        } catch (error) {
            console.error('Error loading file:', error);
            this.showMessage('Error loading file: ' + error.message, 'error');
        }
        return false;
    }

    // Show image preview
    showImagePreview(imageUrl, filename) {
        const editorContainer = document.getElementById('editor');
        if (!editorContainer) return;
        
        editorContainer.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 20px; background: #1a0012;">
                <div style="max-width: 100%; max-height: 80vh; overflow: auto; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                    <img src="${imageUrl}" alt="${filename}" style="max-width: 100%; max-height: 70vh; display: block; border-radius: 4px;" onerror="this.style.display='none'; this.parentElement.innerHTML='<p style=\\'color: #e74c3c; text-align: center; padding: 20px;\\'>Error cargando imagen</p>'">
                </div>
                <div style="margin-top: 20px; text-align: center;">
                    <p style="color: #888; font-size: 14px; margin: 0;">${filename}</p>
                    <p style="color: #666; font-size: 12px; margin: 5px 0 0 0;">Vista previa de imagen</p>
                    <a href="${imageUrl}" target="_blank" style="color: #E95420; text-decoration: none; font-size: 13px; margin-top: 10px; display: inline-block;">Abrir en nueva pestaña</a>
                </div>
            </div>
        `;
    }

    // Save file content
    async saveFile() {
        if (!this.currentFile || !this.currentApp || !this.editor) {
            return false;
        }
        
        try {
            const content = this.editor.value;
            const response = await fetch(`/api/editor/${this.currentApp}/file?filename=${encodeURIComponent(this.currentFile)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: content })
            });
            
            if (response.ok) {
                this.updateSaveStatus('saved');
                this.showMessage('File saved successfully', 'success');
                return true;
            } else {
                console.error('Failed to save file:', response.status);
                this.showMessage('Failed to save file', 'error');
            }
        } catch (error) {
            console.error('Error saving file:', error);
            this.showMessage('Error saving file: ' + error.message, 'error');
        }
        return false;
    }

    // Load files for app
    async loadFiles(appName) {
        try {
            this.currentApp = appName;
            const response = await fetch(`/api/editor/${appName}/files`);
            if (response.ok) {
                this.files = await response.json();
                this.updateFileExplorer();
                return true;
            }
        } catch (error) {
            console.error('Error loading files:', error);
            this.showMessage('Error loading files: ' + error.message, 'error');
        }
        return false;
    }

    // Update file explorer UI
    updateFileExplorer() {
        const fileExplorer = document.getElementById('file-explorer');
        if (!fileExplorer) return;
        
        fileExplorer.innerHTML = '';
        
        this.files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <span class="file-icon ${this.getFileIconClass(file.name)}"></span>
                <span class="file-name">${file.name}</span>
            `;
            
            fileItem.addEventListener('click', () => {
                this.loadFile(this.currentApp, file.name);
            });
            
            fileExplorer.appendChild(fileItem);
        });
    }

    // Get file icon class
    getFileIconClass(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'py': return 'icon-python';
            case 'html': return 'icon-html';
            case 'js': return 'icon-javascript';
            case 'json': return 'icon-json';
            case 'css': return 'icon-css';
            case 'png':
            case 'jpg':
            case 'jpeg':
            case 'gif':
            case 'svg':
            case 'webp':
            case 'bmp':
            case 'ico':
                return 'icon-image';
            default: return 'icon-file';
        }
    }

    // Check if file is an image
    isImageFile(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp', 'ico'];
        return imageExtensions.includes(ext);
    }

    // Update file info UI
    updateFileInfo(appName, filename) {
        const fileInfo = document.getElementById('file-info');
        if (fileInfo) {
            fileInfo.innerHTML = `${appName} / ${filename}`;
        }
    }

    // Update save status UI
    updateSaveStatus(status) {
        const saveStatus = document.getElementById('save-status');
        if (saveStatus) {
            saveStatus.className = `save-status ${status}`;
            saveStatus.textContent = status === 'saved' ? 'Saved' : status === 'modified' ? 'Modified' : 'Error';
        }
    }

    // Show/hide file explorer
    showFileExplorer() {
        const explorer = document.getElementById('file-explorer-container');
        if (explorer) {
            explorer.style.display = explorer.style.display === 'none' ? 'block' : 'none';
        }
    }

    // Create new file
    async createNewFile() {
        const filename = prompt('Nombre del nuevo archivo (ej: nuevo_archivo.py):');
        if (!filename) return;
        
        try {
            const response = await fetch(`/api/editor/${this.currentApp}/file?filename=${encodeURIComponent(filename)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: '' })
            });
            
            if (response.ok) {
                this.showMessage(`Archivo ${filename} creado correctamente`, 'success');
                // Reload files list
                await this.loadFiles(this.currentApp);
                // Load the new file
                await this.loadFile(this.currentApp, filename);
            } else {
                const error = await response.json();
                this.showMessage(`Error creando archivo: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Error creating file:', error);
            this.showMessage('Error creando archivo: ' + error.message, 'error');
        }
    }

    // Delete current file
    async deleteCurrentFile() {
        if (!this.currentFile) {
            this.showMessage('No hay archivo seleccionado', 'error');
            return;
        }
        
        if (!confirm(`¿Estás seguro de eliminar ${this.currentFile}?`)) return;
        
        try {
            const response = await fetch(`/api/editor/${this.currentApp}/file?filename=${encodeURIComponent(this.currentFile)}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showMessage(`Archivo ${this.currentFile} eliminado correctamente`, 'success');
                // Clear editor
                if (this.editor) {
                    this.editor.value = '';
                    this.updateLineNumbers();
                }
                this.currentFile = null;
                // Reload files list
                await this.loadFiles(this.currentApp);
            } else {
                const error = await response.json();
                this.showMessage(`Error eliminando archivo: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting file:', error);
            this.showMessage('Error eliminando archivo: ' + error.message, 'error');
        }
    }

    // Show message
    showMessage(message, type = 'info') {
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            border-radius: 4px;
            z-index: 10000;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

    // Destroy editor
    destroy() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        
        if (this.editor) {
            this.editor.destroy();
        }
    }
}

// Global editor instance
let editor;

// Initialize editor when page loads
document.addEventListener('DOMContentLoaded', () => {
    editor = new UTPyApps_Editor();
    
    // Get app name from URL
    const pathParts = window.location.pathname.split('/');
    const appName = pathParts[pathParts.length - 1];
    
    if (appName && appName !== 'editor') {
        // Load files for the app
        editor.loadFiles(appName);
        
        // Load first file by default
        setTimeout(() => {
            const firstFile = document.querySelector('.file-item');
            if (firstFile) {
                firstFile.click();
            }
        }, 500);
    }
});
