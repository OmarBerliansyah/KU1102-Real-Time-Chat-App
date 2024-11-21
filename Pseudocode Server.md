PROGRAM ChatServer

{ KAMUS }
host : string                      { alamat IP server }
port : integer                     { port server }
clients : array of socket          { daftar koneksi klien }
nicknames : array of string        { daftar nama pengguna }
server : socket                    { socket server }
log_file : string                  { file untuk menyimpan log }

{ FUNGSI dan PROSEDUR }
procedure init_server(input host: string, input port: integer)
{ Inisialisasi server dan binding ke alamat dan port }
    try:
        server ← create_socket()
        bind_socket(server, host, port)
        listen_socket(server)
        create_log_directory()
    catch Exception as e:
        write_log("Gagal memulai server")
        raise e

procedure log_message(input message: string)
{ Mencatat pesan ke file log }
    try:
        TULIS(log_file, message + "\n")
    catch Exception as e:
        write_log("Gagal mencatat pesan")

procedure broadcast(input message: string, input sender: socket)
{ Mengirim pesan ke semua klien kecuali pengirim }
    timestamp ← get_current_time()
    for each client in clients do
        if client ≠ sender then
            try:
                if message is string then
                    send(client, "[" + timestamp + "] " + message)
                else
                    send(client, message)
            catch Exception:
                remove_client(client)

procedure handle_file_transfer(input sender: socket, input message: bytes)
{ Menangani transfer file antara klien }
    { KAMUS LOKAL }
    header, filename, filesize, sender_name : string
    unique_filename : string
    file_data : bytes
    remaining : integer

    { ALGORITMA }
    try:
        parse_header(message)
        create_temp_directory_if_not_exists()
        unique_filename ← generate_unique_filename(filename)
        save_temp_file(unique_filename, file_data, filesize, sender)

        { Broadcast file ke klien lain }
        for each client in clients do
            if client ≠ sender then
                send_file(client, file_data, header)
        delete_temp_file(unique_filename)
    catch Exception:
        write_log("Gagal menangani transfer file")

procedure handle_client(input client: socket, input address: string)
{ Menangani koneksi individual klien }
    { KAMUS LOKAL }
    nickname : string
    message : string

    { ALGORITMA }
    try:
        send(client, "NICK")
        nickname ← receive(client)
        broadcast_join(nickname)
        add_client(client, nickname)

        while client_connected do
            message ← receive(client)
            if starts_with(message, "FILE:") then
                handle_file_transfer(client, message)
            else:
                broadcast(message, client)
                log_message(message)
    finally:
        remove_client(client)

{ ALGORITMA UTAMA }
try:
    init_server(host, port)
    while true do
        client, address ← accept_connection()
        create_thread(handle_client, client, address)
except KeyboardInterrupt:
    stop_server()
except Exception as e:
    write_log("Error fatal: " + e)
