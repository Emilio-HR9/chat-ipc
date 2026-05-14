import socket # Importa el módulo para usar sockets de red
import threading # Importa el módulo para manejar hilos (permitiendo que tareas se ejecuten en paralelo)
import json # Importa json para manipular datos en formato JSON
import time # Importa time para manejar retrasos (sleeps)

# --- CONFIGURACIÓN DE RED ---
# Asegúrate de poner aquí la IP de tu servidor (sea la local o la de ZeroTier)
SERVER_IP = "192.168.43.140" # IP del servidor al que nos vamos a conectar. Cambiar si el servidor está en otra máquina.
PORT = 65432 # Puerto que usa el servidor para la comunicación TCP y UDP
BUFFER_SIZE = 1024 # Tamaño del buffer de recepción de datos (en bytes)

current_hostname = socket.gethostname() # Obtiene el nombre del equipo actual y lo asigna como nombre de usuario por defecto
joined_groups = set() # Crea un conjunto (set) vacío para guardar a qué grupos multicast estamos suscritos (evita duplicados)
known_members = {}  # Diccionario para almacenar los miembros conocidos en cada sala/grupo
messages = [] # Lista que almacenará todos los mensajes que se muestran en el chat
client_socket = None # Variable global para el socket TCP, inicializada en None
web_port = 5000 # Puerto web por defecto (será actualizado por app.py si es necesario)

# SOCKET UDP DEL CLIENTE
# Crea un socket UDP (SOCK_DGRAM) para enviar y recibir paquetes UDP
client_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Enlaza el socket UDP en todas las interfaces y le pide al sistema que le asigne un puerto libre (0)
client_udp.bind(("0.0.0.0", 0))

def set_web_port(port):
    # Función llamada por app.py para actualizar qué puerto web estamos usando
    global web_port
    web_port = port

def get_client_id():
    # Devuelve el identificador único del cliente en formato "IP:PUERTO_WEB"
    return f"{get_local_ip()}:{web_port}"

def get_local_ip():
    # Intenta descubrir cuál es nuestra IP en la red local
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Se conecta a un servidor externo (Google DNS) pero sin enviar nada, solo para forzar a la tarjeta de red a revelar la IP de salida
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0] # Extrae la IP de la conexión falsa
    except Exception:
        ip = '127.0.0.1' # Si falla (ej. sin internet), asume localhost
    finally:
        s.close() # Siempre cierra el socket temporal
    return ip

