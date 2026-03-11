import socket
import threading

HOST = "127.0.0.1"
PORT = 3333
BUFFER_SIZE = 1024

class State:
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()

    def add(self, key, value):
        with self.lock:
            self.data[key] = value
        return "OK - record add"

    def get(self, key):
        with self.lock:
            if key in self.data:
                return f"DATA {self.data[key]}"
            return "ERROR invalid key"

    def remove(self, key):
        with self.lock:
            if key in self.data:
                del self.data[key]
                return "OK value deleted"
            return "ERROR invalid key"

    def list_all(self):
        with self.lock:
            if not self.data:
                return "DATA|"
            res = "DATA|"
            for k, v in self.data.items():
                res += f"{k}={v},"
            return res[:-1]

    def count(self):
        with self.lock:
            return f"DATA {len(self.data.keys())}"

    def clear(self):
        with self.lock:
            self.data.clear()
        return "all data deleted"

    def update(self, key, value):
        with self.lock:
            if key in self.data:
                self.data[key] = value
                return "Data updated"
            return "ERROR invalid key"

    def pop(self, key):
        with self.lock:
            if key in self.data:
                val = self.data[key]
                del self.data[key]
                return f"Data {val}"
            return "ERROR invalid key"

state = State()

def process_command(command):
    parts = command.strip().split()
    if not parts:
        return "Invalid command format"

    cmd = parts[0].upper()
    
    if cmd == "ADD" and len(parts) >= 3:
        key = parts[1]
        val = " ".join(parts[2:])
        return state.add(key, val)
    
    if cmd == "GET" and len(parts) == 2:
        return state.get(parts[1])
    
    if cmd == "REMOVE" and len(parts) == 2:
        return state.remove(parts[1])
        
    if cmd == "LIST" and len(parts) == 1:
        return state.list_all()
        
    if cmd == "COUNT" and len(parts) == 1:
        return state.count()
        
    if cmd == "CLEAR" and len(parts) == 1:
        return state.clear()
        
    if cmd == "UPDATE" and len(parts) >= 3:
        key = parts[1]
        val = " ".join(parts[2:])
        return state.update(key, val)
        
    if cmd == "POP" and len(parts) == 2:
        return state.pop(parts[1])
        
    return "Invalid command"

def handle_client(client_socket):
    with client_socket:
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                command = data.decode('utf-8').strip()
                
                if command.strip().upper() == "QUIT":
                    break
                    
                response = process_command(command)
                
                response_data = f"{len(response)} {response}".encode('utf-8')
                client_socket.sendall(response_data)

            except Exception as e:
                client_socket.sendall(f"Error: {str(e)}".encode('utf-8'))
                break

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[SERVER] Listening on {HOST}:{PORT}")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"[SERVER] Connection from {addr}")
            threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()
