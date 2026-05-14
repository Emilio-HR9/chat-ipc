import socket # Importa el módulo para la comunicación en red a bajo nivel (TCP/UDP)
import threading # Importa el módulo para manejar múltiples hilos (ej. un hilo por cada cliente)
import json # Importa json para codificar y decodificar los mensajes como diccionarios

HOST = '0.0.0.0' # El servidor escuchará en todas las interfaces de red disponibles
PORT = 65432 # Puerto en el que el servidor estará escuchando
BUFFER_SIZE = 1024 # Tamaño máximo del paquete de datos a recibir de una sola vez en bytes

clientes_registrados = {}  # Diccionario que guarda la información de los clientes TCP conectados
grupos = {}                # Diccionario que asocia las IPs de los grupos con los clientes unidos a ellos

# --- MÉTODOS TCP ---

def broadcast_messages(linea_json, sender_addr):
    # Esta función envía un mensaje a todos los clientes excepto al remitente (Broadcast)
    payload = (linea_json + "\n").encode("utf-8") # Convierte el string JSON a bytes agregando un salto de línea
    for addr, data in clientes_registrados.items(): # Itera sobre todos los clientes conectados
        if addr != sender_addr: # Verifica que el cliente actual no sea el que envió el mensaje
            try: data["sock"].sendall(payload) # Intenta enviar el mensaje por el socket TCP del cliente
            except Exception: pass # Si hay error (ej. cliente desconectado), lo ignora

def handle_unicast(linea_json, dest_ip):
    # Esta función envía un mensaje a un cliente específico (Unicast)
    payload = (linea_json + "\n").encode("utf-8") # Prepara el mensaje en bytes
    for addr, data in clientes_registrados.items(): # Recorre los clientes
        # Comprueba si la IP de destino coincide con la IP del cliente registrado
        if data["ip"] == dest_ip or addr[0] == dest_ip: 
            try: data["sock"].sendall(payload) # Envía el mensaje solo a ese cliente
            except Exception: pass # Ignora errores de envío

def handle_multicast(linea_json, group_ip, sender_addr):
    # Esta función envía un mensaje a todos los miembros de un grupo específico (Multicast)
    if group_ip in grupos: # Verifica si el grupo existe
        payload = (linea_json + "\n").encode("utf-8") # Prepara el mensaje
        for addr in list(grupos[group_ip]): # Itera sobre las direcciones de los miembros del grupo
            # Si el miembro no es el remitente y sigue conectado
            if addr != sender_addr and addr in clientes_registrados: 
                try: clientes_registrados[addr]["sock"].sendall(payload) # Le envía el mensaje
                except Exception: pass

def handle_anycast(parsed_msg, sender_addr):
    # Esta función envía un mensaje a UN SOLO cliente al azar (Anycast simulado)
    import random # Importa random para la selección aleatoria
    # Crea una lista de posibles destinatarios excluyendo al remitente
    posibles = [addr for addr in clientes_registrados if addr != sender_addr]
    if posibles: # Si hay al menos un destinatario disponible
        chosen = random.choice(posibles) # Selecciona uno al azar
        target_ip = clientes_registrados[chosen]["ip"] # Obtiene su IP
        target_hostname = clientes_registrados[chosen]["hostname"] # Obtiene su nombre
        parsed_msg["group"] = target_ip # Modifica el mensaje original para indicar que va a esta IP
        payload = (json.dumps(parsed_msg) + "\n").encode("utf-8") # Vuelve a codificar en JSON
        try:
            clientes_registrados[chosen]["sock"].sendall(payload) # Envía el mensaje al seleccionado
            # Prepara un recibo (acuse de recibo) para decirle al remitente a quién le llegó
            receipt = {
                "type": "anycast_receipt",
                "recipient_hostname": target_hostname,
                "recipient_ip": target_ip,
                "message": parsed_msg.get("message", ""),
                "protocol": parsed_msg.get("protocol", "TCP")
            }
            # Envía el recibo de vuelta al remitente
            clientes_registrados[sender_addr]["sock"].sendall((json.dumps(receipt) + "\n").encode("utf-8"))
            return target_hostname # Retorna el nombre del que lo recibió para imprimirlo en servidor
        except Exception: pass
    return None # Si no hay nadie más en la red, falla y devuelve None

