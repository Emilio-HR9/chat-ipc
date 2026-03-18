import socket
import struct
import threading


def get_directed_broadcast_ip():
    """
    Obtiene la IP local real y calcula la dirección de broadcast dinámicamente
    leyendo la máscara de subred real del sistema operativo.
    """
    import ipaddress
    import os
    import subprocess

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Nos conectamos a una IP de prueba para forzar al SO a elegir la interfaz principal
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()

    if local_ip == "127.0.0.1":
        return "255.255.255.255"

    prefix_length = 24  # Valor por defecto /24

    try:
        if os.name == "nt":
            # Windows: Usar PowerShell para obtener la máscara de la IP
            cmd = f"powershell -NoProfile -Command \"(Get-NetIPAddress -IPAddress '{local_ip}' -ErrorAction SilentlyContinue).PrefixLength\""
            output = subprocess.check_output(cmd, shell=True, text=True).strip()
            if output:
                prefix = output.splitlines()[0].strip()
                if prefix.isdigit():
                    prefix_length = int(prefix)
        else:
            # Linux/macOS: Intentar extraer de 'ip addr'
            cmd = f"ip -o -f inet addr show | grep '{local_ip}'"
            output = subprocess.check_output(cmd, shell=True, text=True).strip()
            if "/" in output:
                part = output.split(f"{local_ip}/")[1]
                prefix = part.split()[0]
                if prefix.isdigit():
                    prefix_length = int(prefix)
    except Exception as e:
        print(
            f"[*] No se pudo leer la máscara exacta del SO, usando /{prefix_length}. Error: {e}"
        )

    try:
        # Calcula matemáticamente la dirección de broadcast real
        network = ipaddress.IPv4Network(f"{local_ip}/{prefix_length}", strict=False)
        return str(network.broadcast_address)
    except Exception:
        # Fallback de emergencia
        ip_parts = local_ip.split(".")
        ip_parts[3] = "255"
        return ".".join(ip_parts)


# Lista global para almacenar los mensajes de chat
messages = []

# Puerto para la comunicación
PORT = 65432
# Grupo multicast por defecto
MULTICAST_GROUP = "224.1.1.1"

# Variables globales para el socket UDP y los grupos a los que estamos unidos
udp_socket = None
joined_groups = set([MULTICAST_GROUP])


def tcp_listener():
    """
    Hilo en segundo plano que escucha conexiones TCP entrantes (Unicast).
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind(("0.0.0.0", PORT))
        server_socket.listen(5)
        print(f"[*] Hilo TCP: Escuchando mensajes en el puerto {PORT}...")
    except Exception as e:
        print(f"[!] Hilo TCP: Error al iniciar el servidor en el puerto {PORT}: {e}")
        return

    while True:
        try:
            conn, addr = server_socket.accept()
            with conn:
                data = conn.recv(1024)
                if data:
                    decoded_msg = data.decode("utf-8")
                    formatted_msg = f'<span class="other">[UNICAST from {addr[0]}]</span> {decoded_msg}'
                    messages.append(formatted_msg)
                    print(f"[*] Recibido de {addr[0]}: {decoded_msg}")
        except Exception as e:
            print(f"[!] Hilo TCP: Error procesando conexión: {e}")


def udp_listener():
    """
    Hilo en segundo plano que escucha datagramas UDP (Broadcast y Multicast).
    """
    global udp_socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Escuchar en todas las interfaces en el puerto especificado
        udp_socket.bind(("", PORT))

        # Unirse al grupo multicast por defecto
        mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
        udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print(
            f"[*] Hilo UDP: Escuchando broadcasts y multicasts en el puerto {PORT}..."
        )
    except Exception as e:
        print(f"[!] Hilo UDP: Error al iniciar el listener: {e}")
        return

    while True:
        try:
            # Recibir datos (hasta 1024 bytes)
            data, addr = udp_socket.recvfrom(1024)
            if data:
                decoded_msg = data.decode("utf-8")

                # Para evitar mostrar nuestros propios mensajes en la interfaz si es un eco
                # (Una solución robusta usaría un ID de mensaje)
                if (
                    messages
                    and f"-> {MULTICAST_GROUP}" in messages[-1]
                    and decoded_msg in messages[-1]
                ):
                    continue
                if (
                    messages
                    and "-> &lt;broadcast&gt;" in messages[-1]
                    and decoded_msg in messages[-1]
                ):
                    continue

                formatted_msg = (
                    f'<span class="other">[UDP from {addr[0]}]</span> {decoded_msg}'
                )
                messages.append(formatted_msg)
                print(f"[*] Recibido UDP de {addr[0]}: {decoded_msg}")
        except Exception as e:
            print(f"[!] Hilo UDP: Error procesando datagrama: {e}")


def join_multicast_group(group_ip):
    """
    Permite unirse a un nuevo grupo multicast en tiempo de ejecución.
    """
    global udp_socket
    if not udp_socket:
        return False, "El socket UDP no está inicializado."

    if group_ip in joined_groups:
        return False, "Ya estás en este grupo."

    try:
        mreq = struct.pack("4sl", socket.inet_aton(group_ip), socket.INADDR_ANY)
        udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        joined_groups.add(group_ip)

        formatted_msg = f'<span class="system" style="color: #007bff; font-weight: bold;">[Sistema] Te has unido al grupo multicast {group_ip}</span>'
        messages.append(formatted_msg)
        return True, "Unido exitosamente"
    except Exception as e:
        return False, f"Error uniéndose al grupo: {e}"


def send_message(mode, dest_ip, message_text):
    """
    Envía un mensaje según el modo seleccionado (unicast, broadcast, multicast, anycast).
    """
    display_ip = dest_ip
    try:
        if mode in ["unicast", "anycast"]:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(2.0)
            client_socket.connect((dest_ip, PORT))
            client_socket.sendall(message_text.encode("utf-8"))
            client_socket.close()

        elif mode == "broadcast":
            target_broadcast = get_directed_broadcast_ip()
            display_ip = f"&lt;broadcast: {target_broadcast}&gt;"
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # Enviar a la dirección de broadcast dirigida
            client_socket.sendto(message_text.encode("utf-8"), (target_broadcast, PORT))
            client_socket.close()

        elif mode == "multicast":
            display_ip = dest_ip if dest_ip else MULTICAST_GROUP
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ttl = struct.pack("b", 1)
            client_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            client_socket.sendto(message_text.encode("utf-8"), (display_ip, PORT))
            client_socket.close()

        # Agregar a nuestra propia lista para ver qué enviamos
        formatted_msg = f'<span class="self">[Tú {mode.upper()} -> {display_ip}]</span> {message_text}'
        messages.append(formatted_msg)

    except socket.timeout:
        error_msg = f'<span class="error">[Error timeout conectando a {dest_ip}]</span> El destino no responde.'
        messages.append(error_msg)
    except Exception as e:
        error_msg = f'<span class="error">[Error enviando a {dest_ip}]</span> {e}'
        messages.append(error_msg)


def start_listener_threads():
    """
    Inicia los hilos de los listeners TCP y UDP.
    """
    tcp_thread = threading.Thread(target=tcp_listener, daemon=True)
    udp_thread = threading.Thread(target=udp_listener, daemon=True)
    tcp_thread.start()
    udp_thread.start()