def connect_to_server():
    # Hilo encargado de conectarse al servidor por TCP y escuchar mensajes entrantes
    global client_socket, current_hostname
    local_ip = get_client_id() # Toma la IP local
    
    while True: # Bucle infinito por si el servidor se cae, intentará reconectar
        try:
            # Crea un nuevo socket TCP y se conecta al servidor
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, PORT))
            
            # Prepara el payload inicial de registro enviando el nombre y la IP al servidor
            reg_payload = json.dumps({"type": "register", "hostname": current_hostname, "sender_ip": local_ip})
            client_socket.sendall((reg_payload + "\n").encode("utf-8")) # Envía el registro
            
            # Dar tiempo al servidor para registrar TCP antes del UDP
            time.sleep(0.5)
            
            # Envía también un mensaje de registro UDP para que el servidor sepa nuestro puerto UDP
            udp_reg = json.dumps({"type": "udp_register", "sender_ip": local_ip})
            client_udp.sendto((udp_reg + "\n").encode("utf-8"), (SERVER_IP, PORT))
            
            # Si nos desconectamos y volvemos a conectar, nos re-inscribimos en nuestros grupos
            for g in joined_groups:
                join_payload = json.dumps({"type": "join", "group": g})
                client_socket.sendall((join_payload + "\n").encode("utf-8"))
            
            buffer_datos = "" # Buffer para acumular fragmentos de mensajes TCP
            while True: # Bucle de escucha constante sobre la conexión TCP
                data = client_socket.recv(BUFFER_SIZE) # Espera recibir datos
                if not data: break # Si llega vacío, se cortó la conexión; sale del bucle
                
                buffer_datos += data.decode("utf-8") # Pasa los datos de bytes a string
                while "\n" in buffer_datos: # Procesa línea a línea
                    linea, buffer_datos = buffer_datos.split("\n", 1) # Parte el string
                    if not linea.strip(): continue # Omite si está vacío
                    
                    try:
                        parsed = json.loads(linea) # Intenta decodificar el JSON
                        msg_type = parsed.get("type", "message") # Saca el tipo de mensaje
                        sender_ip = parsed.get("sender_ip", "Unknown") # Quién lo envió
                        hostname = parsed.get("hostname", "Unknown") # El nombre de quien lo envió
                        mode = parsed.get("mode", "broadcast") # El modo (unicast, broadcast, etc.)
                        group_name = parsed.get("group", "Broadcast") # A qué grupo/IP iba destinado
                        protocol_label = parsed.get("protocol", "TCP") # Por qué protocolo llegó
                        
                        # Mantiene la lista de usuarios activa para poder darles clic en la interfaz
                        if sender_ip != "Unknown" and hostname != "Unknown" and msg_type != "disconnect":
                            cat = group_name if mode == "multicast" else "Unicast/Anycast" # Decide la categoría en la interfaz
                            if cat not in known_members: known_members[cat] = {} # Crea la categoría si no existe
                            known_members[cat][sender_ip] = hostname # Añade/Actualiza al miembro
                            
                        # Si es un aviso de que alguien se desconectó
                        if msg_type == "disconnect":
                            if "Unicast/Anycast" in known_members:
                                known_members["Unicast/Anycast"].pop(sender_ip, None) # Lo saca de la lista general
                            for g in known_members:
                                if g != "Unicast/Anycast":
                                    known_members[g].pop(sender_ip, None) # Lo saca de todos los grupos
                            continue # Pasa al siguiente mensaje
                        
                        if msg_type == "discovery": continue # Si es heartbeat puro, lo ignora (ya actualizó su presencia arriba)
                        
                        # Si alguien nos invitó a un grupo
                        if msg_type == "invite":
                            inv_group = parsed.get("group")
                            if inv_group and inv_group not in joined_groups:
                                joined_groups.add(inv_group) # Añade a la lista local
                                
                                # Enviar join al servidor para registrarnos en el grupo a nivel servidor
                                join_payload = json.dumps({"type": "join", "group": inv_group})
                                client_socket.sendall((join_payload + "\n").encode("utf-8"))
                                
                                # Añade un mensaje de sistema a la lista de mensajes de la interfaz
                                messages.append({"chat_id": inv_group, "html": f'<span class="system" style="color: #007bff; font-weight: bold;">[Sistema] Has sido añadido al grupo {inv_group} por {hostname}</span>'})
                            continue

                        # Si alguien salió de un grupo
                        if msg_type == "left_group":
                            g_left = parsed.get("group")
                            s_left = parsed.get("sender_ip")
                            h_left = parsed.get("hostname", "Un usuario")
                            if g_left in known_members and s_left in known_members[g_left]:
                                known_members[g_left].pop(s_left, None) # Lo borra del registro local del grupo
                                if g_left in joined_groups: # Si estamos en el grupo, muestra un aviso
                                    messages.append({"chat_id": g_left, "html": f'<span class="system" style="color: orange; font-weight: bold;">[Sistema] {h_left} ha salido del grupo.</span>', "is_self": False})
                            continue
                        
                        # Si nosotros enviamos un Anycast, el servidor nos devuelve este recibo indicando a quién le tocó
                        if msg_type == "anycast_receipt":
                            recip_host = parsed.get("recipient_hostname")
                            recip_ip = parsed.get("recipient_ip")
                            m_text = parsed.get("message", "")
                            protocol_label = parsed.get("protocol", "TCP")
                            formatted_msg = f'<span class="self">[Tú ANYCAST -> {recip_host} ({recip_ip}) | {protocol_label}]</span> {m_text}'
                            # Ponemos el mensaje en la pestaña de chat del que lo recibió para que lo veamos
                            messages.append({"chat_id": recip_ip, "html": formatted_msg, "is_self": True})
                            continue
                            
                        # Si es un mensaje de chat con texto
                        if "message" in parsed:
                            msg_text = parsed["message"]
                            
                            # --- EL ENRUTAMIENTO CORRECTO DE LAS PESTAÑAS ---
                            if mode in ["unicast", "anycast", "broadcast"]:
                                chat_id = sender_ip  # Va a la pestaña del usuario específico
                            elif mode == "multicast":
                                chat_id = group_name # Va a la pestaña del grupo
                            else:
                                chat_id = "all" # Va a la principal
                            
                            # Crea el bloque HTML para mostrar en pantalla
                            formatted_msg = f'<span class="other">[De {hostname} (<a href="#" class="ip-link" data-ip="{sender_ip}">{sender_ip}</a>) | {protocol_label}]</span> {msg_text}'
                            messages.append({"chat_id": chat_id, "html": formatted_msg, "is_self": False}) # Guarda
                            
                    except json.JSONDecodeError: pass # Ignora si el JSON está mal
        except Exception:
            # Si hay cualquier error de red, cierra el socket y espera 3 segundos antes de reintentar
            if client_socket: client_socket.close()
            time.sleep(3)

