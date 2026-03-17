# Arquitectura del Sistema: Socket-Web Bridge (Chat Inter-procesos)

## 1. Estructura del Proyecto (Modular)
El proyecto ha sido refactorizado para separar responsabilidades en distintos archivos y directorios:
```text
Tarea7/
├── app.py                 # Solo inicialización de Flask y rutas (render_template).
├── socket_manager.py      # Listener TCP, sender TCP y lista global 'messages'.
├── static/
│   ├── css/
│   │   └── style.css      # Estilos visuales.
│   └── js/
│       └── chat.js        # Lógica de fetch() polling y auto-scroll.
└── templates/
    ├── index.html         # Plantilla base (formulario y carga de estáticos).
    └── mensajes.html      # Solo el loop for de Jinja para los mensajes.
```

## 2. Capa de Presentación (Frontend)
+ *Interfaz*: Documento HTML dinámico renderizado por el servidor usando Jinja2 (`templates/`) y archivos estáticos (`static/`).
+ *Componentes*:
  + Área de historial de mensajes con scroll automático (gestionado por `chat.js`).
  + Formulario de entrada de texto (`<input>`) y botón de envío.
+ *Mecanismo de Actualización*: * *Estrategia*: Polling asíncrono en segundo plano mediante `fetch()` en JavaScript (`chat.js`) que consulta un endpoint específico para actualizar únicamente el área (frame) del historial de mensajes tanto entrantes como salientes, sin recargar la página entera (para evitar borrar el texto que se está escribiendo en el `<input>`).

## 3. Capa de Aplicación (Backend - Flask)
+ *Servidor Web Local:* Instancia de Flask (`app.py`) corriendo en `localhost:5000`.
+ *Gestión de Estado:* Estructura de datos tipo `list` (hilo-segura para lecturas) que almacena los mensajes en memoria (RAM), gestionada centralizadamente en `socket_manager.py`.
+ *Endpoints:*
  + `GET /:` Retorna el HTML principal inicial de la interfaz web (`index.html`).
  + `GET /mensajes:` Retorna el fragmento HTML exclusivo del historial de mensajes (`mensajes.html`, consumido por el `fetch()`).
  + `POST /enviar:` Captura el mensaje del usuario y dispara el *Cliente de Sockets* delegando la tarea a `socket_manager.py`.

## 4. Capa de Concurrencia (Gestión de Procesos)
+ Modelo Multi-hilos (Threading):
  + Hilo A (Principal): Ejecuta el servidor Flask y atiende las peticiones del navegador.
  + Hilo B (Daemon): Un proceso en segundo plano (iniciado por `start_listener_thread` en `socket_manager.py`) que mantiene el socket en estado `LISTEN` perpetuo para no bloquear la interfaz web.

## 5. Capa de Comunicación (Redes - Sockets Crudos)
*Protocolo:* TCP sobre IPv4.
+ *Componente Servidor (Receiver):*
  + Usa `socket.bind()` y `socket.accept()` dentro de `tcp_listener()`.
  + Decodifica bytes a UTF-8 y actualiza la lista compartida en el Hilo A.
+ *Componente Cliente (Sender):*
  + Se activa solo al enviar un mensaje mediante la función `send_tcp_message()`.
  + Usa `socket.connect()` a la IP de la máquina remota y cierra la conexión tras el `sendall()`.

---
# Resumen del Stack Técnico
+ *Lenguaje:* Python 3.12+
+ *Framework:* Flask (Micro-framework).
+ *Librerías Core:* socket (Network IPC), threading (Concurrency).

## 6. Requisitos de Comunicación de Red
+ El programa debe soportar múltiples modos de direccionamiento:
  + **Unicast:** Envío de mensajes a un único destinatario.
  + **Broadcast:** Difusión de mensajes a todos los nodos en la red local.
  + **Multicast:** Envío de mensajes a un grupo específico de destinatarios interesados.
  + **Anycast:** Envío de mensajes al nodo más cercano o accesible dentro de un grupo.