# --- SERVIDOR Y MÉTODOS UDP ---

# Crea el socket UDP para el servidor (SOCK_DGRAM significa UDP)
udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Permite que el puerto se reutilice si el servidor se reinicia rápido
udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

def broadcast_udp(linea_json, sender_udp_addr):
    # Broadcast en versión UDP
    payload = (linea_json + "\n").encode("utf-8")
    for addr, data in clientes_registrados.items():
        # Revisa que el cliente tenga registrada su ruta UDP y no sea el remitente
        if "udp_addr" in data and data["udp_addr"] != sender_udp_addr:
            # sendto envía el paquete UDP a la IP/puerto específicos
            try: udp_server.sendto(payload, data["udp_addr"]) 
            except Exception: pass

def unicast_udp(linea_json, dest_ip):
    # Unicast en versión UDP
    payload = (linea_json + "\n").encode("utf-8")
    for addr, data in clientes_registrados.items():
        # Si la IP del registro coincide con el destino
        if data["ip"] == dest_ip or addr[0] == dest_ip:
            if "udp_addr" in data: # Y si conocemos su puerto UDP
                try: udp_server.sendto(payload, data["udp_addr"]) # Le enviamos el paquete
                except Exception: pass

def multicast_udp(linea_json, group_ip, sender_udp_addr):
    # Multicast en versión UDP
    if group_ip in grupos:
        payload = (linea_json + "\n").encode("utf-8")
        for addr in list(grupos[group_ip]): # Para cada miembro del grupo
            if addr in clientes_registrados: # Si el miembro está registrado
                data = clientes_registrados[addr]
                # Si tiene puerto UDP y no es el remitente
                if "udp_addr" in data and data["udp_addr"] != sender_udp_addr:
                    try: udp_server.sendto(payload, data["udp_addr"]) # Envío UDP
                    except Exception: pass

def handle_anycast_udp(parsed_msg, sender_udp_addr):
    # Anycast en versión UDP
    import random
    # Lista de posibles destinatarios que tienen UDP y no son el remitente
    posibles = [addr for addr in clientes_registrados if "udp_addr" in clientes_registrados[addr] and clientes_registrados[addr]["udp_addr"] != sender_udp_addr]
    if posibles:
        chosen = random.choice(posibles) # Selecciona uno al azar
        target_ip = clientes_registrados[chosen]["ip"]
        target_hostname = clientes_registrados[chosen]["hostname"]
        parsed_msg["group"] = target_ip # Sobreescribe destino en el JSON
        payload = (json.dumps(parsed_msg) + "\n").encode("utf-8")
        try:
            udp_server.sendto(payload, clientes_registrados[chosen]["udp_addr"]) # Envía el mensaje
            # Prepara recibo
            receipt = {
                "type": "anycast_receipt",
                "recipient_hostname": target_hostname,
                "recipient_ip": target_ip,
                "message": parsed_msg.get("message", ""),
                "protocol": parsed_msg.get("protocol", "UDP")
            }
            # Envía el recibo al remitente original
            udp_server.sendto((json.dumps(receipt) + "\n").encode("utf-8"), sender_udp_addr)
            return target_hostname
        except Exception: pass
    return None