def listen_udp():
    # Hilo encargado de escuchar de forma independiente los paquetes UDP (Broadcast/Multicast enviados por UDP)
    global current_hostname
    while True:
        try:
            # Recibe directamente del socket UDP un paquete de datos
            data_bytes, addr = client_udp.recvfrom(BUFFER_SIZE)
            linea = data_bytes.decode("utf-8").strip() # Convierte a texto
            if not linea: continue
            
            try:
                parsed = json.loads(linea) # Interpreta el JSON
                msg_type = parsed.get("type", "message")
                sender_ip = parsed.get("sender_ip", "Unknown")
                hostname = parsed.get("hostname", "Unknown")
                mode = parsed.get("mode", "broadcast")
                group_name = parsed.get("group", "Broadcast")
                protocol_label = parsed.get("protocol", "UDP")
                
                # Actualiza también la lista de conocidos con los mensajes que llegan por UDP
                if sender_ip != "Unknown" and hostname != "Unknown" and msg_type != "disconnect":
                    cat = group_name if mode == "multicast" else "Unicast/Anycast"
                    if cat not in known_members: known_members[cat] = {}
                    known_members[cat][sender_ip] = hostname
                    
                # Si llega el aviso de desconexión por UDP
                if msg_type == "disconnect":
                    if "Unicast/Anycast" in known_members:
                        known_members["Unicast/Anycast"].pop(sender_ip, None)
                    for g in known_members:
                        if g != "Unicast/Anycast":
                            known_members[g].pop(sender_ip, None)
                    continue
                
                if msg_type == "discovery": continue
                
                # Si llega la invitación a grupo por UDP
                if msg_type == "invite":
                    inv_group = parsed.get("group")
                    if inv_group and inv_group not in joined_groups:
                        joined_groups.add(inv_group)
                        
                        # Enviar join al servidor (sobre TCP ya que es más seguro y lo requiere el servidor TCP)
                        if client_socket and client_socket.fileno() != -1:
                            join_payload = json.dumps({"type": "join", "group": inv_group})
                            client_socket.sendall((join_payload + "\n").encode("utf-8"))
                            
                        messages.append({"chat_id": inv_group, "html": f'<span class="system" style="color: #007bff; font-weight: bold;">[Sistema] Has sido añadido al grupo {inv_group} por {hostname}</span>'})
                    continue
                
                # Recibo de Anycast versión UDP
                if msg_type == "anycast_receipt":
                    recip_host = parsed.get("recipient_hostname")
                    recip_ip = parsed.get("recipient_ip")
                    m_text = parsed.get("message", "")
                    protocol_label = parsed.get("protocol", "UDP")
                    formatted_msg = f'<span class="self">[Tú ANYCAST -> {recip_host} ({recip_ip}) | {protocol_label}]</span> {m_text}'
                    messages.append({"chat_id": recip_ip, "html": formatted_msg, "is_self": True})
                    continue
                
                # Procesa mensaje de chat en UDP
                if "message" in parsed:
                    msg_text = parsed["message"]
                    
                    if mode in ["unicast", "anycast", "broadcast"]:
                        chat_id = sender_ip
                    elif mode == "multicast":
                        chat_id = group_name
                    else:
                        chat_id = "all"
                    
                    # Formatea e inserta el mensaje UDP en la interfaz
                    formatted_msg = f'<span class="other">[De {hostname} (<a href="#" class="ip-link" data-ip="{sender_ip}">{sender_ip}</a>) | {protocol_label}]</span> {msg_text}'
                    messages.append({"chat_id": chat_id, "html": formatted_msg, "is_self": False})
                    
            except json.JSONDecodeError: pass
        except Exception:
            time.sleep(1) # Si hay un error al leer UDP, espera 1 segundo y reintenta

def discovery_broadcaster():
    # Hilo que se ejecuta cada 5 segundos para anunciar al servidor que seguimos "vivos" y estamos en X grupos
    global client_socket, current_hostname
    while True:
        if client_socket and client_socket.fileno() != -1: # Si estamos conectados
            my_ip = get_client_id()
            try:
                # Heartbeat de registro UDP para que el servidor nunca olvide nuestra ruta UDP (por si el puerto/ip de la tabla NAT cambió)
                udp_reg = json.dumps({"type": "udp_register", "sender_ip": my_ip})
                client_udp.sendto((udp_reg + "\n").encode("utf-8"), (SERVER_IP, PORT))
                
                # Envía heartbeat TCP genérico
                payload = json.dumps({
                    "type": "discovery", "hostname": current_hostname, "group": "Unicast/Anycast",
                    "mode": "broadcast", "sender_ip": my_ip
                })
                client_socket.sendall((payload + "\n").encode("utf-8"))
                
                # Envía heartbeats TCP para reafirmar nuestra presencia en cada grupo en el que estamos
                for g in list(joined_groups):
                    payload_g = json.dumps({
                        "type": "discovery", "hostname": current_hostname, "group": g,
                        "mode": "multicast", "sender_ip": my_ip
                    })
                    client_socket.sendall((payload_g + "\n").encode("utf-8"))
            except Exception: pass
        time.sleep(5) # Espera 5 segundos antes del siguiente ping

