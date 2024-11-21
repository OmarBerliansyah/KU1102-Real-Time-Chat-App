# server.py
import socket
import threading
import logging
import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatServer:
    def __init__(self, host, port):
        """Initialize the chat server."""
        self.host = host
        self.port = port
        self.clients = []
        self.nicknames = []
        
        # Create server socket
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((host, port))
            self.server.listen()
            logger.info(f"Server running on {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise

        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        self.log_file = f"logs/chat_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    def log_message(self, message):
        """Log messages to file."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{message}\n")
        except Exception as e:
            logger.error(f"Error logging message: {e}")

    def broadcast(self, message, sender_client=None):
        """Broadcast message to all clients except sender."""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        for client in self.clients:
            if client != sender_client:
                try:
                    if isinstance(message, str):
                        client.send(f"[{timestamp}] {message}".encode('utf-8'))
                    else:
                        client.send(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    self.remove_client(client)

    def handle_file_transfer(self, sender_client, message):
        """Handle file transfer between clients."""
        try:
            # Parse file header
            header = message.decode('utf-8')
            _, filename, filesize, sender = header.split(':')
            filesize = int(filesize)
            
            # Create temp directory if not exists
            if not os.path.exists('temp_files'):
                os.makedirs('temp_files')
            
            # Save file temporarily
            temp_path = os.path.join('temp_files', filename)
            
            # Receive file data
            file_data = b''
            remaining = filesize
            while remaining > 0:
                chunk = sender_client.recv(min(8192, remaining))
                if not chunk:
                    break
                file_data += chunk
                remaining -= len(chunk)
            
            # Save file data
            with open(temp_path, 'wb') as f:
                f.write(file_data)
            
            # Broadcast file to all other clients
            for client in self.clients:
                if client != sender_client:
                    try:
                        # Send header first
                        client.send(message)
                        # Then send file data in chunks
                        with open(temp_path, 'rb') as f:
                            while True:
                                chunk = f.read(8192)
                                if not chunk:
                                    break
                                client.sendall(chunk)
                    except Exception as e:
                        logger.error(f"Error sending file to client: {e}")
                        self.remove_client(client)
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            logger.info(f"File '{filename}' ({filesize} bytes) transferred from {sender}")
            self.log_message(f"[{datetime.datetime.now()}] {sender} shared file: {filename}")
            
        except Exception as e:
            logger.error(f"Error handling file transfer: {e}")

    def handle_client(self, client, address):
        """Handle individual client connection."""
        try:
            # Request nickname
            client.send('NICK'.encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
            
            # Send two separate messages for join notification
            # 1. First send join notification to everyone else
            for other_client in self.clients:
                try:
                    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                    other_client.send(f"[{timestamp}] {nickname} joined the chat!".encode('utf-8'))
                except:
                    pass
                    
            # 2. Now add client to active lists
            self.nicknames.append(nickname)
            self.clients.append(client)
            
            # Log the join
            logger.info(f"New connection from {address}, nickname: {nickname}")
            self.log_message(f"[{datetime.datetime.now()}] {nickname} joined the chat")
            
            # Main client handling loop
            while True:
                try:
                    message = client.recv(8192)
                    if not message:
                        break
                    
                    if message.startswith(b'FILE:'):
                        self.handle_file_transfer(client, message)
                    else:
                        decoded_msg = message.decode('utf-8')
                        self.broadcast(decoded_msg, client)
                        self.log_message(decoded_msg)
                        
                except ConnectionResetError:
                    break
                except Exception as e:
                    logger.error(f"Error handling client {nickname}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            self.remove_client(client, nickname)
    
    def remove_client(self, client, nickname=None):
        """Remove client and clean up."""
        try:
            if client in self.clients:
                idx = self.clients.index(client)
                self.clients.remove(client)
                nickname = nickname or self.nicknames.pop(idx)
                client.close()
                
                # Send leave notification
                timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                for other_client in self.clients:
                    try:
                        other_client.send(f"[{timestamp}] {nickname} left the chat!".encode('utf-8'))
                    except:
                        pass
                        
                self.log_message(f"[{datetime.datetime.now()}] {nickname} left the chat")
                logger.info(f"Client {nickname} disconnected")
        except Exception as e:
            logger.error(f"Error removing client: {e}")
    
    def start(self):
        """Start the server and accept connections."""
        logger.info("Server started, waiting for connections...")
        while True:
            try:
                client, address = self.server.accept()
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client, address),
                    daemon=True
                )
                thread.start()
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
                continue

    def stop(self):
        """Stop the server gracefully."""
        logger.info("Shutting down server...")
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.server.close()

if __name__ == "__main__":
    try:
        # Get local IP address
        HOST = socket.gethostbyname(socket.gethostname())
        PORT = 8000
        
        server = ChatServer(HOST, PORT)
        logger.info(f"Chat server started on {HOST}:{PORT}")
        server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        server.stop()
    except Exception as e:
        logger.error(f"Fatal server error: {e}")