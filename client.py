import socket
import threading
import customtkinter
import tkinter
from tkinter import filedialog, simpledialog, ttk, messagebox
import sys
import datetime
import os


class ServerSelectionDialog:
    def __init__(self):
        self.window = customtkinter.CTk()
        self.window.title("Select Server")
        self.window.geometry("400x300")
        self.selected_ip = None
        
        # Center the window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 300) // 2
        self.window.geometry(f"400x300+{x}+{y}")
        
        # Create main frame
        self.frame = customtkinter.CTkFrame(self.window)
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add label
        self.label = customtkinter.CTkLabel(
            self.frame,
            text="Select Server IP or Enter Manually:",
            font=("Helvetica", 12)
        )
        self.label.pack(pady=10)
        
        # Create IP listbox
        self.ip_list = ttk.Treeview(
            self.frame,
            columns=("IP", "Type"),
            show="headings",
            height=6
        )
        self.ip_list.heading("IP", text="IP Address")
        self.ip_list.heading("Type", text="Type")
        self.ip_list.pack(pady=10, fill="both", expand=True)
        
        # Add manual IP entry
        self.manual_frame = customtkinter.CTkFrame(self.frame)
        self.manual_frame.pack(fill="x", pady=10)
        
        self.ip_entry = customtkinter.CTkEntry(
            self.manual_frame,
            placeholder_text="Enter IP manually..."
        )
        self.ip_entry.pack(side="left", expand=True, padx=(0, 10))
        
        self.port_entry = customtkinter.CTkEntry(
            self.manual_frame,
            placeholder_text="Port (default: 8000)",
            width=100
        )
        self.port_entry.pack(side="right")
        
        # Add Refresh button
        self.refresh_button = customtkinter.CTkButton(
            self.frame,
            text="Refresh IPs",
            command=self.populate_ips
        )
        self.refresh_button.pack(pady=5)
        
        # Add Connect button
        self.connect_button = customtkinter.CTkButton(
            self.frame,
            text="Connect",
            command=self.on_connect
        )
        self.connect_button.pack(pady=5)
        
        # Populate IPs
        self.populate_ips()
        
        # Bind double-click on IP list
        self.ip_list.bind('<Double-1>', lambda e: self.on_connect())
        
    def get_available_ips(self):
        ips = []
        try:
            # Get hostname
            hostname = socket.gethostname()
            
            # Get local IP
            local_ip = socket.gethostbyname(hostname)
            if local_ip and not local_ip.startswith('127.'):
                ips.append((local_ip, "Local IP"))
            
            # Add localhost
            ips.append(('127.0.0.1', "Localhost"))
            
            # Try to get additional IPs
            try:
                host_info = socket.getaddrinfo(
                    hostname, 
                    None, 
                    socket.AF_INET,
                    socket.SOCK_DGRAM, 
                    socket.IPPROTO_IP
                )
                for ip in set(item[4][0] for item in host_info):
                    if ip not in [addr[0] for addr in ips]:
                        ips.append((ip, "Network IP"))
            except:
                pass
                
        except Exception as e:
            print(f"Error getting IPs: {e}")
            ips.append(('127.0.0.1', "Localhost"))
            
        return ips

    def populate_ips(self):
        for item in self.ip_list.get_children():
            self.ip_list.delete(item)
        
        for ip, ip_type in self.get_available_ips():
            self.ip_list.insert('', 'end', values=(ip, ip_type))

    def on_connect(self):
        selection = self.ip_list.selection()
        if selection:
            ip = self.ip_list.item(selection[0])['values'][0]
        else:
            ip = self.ip_entry.get().strip()
            if not ip:
                ip = '127.0.0.1'
        
        port = self.port_entry.get().strip()
        try:
            port = int(port) if port else 8000
        except ValueError:
            port = 8000
        
        self.selected_ip = (ip, port)
        self.window.quit()
        
    def get_server_info(self):
        self.window.mainloop()
        self.window.destroy()
        return self.selected_ip

class LoadingScreen:
    def __init__(self):
        self.window = customtkinter.CTk()
        self.window.title("Connecting...")
        self.window.geometry("300x150")
        self.window.attributes('-topmost', True)
        
        # Center the window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 150) // 2
        self.window.geometry(f"300x150+{x}+{y}")
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.window, 
            orient="horizontal",
            length=200, 
            mode="indeterminate"
        )
        self.progress.pack(pady=30)
        
        # Loading text
        self.label = customtkinter.CTkLabel(
            self.window,
            text="Connecting to server...",
            font=("Helvetica", 12)
        )
        self.label.pack(pady=10)
        
        self.progress.start()
        
    def destroy(self):
        self.progress.stop()
        self.window.destroy()