def handle_udp_loop():
    # Bucle principal que escucha mensajes UDP entrantes en el servidor
    while True:
        try:
            # Recibe datos y la dirección de quien los envía
            data_bytes, addr = udp_server.recvfrom(BUFFER_SIZE)
            if not data_bytes: continue # Si no hay datos, pasa al siguiente
            
            # Decodifica los bytes y separa por saltos de línea (por si llegan pegados)
            lineas = data_bytes.decode("utf-8").strip().split('\n')
            for linea in lineas:
                if not linea.strip(): continue # Omite líneas vacías
                try:
                    parsed_msg = json.loads(linea) # Convierte de JSON a diccionario
                    msg_type = parsed_msg.get("type", "message") # Obtiene el tipo de mensaje
                    
                    if msg_type == "udp_register":
                        # Mensaje especial: un cliente se registra en el UDP para dar su puerto
                        sender_ip = parsed_msg.get("sender_ip", "")
                        for tcp_addr, c_data in clientes_registrados.items():
                            if c_data["ip"] == sender_ip:
                                c_data["udp_addr"] = addr # Guarda la tupla (IP, Puerto UDP)
                        continue # Termina de procesar esta línea
                    
                    # Obtiene el modo de envío y el grupo (o IP) destino
                    mode = parsed_msg.get("mode", "broadcast")
                    group = parsed_msg.get("group", "")
                    target_display = group if group else 'Todos'
                    hostname = parsed_msg.get("hostname", "Desconocido")
                    
                    # Rutea el mensaje a la función UDP correspondiente
                    if mode == "anycast":
                        chosen_host = handle_anycast_udp(parsed_msg, addr)
                        if chosen_host: target_display = chosen_host
                        else: target_display = "Nadie (sin usuarios)"
                    elif mode == "unicast" and group:
                        for c_data in clientes_registrados.values(): # Solo para buscar el nombre en el log
                            if c_data["ip"] == group:
                                target_display = c_data["hostname"]
                                break
                        unicast_udp(linea, group) # Envia el Unicast UDP
                    elif mode == "multicast" and group:
                        multicast_udp(linea, group, addr) # Envia el Multicast UDP
                    elif mode == "broadcast":
                        broadcast_udp(linea, addr) # Envia Broadcast UDP
                    
                    # Imprime un log en el servidor para depuración
                    if "message" in parsed_msg:
                        print(f"[{hostname}] -> {target_display}: {parsed_msg['message']} ({mode} vía UDP)")
                except json.JSONDecodeError: pass # Ignora si el JSON es inválido
        except Exception: pass

# --- HILO DEL CLIENTE (TCP) ---

