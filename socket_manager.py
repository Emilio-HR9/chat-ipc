import socket
import threading

# Lista global para almacenar los mensajes de chat
messages = []

# Puerto para la comunicación raw TCP
PORT = 65432


def tcp_listener():
    """
    Hilo en segundo plano que escucha conexiones TCP entrantes.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Permitir la reutilización del puerto inmediatamente después de cerrar
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Escuchar en todas las interfaces (0.0.0.0)
        server_socket.bind(("0.0.0.0", PORT))
        server_socket.listen(5)
        print(f"[*] Hilo TCP: Escuchando mensajes en el puerto {PORT}...")
    except Exception as e:
        print(f"[!] Hilo TCP: Error al iniciar el servidor en el puerto {PORT}: {e}")
        return

    while True:
        try:
            # Aceptar conexiones entrantes
            conn, addr = server_socket.accept()
            with conn:
                # Recibir datos (hasta 1024 bytes)
                data = conn.recv(1024)
                if data:
                    # Decodificar el mensaje y agregarlo a la lista global
                    decoded_msg = data.decode("utf-8")
                    formatted_msg = (
                        f'<span class="other">[{addr[0]}]</span> {decoded_msg}'
                    )
                    messages.append(formatted_msg)
                    print(f"[*] Recibido de {addr[0]}: {decoded_msg}")
        except Exception as e:
            print(f"[!] Hilo TCP: Error procesando conexión: {e}")


def send_tcp_message(dest_ip, message_text):
    """
    Envía un mensaje TCP a una IP destino.
    """
    try:
        # Crear un nuevo socket TCP como cliente
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Timeout corto de 2 segundos por si la IP destino no está disponible
        client_socket.settimeout(2.0)

        # Conectar a la IP destino en el puerto especificado
        client_socket.connect((dest_ip, PORT))

        # Enviar el mensaje codificado en UTF-8
        client_socket.sendall(message_text.encode("utf-8"))
        client_socket.close()

        # Agregar a nuestra propia lista para ver qué enviamos
        formatted_msg = f'<span class="self">[Tú -> {dest_ip}]</span> {message_text}'
        messages.append(formatted_msg)

    except socket.timeout:
        error_msg = f'<span class="error">[Error timeout conectando a {dest_ip}]</span> El destino no responde.'
        messages.append(error_msg)
    except Exception as e:
        error_msg = f'<span class="error">[Error enviando a {dest_ip}]</span> {e}'
        messages.append(error_msg)


def start_listener_thread():
    """
    Inicia el hilo del listener TCP.
    """
    listener_thread = threading.Thread(target=tcp_listener, daemon=True)
    listener_thread.start()