def send_message(mode, target, message_text, protocol="TCP"):
    # Función que se usa desde app.py para enviar cualquier mensaje
    global client_socket, current_hostname
    # Evita enviar si no hay conexión TCP activa (incluso para UDP necesitamos conexión lógica)
    if not client_socket or client_socket.fileno() == -1: return
    
    local_ip = get_client_id()
    group_name = target if mode != "broadcast" else "Broadcast"
    display_ip = target if mode != "broadcast" else "Todos"
    
    try:
        # Prepara el cuerpo principal del mensaje
        payload = json.dumps({
            "hostname": current_hostname, "message": message_text, "mode": mode,
            "group": group_name, "sender_ip": local_ip, "protocol": protocol
        })
        payload_bytes = (payload + "\n").encode("utf-8") # A bytes con terminador de línea
        
        # Decide por qué socket mandarlo según lo que elija el usuario
        if protocol == "UDP":
            client_udp.sendto(payload_bytes, (SERVER_IP, PORT)) # Envío directo al server UDP
        else:
            client_socket.sendall(payload_bytes) # Envío directo al server TCP
        
        # --- EL AUTO-ECO A LA PESTAÑA CORRECTA ---
        # Si no es anycast (anycast espera el recibo desde el servidor antes de pintar el mensaje), lo pinta en nuestra pantalla ya mismo
        if mode != "anycast":
            if mode in ["unicast", "multicast"]:
                chat_id = target
            else:
                chat_id = "all"
                
            # Agrega un mensaje que empieza con "[Tú...]"
            formatted_msg = f'<span class="self">[Tú {mode.upper()} -> {display_ip} | {protocol}]</span> {message_text}'
            messages.append({"chat_id": chat_id, "html": formatted_msg, "is_self": True})
    except Exception: pass

def join_multicast_group(group_ip, invitees=None):
    # Función para unirse y opcionalmente invitar a otros a un grupo
    global client_socket
    joined_groups.add(group_ip) # Lo añade al registro local
    if client_socket:
        try:
            # Pide al servidor unirse al grupo
            payload = json.dumps({"type": "join", "group": group_ip})
            client_socket.sendall((payload + "\n").encode("utf-8"))
            
            # Si se seleccionaron personas a invitar, manda comando de invite
            if invitees:
                inv_payload = json.dumps({"type": "invite", "group": group_ip, "invitees": invitees, "hostname": current_hostname})
                client_socket.sendall((inv_payload + "\n").encode("utf-8"))
        except Exception: pass
    # Muestra aviso en la pestaña del grupo
    messages.append({"chat_id": group_ip, "html": f'<span class="system" style="color: #007bff; font-weight: bold;">[Sistema] Te has unido a la sala {group_ip}</span>'})
    return True, f"Unido exitosamente a {group_ip}"

def leave_multicast_group(group_ip):
    # Función para salir de un grupo
    global client_socket
    if group_ip in joined_groups:
        joined_groups.remove(group_ip) # Lo quita localmente
        if client_socket:
            try:
                # Le avisa al servidor que nos saque de su registro de ese grupo
                payload = json.dumps({"type": "leave", "group": group_ip})
                client_socket.sendall((payload + "\n").encode("utf-8"))
            except Exception: pass
        # Muestra en la pestaña que ya salimos
        messages.append({"chat_id": group_ip, "html": f'<span class="system" style="color: red; font-weight: bold;">[Sistema] Has salido de la sala {group_ip}</span>'})
        return True
    return False

def start_listener_threads(): 
    # Función inicializadora, lanza los 3 hilos de trabajo pesado en modo 'daemon' (se cierran solos al salir de la app)
    threading.Thread(target=connect_to_server, daemon=True).start()
    threading.Thread(target=listen_udp, daemon=True).start()
    threading.Thread(target=discovery_broadcaster, daemon=True).start()

def get_current_hostname(): 
    # Devuelve el hostname actual
    return current_hostname
def set_custom_hostname(name): 
    # Actualiza el hostname cuando el usuario lo cambia en la web
    global current_hostname; current_hostname = name
