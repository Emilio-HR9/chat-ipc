from flask import Flask, redirect, render_template, request, url_for

from socket_manager import messages, send_tcp_message, start_listener_thread

app = Flask(__name__)


@app.route("/")
def index():
    """
    Ruta principal para mostrar la interfaz web del chat.
    """
    # Renderizamos la plantilla HTML usando el template engine
    return render_template("index.html", messages=messages)


@app.route("/mensajes")
def get_messages():
    """
    Ruta para el polling desde el frontend (JS fetch).
    Retorna solo el HTML de los mensajes.
    """
    return render_template("mensajes.html", messages=messages)


@app.route("/enviar", methods=["POST"])
def send_message():
    """
    Ruta que maneja el envío de mensajes desde el formulario web.
    """
    dest_ip = request.form.get("ip")
    message_text = request.form.get("message")

    if dest_ip and message_text:
        send_tcp_message(dest_ip, message_text)

    # Redirigir de vuelta al inicio
    return redirect(url_for("index"))


if __name__ == "__main__":
    # 1. Iniciar el hilo del listener TCP antes de Flask
    start_listener_thread()

    # 2. Iniciar el servidor web Flask
    print("[*] Iniciando servidor web Flask...")
    # debug=False es recomendado cuando se usan hilos adicionales para evitar
    # que se ejecuten doble vez (por el reloader de Werkzeug)
    app.run(host="0.0.0.0", port=5000, debug=False)
