import socket

from flask import Flask, jsonify, render_template, request

from socket_manager import (
    get_local_ip,
    join_multicast_group,
    joined_groups,
    known_members,
    messages,
    send_message,
    start_listener_threads,
)

app = Flask(__name__)


@app.route("/")
def index():
    """
    Ruta principal para mostrar la interfaz web del chat.
    """
    local_ip = get_local_ip()
    hostname = socket.gethostname()
    return render_template(
        "index.html", messages=messages, local_ip=local_ip, hostname=hostname
    )


@app.route("/mensajes")
def get_messages():
    """
    Ruta para el polling desde el frontend (JS fetch).
    Retorna solo el HTML de los mensajes.
    """
    return render_template("mensajes.html", messages=messages)


@app.route("/estado")
def get_estado():
    """
    Ruta para el polling desde el frontend de grupos y miembros conocidos.
    """
    return jsonify({"grupos": list(joined_groups), "miembros": known_members})


@app.route("/enviar", methods=["POST"])
def handle_send_message():
    """
    Ruta que maneja el envío de mensajes desde el formulario web.
    """
    mode = request.form.get("mode")
    dest_ip = request.form.get("ip")
    message_text = request.form.get("message")

    if mode and message_text:
        # La IP de destino no es necesaria para broadcast
        if mode == "broadcast":
            dest_ip = ""
        send_message(mode, dest_ip, message_text)

    return jsonify({"status": "ok"})


@app.route("/join_group", methods=["POST"])
def handle_join_group():
    """
    Ruta para unirse a un nuevo grupo multicast.
    """
    group_ip = request.form.get("ip")
    if group_ip:
        success, msg = join_multicast_group(group_ip)
        if success:
            return jsonify({"status": "ok", "message": msg})
        else:
            return jsonify({"status": "error", "message": msg}), 400
    return jsonify({"status": "error", "message": "IP no proporcionada"}), 400


if __name__ == "__main__":
    # 1. Iniciar los hilos de los listeners (TCP y UDP)
    start_listener_threads()

    # 2. Iniciar el servidor web Flask
    print("[*] Iniciando servidor web Flask...")
    app.run(host="0.0.0.0", port=5000, debug=False)