class Client:
    def __init__(self, host, port):
        # Get nickname first before connecting
        self.nickname = None
        self.prompt_nickname()
        if not self.nickname:
            sys.exit(0)

        # Then show loading screen
        self.loading_screen = LoadingScreen()
        self.loading_screen.window.update()
        
        # Initialize socket connection
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
        except Exception as e:
            self.loading_screen.label.configure(text="Connection failed!")
            self.loading_screen.window.after(2000, self.loading_screen.destroy)
            raise e

        # Initialize other variables
        self.gui_done = False
        self.running = True
        self.history_file = "chat_history.txt"
        
        # Start receive thread
        receive_thread = threading.Thread(target=self.receive, daemon=True)
        receive_thread.start()
        
        # Close loading screen and start GUI
        self.loading_screen.destroy()
        self.gui_loop()

    def gui_loop(self):
        self.win = customtkinter.CTk()
        self.win.title(f"Chat Application - {self.nickname}")
        
        # Set initial window size to 80% of screen size instead of fullscreen
        screen_width = self.win.winfo_screenwidth()
        screen_height = self.win.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.win.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Add maximize/fullscreen button
        self.main_frame = customtkinter.CTkFrame(self.win)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with exit and maximize buttons
        self.header = customtkinter.CTkFrame(self.main_frame)
        self.header.pack(fill="x", pady=(0, 10))
        
        self.title_label = customtkinter.CTkLabel(
            self.header,
            text="Chat Room",
            font=("Helvetica", 24, "bold")
        )
        self.title_label.pack(side="left", padx=10)
        
        # Button frame for window controls
        self.window_controls = customtkinter.CTkFrame(self.header)
        self.window_controls.pack(side="right")
        
        self.maximize_button = customtkinter.CTkButton(
            self.window_controls,
            text="🗖",  # Unicode maximize symbol
            width=40,
            command=self.toggle_fullscreen
        )
        self.maximize_button.pack(side="left", padx=5)
        
        self.exit_button = customtkinter.CTkButton(
            self.window_controls,
            text="✕",  # Unicode close symbol
            command=self.stop,
            width=40
        )
        self.exit_button.pack(side="left", padx=5)
        
        # Chat area with bubble styling
        self.text_area = tkinter.Text(
            self.main_frame,
            font=("Helvetica", 12),
            wrap="word",
            bg="#ECE5DD",  # WhatsApp-like background color
            fg="#000000",
            insertbackground="#000000",
            padx=10,
            pady=10
        )
        self.text_area.pack(fill="both", expand=True, pady=(0, 10))
        self.text_area.configure(state="disabled")
        
        # Configure tags for message bubbles and formatting
        self.text_area.tag_configure('bubble_self', 
            background='#DCF8C6',  # Light green for own messages
            lmargin1=50,
            lmargin2=50,
            rmargin=20,
            spacing1=5,
            spacing3=5
        )
        self.text_area.tag_configure('bubble_other', 
            background='#FFFFFF',  # White for others' messages
            lmargin1=20,
            lmargin2=20,
            rmargin=50,
            spacing1=5,
            spacing3=5
        )
        self.text_area.tag_configure('bold', font=("Helvetica", 12, "bold"))
        self.text_area.tag_configure('italic', font=("Helvetica", 12, "italic"))
        self.text_area.tag_configure('underline', underline=True)
        
        # Bottom frame for input and buttons
        self.bottom_frame = customtkinter.CTkFrame(self.main_frame)
        self.bottom_frame.pack(fill="x")
        
        # Input area
        self.input_area = customtkinter.CTkTextbox(
            self.bottom_frame,
            height=100,
            font=("Helvetica", 12),
            wrap="word"
        )
        self.input_area.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Buttons frame
        self.buttons_frame = customtkinter.CTkFrame(self.bottom_frame)
        self.buttons_frame.pack(side="right")
        
        # Format buttons
        self.bold_button = customtkinter.CTkButton(
            self.buttons_frame,
            text="B",
            width=40,
            command=lambda: self.format_text("bold")
        )
        self.bold_button.pack(pady=2)
        
        self.italic_button = customtkinter.CTkButton(
            self.buttons_frame,
            text="I",
            width=40,
            command=lambda: self.format_text("italic")
        )
        self.italic_button.pack(pady=2)
        
        self.underline_button = customtkinter.CTkButton(
            self.buttons_frame,
            text="U",
            width=40,
            command=lambda: self.format_text("underline")
        )
        self.underline_button.pack(pady=2)
        
        self.file_button = customtkinter.CTkButton(
            self.buttons_frame,
            text="📎",
            width=40,
            command=self.send_file
        )
        self.file_button.pack(pady=2)
        
        self.send_button = customtkinter.CTkButton(
            self.buttons_frame,
            text="Send",
            width=40,
            command=self.write
        )

        self.clear_history_button = customtkinter.CTkButton(
        self.buttons_frame,
        text="🗑️",
        width=40,
        command=self.clear_chat_history)

        self.clear_history_button.pack(pady=2)
        self.send_button.pack(pady=2)
        
        # Fullscreen state
        self.is_fullscreen = False
        
        # Bind keyboard shortcuts
        self.win.bind('<Control-b>', lambda e: self.format_text("bold"))
        self.win.bind('<Control-i>', lambda e: self.format_text("italic"))
        self.win.bind('<Control-u>', lambda e: self.format_text("underline"))
        self.win.bind('<Control-Return>', lambda e: self.write())
        self.win.bind('<F11>', lambda e: self.toggle_fullscreen())
        
        self.gui_done = True
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.load_chat_history()
        self.win.mainloop()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        self.win.attributes('-fullscreen', self.is_fullscreen)
        self.maximize_button.configure(text="🗗" if self.is_fullscreen else "🗖")

    def prompt_nickname(self):
        prompt = customtkinter.CTk()
        prompt.withdraw()
        while not self.nickname:
            self.nickname = simpledialog.askstring("Nickname", "Please choose a nickname", parent=prompt)
            if not self.nickname:
                if not simpledialog.askretrycancel("Error", "Nickname cannot be empty!", parent=prompt):
                    sys.exit(0)
        prompt.destroy()

    def format_text(self, style):
        try:
            selection = self.input_area.get("sel.first", "sel.last")
            if selection:
                if style == "bold":
                    formatted = f"**{selection}**"
                elif style == "italic":
                    formatted = f"*{selection}*"
                elif style == "underline":
                    formatted = f"_{selection}_"
                self.input_area.delete("sel.first", "sel.last")
                self.input_area.insert("insert", formatted)
        except:
            pass

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                file_size = os.path.getsize(file_path)
                filename = os.path.basename(file_path)
                
                # Add file size limit (e.g., 100MB)
                if file_size > 100 * 1024 * 1024:  # 100MB
                    messagebox.showerror("Error", "File is too large. Maximum size is 100MB.")
                    return
                    
                # Send file header with error handling
                try:
                    header = f"FILE:{filename}:{file_size}:{self.nickname}"
                    self.sock.send(header.encode('utf-8'))
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to initiate file transfer: {str(e)}")
                    return
                
                # Create progress dialog
                progress_window = customtkinter.CTkToplevel()
                progress_window.title("Sending File")
                progress_window.geometry("300x150")
                
                try:
                    # Center progress window
                    screen_width = progress_window.winfo_screenwidth()
                    screen_height = progress_window.winfo_screenheight()
                    x = (screen_width - 300) // 2
                    y = (screen_height - 150) // 2
                    progress_window.geometry(f"300x150+{x}+{y}")
                    
                    progress_label = customtkinter.CTkLabel(
                        progress_window,
                        text=f"Sending {filename}..."
                    )
                    progress_label.pack(pady=10)
                    
                    progress_bar = ttk.Progressbar(
                        progress_window,
                        length=200,
                        mode='determinate'
                    )
                    progress_bar.pack(pady=10)
                    
                    # Send file data in chunks with timeout
                    sent = 0
                    with open(file_path, 'rb') as f:
                        while sent < file_size:
                            chunk = f.read(min(8192, file_size - sent))
                            if not chunk:
                                break
                            try:
                                self.sock.settimeout(10)  # 10 second timeout
                                self.sock.sendall(chunk)
                                self.sock.settimeout(None)  # Reset timeout
                                sent += len(chunk)
                                progress = (sent / file_size) * 100
                                progress_bar['value'] = progress
                                progress_window.update()
                            except socket.timeout:
                                raise Exception("Connection timed out while sending file")
                            except Exception as e:
                                raise Exception(f"Failed to send file chunk: {str(e)}")
                    
                    self.log_message(f"You shared file: {filename}")
                    
                finally:
                    progress_window.destroy()
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send file: {str(e)}")
                self.log_message(f"Error sending file: {str(e)}")
                # Reconnect socket if necessary
                try:
                    self.sock.settimeout(None)
                except:
                    pass

    def write(self):
        message = self.input_area.get("1.0", "end-1c").strip()
        if message:
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            # Format pesan yang akan dikirim ke server
            server_message = f"{self.nickname}: {message}"
            self.sock.send(server_message.encode('utf-8'))
            # Tampilkan pesan di layar pengirim
            self.log_message(f"[{timestamp}] {server_message}")
            self.input_area.delete("1.0", "end")
            # Simpan ke history
            self.save_to_history(f"[{timestamp}] {server_message}")

    def load_chat_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = f.read()
                    if history:
                        self.text_area.configure(state='normal')
                        self.text_area.insert('end', history)
                        self.text_area.configure(state='disabled')
                        self.text_area.see('end')
        except Exception as e:
            self.log_message(f"Error loading chat history: {str(e)}")

    def save_to_history(self, message):
        try:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except Exception as e:
            self.log_message(f"Error saving to history: {str(e)}")
    
    def clear_chat_history(self):
        """Clear chat history file and current display"""
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            if self.gui_done:
                self.text_area.configure(state='normal')
                self.text_area.delete('1.0', 'end')
                self.text_area.configure(state='disabled')
        except Exception as e:
            self.log_message(f"Error clearing chat history: {str(e)}")

    def save_to_history(self, message):
        """Only save important messages to reduce history size"""
        try:
            # Skip saving certain types of messages
            if any(skip in message.lower() for skip in [
                "joined the chat",
                "left the chat",
                "error:",
                "failed to",
                "could not"
            ]):
                return
                
            # Limit history file size
            if os.path.exists(self.history_file):
                if os.path.getsize(self.history_file) > 1024 * 1024:  # 1MB limit
                    # Keep only the last 1000 lines
                    with open(self.history_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-1000:]
                    with open(self.history_file, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
            
            # Append new message
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except Exception as e:
            print(f"Error saving to history: {str(e)}")

    def log_message(self, message):
        """Enhanced message display with notifications and regular messages"""
        if self.gui_done:
            try:
                self.text_area.configure(state='normal')
                
                # Skip NICK messages
                if message.strip() == 'NICK':
                    return

                # Set up notification style
                self.text_area.tag_configure('notification', 
                    justify='center',
                    spacing1=10,
                    spacing3=10,
                    foreground='#666666',
                    background='#E8E8E8',
                )

                # Split join message and first message
                if "joined the chat!" in message and ":" in message:
                    parts = message.split("]", 1)
                    if len(parts) > 1:
                        timestamp = parts[0].strip('[')
                        content = parts[1].strip()
                        
                        # Split into join notification and first message
                        name_and_message = content.split(":", 1)
                        name = name_and_message[0].split("joined")[0].strip()
                        
                        # Display join notification
                        self.text_area.insert('end', '\n')
                        self.text_area.insert('end', f"{name} joined the chat!\n", 'notification')
                        
                        # Display first message if exists
                        if len(name_and_message) > 1:
                            first_message = name_and_message[1].strip()
                            if first_message and "joined the chat!" not in first_message:
                                self.text_area.insert('end', f"\n[{timestamp}] {name}: {first_message}\n", 'bubble_other')
                    return

                # Handle regular join/leave notifications
                if "joined the chat!" in message or "left the chat!" in message:
                    parts = message.split("]", 1)
                    if len(parts) > 1:
                        content = parts[1].strip()
                        name = content.split("joined" if "joined" in content else "left")[0].strip()
                        action = "joined the chat!" if "joined" in content else "left the chat!"
                        self.text_area.insert('end', '\n')
                        self.text_area.insert('end', f"{name} {action}\n", 'notification')
                    return
                    
                # Handle regular messages
                is_self_message = f"{self.nickname}:" in message
                bubble_tag = 'bubble_self' if is_self_message else 'bubble_other'
                
                if '**' in message or '*' in message or '_' in message:
                    self.text_area.insert('end', '\n')
                    parts = message.split('**')
                    is_bold = False
                    for part in parts:
                        italic_parts = part.split('*')
                        is_italic = False
                        for ip in italic_parts:
                            underline_parts = ip.split('_')
                            is_underline = False
                            for up in underline_parts:
                                tags = [bubble_tag]
                                if is_bold: tags.append('bold')
                                if is_italic: tags.append('italic')
                                if is_underline: tags.append('underline')
                                
                                self.text_area.insert('end', up, ' '.join(tags) if tags else bubble_tag)
                                is_underline = not is_underline
                            is_italic = not is_italic
                        is_bold = not is_bold
                    self.text_area.insert('end', '\n')
                else:
                    self.text_area.insert('end', f'\n{message}\n', bubble_tag)
                
                self.text_area.see('end')
                self.text_area.configure(state='disabled')
            except Exception as e:
                print(f"Error displaying message: {e}")

    def handle_file_receive(self, header):
            try:
                _, filename, filesize, sender = header.split(':')
                filesize = int(filesize)
                
                # Check file size
                if filesize > 100 * 1024 * 1024:  # 100MB
                    messagebox.showerror("Error", "File is too large. Maximum size is 100MB.")
                    self._consume_file_data(filesize)
                    return
                    
                save_path = filedialog.asksaveasfilename(
                    defaultextension=os.path.splitext(filename)[1],
                    initialfile=filename,
                    title=f"Save file from {sender}"
                )
                
                if not save_path:
                    self._consume_file_data(filesize)
                    return
                    
                progress_window = None
                try:
                    progress_window = customtkinter.CTkToplevel()
                    progress_window.title("Receiving File")
                    progress_window.geometry("300x150")
                    
                    screen_width = progress_window.winfo_screenwidth()
                    screen_height = progress_window.winfo_screenheight()
                    x = (screen_width - 300) // 2
                    y = (screen_height - 150) // 2
                    progress_window.geometry(f"300x150+{x}+{y}")
                    
                    progress_label = customtkinter.CTkLabel(
                        progress_window,
                        text=f"Receiving {filename}..."
                    )
                    progress_label.pack(pady=10)
                    
                    progress_bar = ttk.Progressbar(
                        progress_window,
                        length=200,
                        mode='determinate'
                    )
                    progress_bar.pack(pady=10)

                    # Receive with timeout and temporary file
                    temp_path = save_path + '.tmp'
                    received = 0
                    
                    with open(temp_path, 'wb') as f:
                        while received < filesize:
                            chunk_size = min(8192, filesize - received)
                            try:
                                self.sock.settimeout(10)  # 10 second timeout
                                chunk = self.sock.recv(chunk_size)
                                self.sock.settimeout(None)  # Reset timeout
                                if not chunk:
                                    raise Exception("Connection lost while receiving file")
                                f.write(chunk)
                                received += len(chunk)
                                progress = (received / filesize) * 100
                                progress_bar['value'] = progress
                                progress_window.update()
                            except socket.timeout:
                                raise Exception("Connection timed out while receiving file")
                    
                    # Rename temp file to final file
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    os.rename(temp_path, save_path)
                    
                    self.log_message(f"Received file '{filename}' from {sender}")
                    
                    if messagebox.askyesno("File Received", f"File saved successfully. Do you want to open {filename}?"):
                        try:
                            os.startfile(save_path)
                        except AttributeError:
                            import subprocess
                            subprocess.call(('xdg-open', save_path))
                        except Exception:
                            messagebox.showwarning("Error", "Could not open file automatically. Please open it manually.")
                            
                finally:
                    if progress_window:
                        progress_window.destroy()
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to receive file: {str(e)}")
                self.log_message(f"Error receiving file: {str(e)}")
                # Ensure socket is reset
                try:
                    self.sock.settimeout(None)
                except:
                    pass

    def _consume_file_data(self, filesize):
        """Helper method to consume unwanted file data"""
        try:
            remaining = filesize
            while remaining > 0:
                chunk_size = min(8192, remaining)
                self.sock.recv(chunk_size)
                remaining -= chunk_size
        except:
            pass

    def receive(self):
        while self.running:
            try:
                message = self.sock.recv(8192)
                if message:
                    if message.startswith(b'FILE:'):
                        self.handle_file_receive(message.decode('utf-8'))
                    else:
                        decoded_message = message.decode('utf-8')
                        
                        if decoded_message.strip() == 'NICK':
                            continue

                        # Add timestamp for messages without one
                        if not decoded_message.startswith('['):
                            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                            decoded_message = f"[{timestamp}] {decoded_message}"

                        # Handle messages
                        self.log_message(decoded_message)

                        # Save non-notification messages to history
                        if not any(x in decoded_message for x in ["joined the chat", "left the chat"]):
                            self.save_to_history(decoded_message)
                                
            except Exception as e:
                if self.running:
                    self.log_message(f"Error: {str(e)}")
                break
            
    def stop(self):
        self.running = False
        self.win.destroy()
        self.sock.close()
        sys.exit(0)

if __name__ == "__main__":
    # Show server selection dialog
    server_dialog = ServerSelectionDialog()
    server_info = server_dialog.get_server_info()
    
    if server_info:
        HOST, PORT = server_info
        try:
            client = Client(HOST, PORT)
        except Exception as e:
            error_window = customtkinter.CTk()
            error_window.withdraw()
            messagebox.showerror(
                "Connection Error",
                f"Could not connect to {HOST}:{PORT}\nError: {str(e)}"
            )
            error_window.destroy()
            sys.exit(1)
    else:
        sys.exit(0)