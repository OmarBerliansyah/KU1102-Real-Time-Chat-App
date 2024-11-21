PROGRAM ChatClient

{ ===================== DEFINISI TIPE ===================== }
type Window : <
    title: string,
    width: integer,
    height: integer,
    is_fullscreen: boolean
>

type Button : <
    text: string,
    width: integer,
    command: function
>

type TextArea : <
    content: string,
    font: string,
    state: string,
    tags: array of string
>

{ ===================== KAMUS GLOBAL ===================== }
host, nickname : string
port : integer
sock : socket
gui_done, running : boolean
clients : array of socket
history_file : string
win : Window
text_area : TextArea
input_area : TextArea
is_fullscreen : boolean

{ ===================== KELAS ===================== }

{ Kelas untuk dialog pemilihan server }
class ServerSelectionDialog
    { KAMUS LOKAL }
    window : Window
    selected_ip : tuple of (string, integer)
    ip_list : array of string
    ip_entry, port_entry : TextArea
    
    { METODE }
    procedure init()
        window ← create_window("Select Server", 400, 300)
        create_gui_components()
        populate_ips()
    
    function get_available_ips() → array of tuple
        { Mendapatkan daftar IP yang tersedia }
        try:
            hostname ← get_hostname()
            local_ip ← get_local_ip(hostname)
            return array berisi (ip, tipe)
        catch:
            return [('127.0.0.1', "Localhost")]
    
    procedure on_connect()
        if selection from ip_list then
            ip ← selection.value
        else
            ip ← ip_entry.text or '127.0.0.1'
        port ← convert_to_int(port_entry.text) or 8000
        selected_ip ← (ip, port)
        window.quit()

{ Kelas untuk tampilan loading }
class LoadingScreen
    { KAMUS LOKAL }
    window : Window
    progress_bar : ProgressBar
    label : Label
    
    { METODE }
    procedure init()
        window ← create_window("Connecting...", 300, 150)
        create_progress_bar()
        create_label("Connecting to server...")
        start_progress()

{ Kelas utama client }
class Client
    { KAMUS LOKAL }
    nickname : string
    sock : socket
    gui_done : boolean
    running : boolean
    history_file : string
    
    { METODE }
    procedure init(host: string, port: integer)
        { Inisialisasi client }
        prompt_nickname()
        show_loading_screen()
        connect_to_server(host, port)
        start_receive_thread()
        start_gui()
    
    procedure gui_loop()
        { Setup GUI utama }
        create_main_window()
        create_chat_area()
        create_input_area()
        create_buttons()
        setup_event_handlers()
        start_gui_loop()
    
    procedure handle_message(message: string)
        { Menangani pesan yang diterima }
        if starts_with(message, "FILE:") then
            handle_file_receive(message)
        else
            format_and_display_message(message)
            save_to_history(message)
    
    procedure handle_file_transfer(message: string)
        { Menangani transfer file }
        { KAMUS LOKAL }
        filename, filesize, sender : string
        progress_window : Window
        file_data : bytes
        remaining : integer
        
        { ALGORITMA }
        parse_file_header(message)
        save_path ← ask_save_location()
        if save_path ≠ empty then
            show_progress_window()
            while remaining > 0 do
                receive_and_save_chunk()
                update_progress()
            save_complete_file()
            offer_to_open_file()
    
    procedure format_text(style: string)
        { Format teks yang dipilih }
        try:
            selection ← get_selected_text()
            if selection ≠ empty then
                case of style:
                    "bold": formatted ← "**" + selection + "**"
                    "italic": formatted ← "*" + selection + "*"
                    "underline": formatted ← "_" + selection + "_"
                replace_selection(formatted)
        catch:
            pass
    
    procedure send_message()
        { Mengirim pesan }
        message ← get_input_text()
        if not empty(message) then
            timestamp ← get_current_time()
            server_message ← nickname + ": " + message
            send_to_server(server_message)
            display_message(timestamp + server_message)
            clear_input()
            save_to_history(message)
    
    procedure receive_messages()
        { Thread untuk menerima pesan }
        while running do
            try:
                message ← receive_from_server()
                if not empty(message) then
                    process_received_message(message)
            catch:
                if running then
                    log_error("Connection lost")
                break

{ ===================== ALGORITMA UTAMA ===================== }
{ Program utama }
server_dialog ← new ServerSelectionDialog()
server_info ← server_dialog.get_server_info()

if server_info ≠ empty then
    HOST, PORT ← server_info
    try:
        client ← new Client(HOST, PORT)
        client.start()
    catch Exception as e:
        show_error("Could not connect to " + HOST + ":" + PORT)
        exit(1)
else:
    exit(0)
