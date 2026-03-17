import socket
import threading

from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

# Lista global para almacenar los mensajes de chat
messages = []

# Puerto para la comunicación raw TCP
PORT = 65432

# Plantilla HTML para la interfaz de chat (en lugar de un archivo externo por simplicidad)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Chat TCP</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f4f9; color: #333; }
        h1 { color: #5a5a5a; }
        #chat-box {
            border: 1px solid #ccc;
            background: #fff;
            padding: 15px;
            height: 350px;
            overflow-y: scroll;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .message { margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        .error { color: red; font-weight: bold; }
        .self { color: blue; }
        .other { color: green; }

        .form-group { margin-bottom: 15px; }
        label { display: inline-block; width: 100px; }
        input[type="text"] { padding: 5px; width: 250px; border: 1px solid #ccc; border-radius: 3px; }
        button { padding: 8px 15px; background: #007BFF; color: white; border: none; border-radius: 3px; cursor: pointer; }
        button:hover { background: #0056b3; }
    </style>
    <script>
        // Polling usando fetch para no interrumpir la escritura en el formulario
        setInterval(function() {
            fetch('/mensajes')
                .then(response => response.text())
                .then(html => {
                    const chatBox = document.getElementById('chat-box');
                    // Solo auto-scrollear si estábamos cerca del final
                    const isScrolledToBottom = chatBox.scrollHeight - chatBox.clientHeight <= chatBox.scrollTop + 50;
                    chatBox.innerHTML = html;
                    if (isScrolledToBottom) {
                        chatBox.scrollTop = chatBox.scrollHeight;
                    }
                })
                .catch(err => console.error("Error en polling:", err));
        }, 2000);

        // Hacer scroll automático hacia abajo al cargar la página por primera vez
        window.onload = function() {
            const chatBox = document.getElementById('chat-box');
            chatBox.scrollTop = chatBox.scrollHeight;
        };
    </script>
</head>
<body>
    <h1>Chat TCP via Flask</h1>

    <div id="chat-box">
        {% for msg in messages %}
            <div class="message">{{ msg|safe }}</div>
        {% else %}
            <div class="message"><i>No hay mensajes aún. ¡Comienza a chatear!</i></div>
        {% endfor %}
    </div>

    <form action="/enviar" method="post">
        <div class="form-group">
            <label for="ip">IP Destino:</label>
            <input type="text" id="ip" name="ip" required value="127.0.0.1" placeholder="Ej. 192.168.1.10">
        </div>
        <div class="form-group">
            <label for="message">Mensaje:</label>
            <input type="text" id="message" name="message" required autofocus autocomplete="off" placeholder="Escribe tu mensaje aquí...">
        </div>
        <button type="submit">Enviar Mensaje</button>
    </form>
</body>
</html>
"""


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


@app.route("/")
def index():
    """
    Ruta principal para mostrar la interfaz web del chat.
    """
    # Renderizamos la plantilla HTML en línea, pasando la lista de mensajes
    return render_template_string(HTML_TEMPLATE, messages=messages)


@app.route("/mensajes")
def get_messages():
    """
    Ruta para el polling desde el frontend (JS fetch).
    Retorna solo el HTML de los mensajes.
    """
    template = """
    {% for msg in messages %}
        <div class="message">{{ msg|safe }}</div>
    {% else %}
        <div class="message"><i>No hay mensajes aún. ¡Comienza a chatear!</i></div>
    {% endfor %}
    """
    return render_template_string(template, messages=messages)


@app.route("/enviar", methods=["POST"])
def send_message():
    """
    Ruta que maneja el envío de mensajes desde el formulario web.
    """
    dest_ip = request.form.get("ip")
    message_text = request.form.get("message")

    if dest_ip and message_text:
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
            formatted_msg = (
                f'<span class="self">[Tú -> {dest_ip}]</span> {message_text}'
            )
            messages.append(formatted_msg)

        except socket.timeout:
            error_msg = f'<span class="error">[Error timeout conectando a {dest_ip}]</span> El destino no responde.'
            messages.append(error_msg)
        except Exception as e:
            error_msg = f'<span class="error">[Error enviando a {dest_ip}]</span> {e}'
            messages.append(error_msg)

    # Redirigir de vuelta al inicio
    return redirect(url_for("index"))


if __name__ == "__main__":
    # 1. Iniciar el hilo del listener TCP antes de Flask
    # daemon=True permite que el hilo se cierre cuando el programa principal termine
    listener_thread = threading.Thread(target=tcp_listener, daemon=True)
    listener_thread.start()

    # 2. Iniciar el servidor web Flask
    print("[*] Iniciando servidor web Flask...")
    # debug=False es recomendado cuando se usan hilos adicionales para evitar que se ejecuten doble vez (por el reloader de Werkzeug)
    app.run(host="0.0.0.0", port=5000, debug=False)