def handle_client(conn, addr):
    # Función que se ejecuta en un hilo separado por cada cliente TCP conectado
    buffer_datos = "" # Acumula datos parciales recibidos
    registrado = False # Bandera para saber si el cliente ya envió su mensaje de "register"
    hostname = "Desconocido"
    
    while True: # Bucle infinito mientras el cliente esté conectado
        try:
            data = conn.recv(BUFFER_SIZE) # Espera y recibe datos del socket TCP
            if not data: break # Si recv() devuelve vacío, el cliente se desconectó
            
            buffer_datos += data.decode("utf-8") # Convierte a texto y lo suma al buffer
            # Procesa línea por línea usando el delimitador '\n'
            while "\n" in buffer_datos:
                linea, buffer_datos = buffer_datos.split("\n", 1) # Extrae la primera línea y deja el resto
                if not linea.strip(): continue # Ignora líneas en blanco
                
                try:
                    parsed_msg = json.loads(linea) # Transforma la línea en diccionario
                    msg_type = parsed_msg.get("type", "message")
                    
                    # Si aún no está registrado y manda "register"
                    if not registrado and msg_type == "register":
                        hostname = parsed_msg.get("hostname", "Desconocido")
                        sender_ip = parsed_msg.get("sender_ip", addr[0])
                        # Lo añade al diccionario global de clientes TCP
                        clientes_registrados[addr] = {"sock": conn, "hostname": hostname, "ip": sender_ip}
                        registrado = True
                        continue
                    
                    # Si ya está registrado, pero actualiza su nombre
                    if registrado and "hostname" in parsed_msg and addr in clientes_registrados:
                        current_h = parsed_msg["hostname"]
                        clientes_registrados[addr]["hostname"] = current_h
                        hostname = current_h
                    
                    # Si pide unirse a un grupo multicast
                    if msg_type == "join":
                        group_ip = parsed_msg.get("group")
                        if group_ip not in grupos: grupos[group_ip] = set() # Lo crea si no existe
                        grupos[group_ip].add(addr) # Agrega la dirección del cliente al grupo
                        continue

                    # Si pide abandonar un grupo multicast
                    if msg_type == "leave":
                        group_ip = parsed_msg.get("group")
                        if group_ip in grupos and addr in grupos[group_ip]:
                            grupos[group_ip].remove(addr) # Lo saca
                            # Prepara mensaje para avisarle a los demás que se fue
                            leave_msg = json.dumps({
                                "type": "left_group",
                                "group": group_ip,
                                "sender_ip": clientes_registrados[addr]["ip"],
                                "hostname": clientes_registrados[addr]["hostname"]
                            })
                            broadcast_messages(leave_msg, addr) # Retransmite el aviso
                        continue

                    # Si quiere invitar a alguien a un grupo
                    if msg_type == "invite":
                        group_name = parsed_msg.get("group")
                        invitees = parsed_msg.get("invitees", []) # Lista de IPs a invitar
                        if group_name and invitees:
                            if group_name not in grupos: grupos[group_name] = set()
                            grupos[group_name].add(addr) # El invitador se asegura de estar en el grupo
                            payload_inv = (linea + "\n").encode("utf-8")
                            # Busca a los invitados y les manda la invitación directa
                            for m_addr, m_data in clientes_registrados.items():
                                if m_data["ip"] in invitees:
                                    try: m_data["sock"].sendall(payload_inv)
                                    except Exception: pass
                        continue

                    # Mensaje de descubrimiento continuo (heartbeat)
                    if msg_type == "discovery":
                        broadcast_messages(linea, addr) # Lo retransmite a todos
                        continue

                    # Llegado a este punto, es un mensaje de chat normal
                    mode = parsed_msg.get("mode", "broadcast")
                    group = parsed_msg.get("group", "")
                    
                    target_display = group if group else 'Todos' # Para el print en consola
                    
                    # Ruteo de mensajes TCP según el modo
                    if mode == "anycast":
                        chosen_host = handle_anycast(parsed_msg, addr)
                        if chosen_host:
                            target_display = chosen_host
                        else:
                            target_display = "Nadie (sin usuarios)"
                    elif mode == "unicast" and group:
                        for c_data in clientes_registrados.values():
                            if c_data["ip"] == group:
                                target_display = c_data["hostname"]
                                break
                        handle_unicast(linea, group) # Enviar Unicast TCP
                    elif mode == "multicast" and group:
                        handle_multicast(linea, group, addr) # Enviar Multicast TCP
                    elif mode == "broadcast":
                        broadcast_messages(linea, addr) # Enviar Broadcast TCP
                        
                    # Log en el servidor
                    if "message" in parsed_msg:
                        print(f"[{hostname}] -> {target_display}: {parsed_msg['message']} ({mode} vía TCP)")
                        
                except json.JSONDecodeError: pass # Ignora si hubo error de formato JSON
        except Exception: break # Si el recv() falla por error de conexión, rompe el bucle principal

    # --- RUTINA DE DESCONEXIÓN ---
    conn.close() # Cierra el socket del cliente
    if addr in clientes_registrados:
        sender_ip = clientes_registrados[addr]["ip"]
        # Crea un mensaje especial para que los clientes sepan que se desconectó y borren su IP
        disconnect_msg = json.dumps({"type": "disconnect", "sender_ip": sender_ip})
        del clientes_registrados[addr] # Lo borra del diccionario global
        broadcast_messages(disconnect_msg, addr) # Avisa a todos por TCP
        try: broadcast_udp(disconnect_msg, None) # Avisa por UDP si es posible
        except Exception: pass
        
    # Lo saca de todos los grupos a los que estaba unido
    for g in grupos.values():
        if addr in g: g.remove(addr)

def iniciar_servidor():
    # Inicializa los servidores TCP y UDP principales
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Enlaza el servidor UDP a la IP 0.0.0.0 y al puerto 65432
        udp_server.bind((HOST, PORT))
        # Arranca el hilo en bucle que escucha mensajes UDP
        threading.Thread(target=handle_udp_loop, daemon=True).start()
    except Exception as e: print(f"[!] Error UDP: {e}")
    
    try:
        # Enlaza el servidor TCP
        server.bind((HOST, PORT))
        server.listen() # Comienza a escuchar conexiones entrantes (Handshake)
        print(f"[*] SERVIDOR INICIADO EN {HOST}:{PORT} (TCP/UDP)")
        while True: # Bucle infinito esperando nuevos clientes
            conn, addr = server.accept() # Acepta una nueva conexión. Bloquea hasta que alguien entre.
            # Inicia un hilo dedicado exclusivamente a este cliente y sigue esperando más
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as e: print(f"[!] Error TCP: {e}")

if __name__ == "__main__":
    # Solo ejecuta el servidor si se ejecuta este script directamente
    iniciar_servidor()
