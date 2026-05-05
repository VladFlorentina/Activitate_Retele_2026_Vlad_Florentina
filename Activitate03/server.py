import socket
import json
import os
import threading

# Configuration
SERVER_HOST = 'localhost'
SERVER_PORT = 5000
FILES_DIR = 'files'
DEFAULT_USER = 'student'
DEFAULT_PASSWORD = '1234'

file_history = {}

def ensure_files_dir():
    """Ensure files directory exists"""
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)
        print(f"✓ Directory '{FILES_DIR}' created")


def authenticate(username, password):
    """Authenticate user"""
    return username == DEFAULT_USER and password == DEFAULT_PASSWORD


def handle_client(conn, addr):
    """Handle client connection"""
    print(f"\n🔗 Client connected from {addr}")
    authenticated = False
    current_user = None
    
    try:
        while True:
            # Receive request
            request_data = conn.recv(4096).decode('utf-8')
            if not request_data:
                break
            
            try:
                request = json.loads(request_data)
                command = request.get('command')
                
                print(f"📨 Command received: {command}")
                
                # Authentication
                if command == 'login':
                    username = request.get('username')
                    password = request.get('password')
                    
                    if authenticate(username, password):
                        authenticated = True
                        current_user = username
                        response = {'status': 'success', 'message': f'Welcome {username}!'}
                        print(f"✓ User {username} authenticated")
                    else:
                        response = {'status': 'error', 'message': 'Invalid credentials'}
                        print(f"✗ Authentication failed for user {username}")
                
                elif not authenticated:
                    response = {'status': 'error', 'message': 'Not authenticated. Use login first'}
                
                # File operations
                elif command == 'create_file':
                    filename = request.get('filename')
                    content = request.get('content', '')
                    
                    filepath = os.path.join(FILES_DIR, filename)
                    with open(filepath, 'w') as f:
                        f.write(content)
                    if filename not in file_history:
                        file_history[filename] = []
                    file_history[filename].append('create')
                    
                    response = {'status': 'success', 'message': f'File {filename} created on server'}
                    print(f"✓ File created: {filename}")
                
                elif command == 'upload':
                    filename = request.get('filename')
                    content = request.get('content')
                    
                    filepath = os.path.join(FILES_DIR, filename)
                    with open(filepath, 'w') as f:
                        f.write(content)
                    if filename not in file_history:
                        file_history[filename] = []
                    file_history[filename].append('upload')
                    
                    response = {'status': 'success', 'message': f'File {filename} uploaded'}
                    print(f"✓ File uploaded: {filename}")
                
                elif command == 'rename_file':
                    old_name = request.get('old_name')
                    new_name = request.get('new_name')
                    old_path = os.path.join(FILES_DIR, old_name)
                    new_path = os.path.join(FILES_DIR, new_name)
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                        if old_name in file_history:
                            file_history[new_name] = file_history.pop(old_name)
                        if new_name not in file_history:
                            file_history[new_name] = []
                        file_history[new_name].append('rename from ' + old_name + ' to ' + new_name)
                        response = {'status': 'success', 'message': f'Fisierul {old_name} a fost redenumit in {new_name}'}
                    else:
                        response = {'status': 'error', 'message': f'Fisierul {old_name} nu exista'}
                
                elif command == 'read_file':
                    filename = request.get('filename')
                    filepath = os.path.join(FILES_DIR, filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'r') as f:
                            content = f.read()
                        if filename not in file_history:
                            file_history[filename] = []
                        file_history[filename].append('read')
                        response = {'status': 'success', 'content': content}
                    else:
                        response = {'status': 'error', 'message': f'Fisierul {filename} nu exista'}
                
                elif command == 'download':
                    filename = request.get('filename')
                    filepath = os.path.join(FILES_DIR, filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'r') as f:
                            content = f.read()
                        if filename not in file_history:
                            file_history[filename] = []
                        file_history[filename].append('download')
                        response = {'status': 'success', 'filename': filename, 'content': content}
                    else:
                        response = {'status': 'error', 'message': f'Fisierul {filename} nu exista'}
                
                elif command == 'edit_file':
                    filename = request.get('filename')
                    content = request.get('content')
                    filepath = os.path.join(FILES_DIR, filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'w') as f:
                            f.write(content)
                        if filename not in file_history:
                            file_history[filename] = []
                        file_history[filename].append('edit')
                        response = {'status': 'success', 'message': f'Fisierul {filename} a fost editat'}
                    else:
                        response = {'status': 'error', 'message': f'Fisierul {filename} nu exista'}
                
                elif command == 'see_file_operation_history':
                    filename = request.get('filename')
                    if filename in file_history and len(file_history[filename]) > 0:
                        history = file_history[filename]
                        response = {'status': 'success', 'history': history}
                    else:
                        response = {'status': 'error', 'message': f'Nu exista istoric pentru {filename}'}
                
                elif command == 'list_files':
                    files = os.listdir(FILES_DIR)
                    response = {'status': 'success', 'files': files}
                    print(f"✓ Files listed: {len(files)} files found")
                
                elif command == 'logout':
                    authenticated = False
                    current_user = None
                    response = {'status': 'success', 'message': 'Logged out'}
                    print(f"✓ User logged out")
                
                else:
                    response = {'status': 'error', 'message': f'Unknown command: {command}'}
                
            except Exception as e:
                response = {'status': 'error', 'message': str(e)}
                print(f"✗ Error: {str(e)}")
            
            # Send response
            conn.send(json.dumps(response).encode('utf-8'))
    
    except Exception as e:
        print(f"✗ Connection error: {str(e)}")
    finally:
        conn.close()
        print(f"🔌 Client disconnected from {addr}")


def start_server():
    """Start FTP server"""
    ensure_files_dir()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    
    print("=" * 60)
    print("🚀 FTP SERVER STARTED")
    print("=" * 60)
    print(f"Host: {SERVER_HOST}")
    print(f"Port: {SERVER_PORT}")
    print(f"Files Directory: {FILES_DIR}")
    print(f"Default User: {DEFAULT_USER}")
    print(f"Default Password: {DEFAULT_PASSWORD}")
    print("=" * 60)
    
    try:
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\n\n⛔ Server shutting down...")
    finally:
        server_socket.close()


if __name__ == '__main__':
    start_server()
