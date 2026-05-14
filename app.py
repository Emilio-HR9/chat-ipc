import socket # Importa el módulo de sockets (aunque no se usa directamente en este archivo superior más allá de la verificación de puertos, sirve para manejo de red)
from flask import Flask, jsonify, render_template, request # Importa las clases necesarias de Flask para crear la API web y renderizar HTML

# Importamos la lógica de sockets consolidada desde el archivo "socket_manager.py"
from socket_manager import (
    get_client_id,           # Función para obtener la IP de este cliente
    set_web_port,            # Función para compartir el puerto web usado a los demás archivos
    join_multicast_group,    # Función para unirse a un grupo Multicast
    leave_multicast_group,   # Función para salirse de un grupo Multicast
    joined_groups,           # Variable (set) que guarda los grupos a los que estamos unidos
    known_members,           # Diccionario que guarda los miembros conocidos (peers)
    messages,                # Lista que guarda todos los mensajes del chat
    send_message,            # Función para enviar un mensaje (Unicast, Multicast, etc.)
    start_listener_threads,  # Función que inicia los hilos para escuchar mensajes entrantes
    get_current_hostname,    # Función para obtener el nombre de usuario actual
    set_custom_hostname      # Función para actualizar el nombre de usuario actual
)

app = Flask(__name__) # Inicializa la aplicación Flask con el nombre del módulo actual

@app.route("/") # Define la ruta raíz de la aplicación web (la página principal)
def index():
    local_ip = get_client_id() # Obtiene la dirección IP local de este cliente
    hostname = get_current_hostname() # Obtiene el nombre de usuario configurado actualmente
    # Renderiza la plantilla "index.html" enviando mensajes, IP local y hostname para que se muestren
    return render_template(
        "index.html", messages=messages, local_ip=local_ip, hostname=hostname
    )

@app.route("/mensajes") # Define la ruta para obtener solo los mensajes (usado para actualizar el chat en vivo)
def get_messages():
    # Renderiza "mensajes.html", que es solo un fragmento de HTML con los mensajes renderizados
    return render_template("mensajes.html", messages=messages)

@app.route("/estado") # Ruta de la API que retorna el estado actual (grupos unidos y miembros descubiertos)
def get_estado():
    # Retorna un JSON con los grupos actuales (convertidos a lista) y los miembros conocidos
    return jsonify({"grupos": list(joined_groups), "miembros": known_members})

@app.route("/enviar", methods=["POST"]) # Ruta que se encarga de procesar los mensajes enviados por el usuario
def handle_send_message():
    mode = request.form.get("mode") # Obtiene el modo de envío del formulario (ej. 'unicast', 'broadcast')
    dest_ip = request.form.get("ip") # Obtiene la IP de destino del formulario
    message_text = request.form.get("message") # Obtiene el texto del mensaje a enviar
    protocol = request.form.get("protocol", "TCP") # Obtiene el protocolo (por defecto TCP si no viene en el form)
    
    if mode and message_text: # Se asegura de que haya un modo y un mensaje válidos
        if mode == "broadcast": # Si el modo es broadcast (enviar a todos)
            dest_ip = "" # Vacía la IP de destino porque no aplica a un usuario particular
        # Llama a la función de socket_manager para realizar el envío a nivel de red
        send_message(mode, dest_ip, message_text, protocol)
        
    return jsonify({"status": "ok"}) # Retorna respuesta exitosa a la web

@app.route("/join_group", methods=["POST"]) # Ruta para manejar cuando un usuario se une a un grupo Multicast
def handle_join_group():
    group_ip = request.form.get("ip") # Obtiene la IP del grupo (ej. 224.x.x.x)
    invitees = request.form.getlist("invitees") # Obtiene la lista de usuarios que se quieran invitar al grupo
    if group_ip: # Si se proporcionó una IP
        # Llama a socket_manager para ejecutar la lógica de suscripción
        success, msg = join_multicast_group(group_ip, invitees)
        if success: # Si tuvo éxito la suscripción
            return jsonify({"status": "ok", "message": msg}) # Retorna un JSON exitoso
        else:
            return jsonify({"status": "error", "message": msg}), 400 # Si falló, retorna error con código HTTP 400
    return jsonify({"status": "error", "message": "IP no proporcionada"}), 400 # Falla por no tener IP

@app.route("/leave_group", methods=["POST"]) # Ruta para salirse de un grupo de chat
def handle_leave_group():
    group_ip = request.form.get("group") # Obtiene el ID/IP del grupo del cual salir
    if group_ip: # Si hay una IP válida
        success = leave_multicast_group(group_ip) # Ejecuta el abandono en socket_manager
        if success:
            return jsonify({"status": "ok"}) # Si fue exitoso, devuelve status ok
    return jsonify({"status": "error"}), 400 # Si algo falló, devuelve error HTTP 400

@app.route("/set_hostname", methods=["POST"]) # Ruta que permite cambiar el nombre del usuario
def handle_set_hostname():
    new_name = request.form.get("hostname") # Toma el nombre nuevo del formulario
    if new_name: # Si hay texto para el nuevo nombre
        set_custom_hostname(new_name) # Cambia el hostname en socket_manager
        return jsonify({"status": "ok", "message": "Nombre actualizado"}) # Notifica que se actualizó
    return jsonify({"status": "error", "message": "Nombre no proporcionado"}), 400 # Error si viene vacío

if __name__ == "__main__": # Este bloque se ejecuta solo si el script se inicia directamente
    import socket as sckt # Importamos socket con alias para usarlo localmente y verificar puertos
    
    port = 5000 # Definimos 5000 como el puerto inicial que queremos usar para la web
    while True: # Bucle para intentar conseguir un puerto libre
        try:
            # Intenta crear un socket TCP rápido en la interfaz local con el puerto actual
            with sckt.socket(sckt.AF_INET, sckt.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port)) # Intenta enlazarse. Si falla, el puerto está ocupado
                break # Si tiene éxito, sale del bucle, confirmando que este puerto está libre
        except OSError: # Si salta OSError es porque el puerto está usado
            port += 1 # Incrementa en 1 e intenta de nuevo (ej. pasará a 5001)
            
    set_web_port(port) # Le dice a socket_manager cuál fue el puerto final para la interfaz web (útil por si se cambió)
    start_listener_threads() # Inicia los hilos en segundo plano que escuchan los mensajes entrantes (TCP y UDP)
    print(f"[*] Iniciando servidor web Flask en puerto {port}...") # Imprime a terminal la inicialización
    print(f"[*] Accede a http://localhost:{port} desde el navegador.") # Da instrucciones al usuario de dónde entrar
    # Inicia la aplicación Flask para escuchar en todas las interfaces de red ('0.0.0.0') en el puerto hallado
    app.run(host="0.0.0.0", port=port, debug=False)
