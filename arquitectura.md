# Arquitectura del Sistema: Socket-Web Bridge Multi-Protocolo

## 1. Estructura del Proyecto (Modular)
El proyecto ha sido diseñado para separar responsabilidades en distintos archivos y directorios utilizando un modelo Cliente-Servidor:
```text
chat-ipc/
├── servidor.py            # Servidor central: Enruta mensajes (TCP/UDP) y gestiona clientes y grupos.
├── app.py                 # Cliente (Backend): Inicialización de Flask y enrutamiento (API web local).
├── socket_manager.py      # Lógica core del cliente: Conexión al servidor central, Listeners TCP/UDP.
├── scripts_red/           # Scripts .bat para abrir/cerrar el firewall en Windows.
├── static/
│   ├── css/
│   │   └── style.css      # Estilos visuales (modo claro/oscuro, flexbox panels).
│   └── js/
│       └── chat.js        # Lógica de cliente (Frontend): Polling, cambio de salas y notificaciones.
└── templates/
    ├── index.html         # Plantilla base (layout, formularios de chat y grupos).
    └── mensajes.html      # Fragmento HTML renderizado por Jinja para la lista de mensajes.
```

## 2. Capa de Presentación (Frontend Web)
+ *Interfaz*: Documento HTML dinámico servido por `app.py`. Se compone de un diseño en 3 paneles principales: Lista de mensajes, Selector de Chats y Controles de envío.
+ *Componentes Clave*:
  + **Gestor de Salas (chat.js):** Controla qué "chat" (Unicast, Multicast, o Broadcast) está activo en el DOM filtrando dinámicamente el HTML recibido.
  + **Notificaciones:** Un sistema local en el cliente rastrea los incrementos en la lista de mensajes (por `chat_id`) para renderizar "burbujas" rojas de no leídos en chats inactivos.
+ *Mecanismo de Actualización*:
  + *Polling Asíncrono Dual*: `chat.js` ejecuta `setInterval()` hacia dos endpoints locales de Flask:
    1. `/mensajes`: Obtiene todo el historial HTML de mensajes. El cliente web filtra y muestra solo los que corresponden al grupo seleccionado.
    2. `/estado`: Obtiene en JSON la lista actualizada de grupos a los que se ha unido y los miembros descubiertos.

## 3. Capa de Aplicación (Backend del Cliente - Flask)
+ *Servidor Web Local:* Instancia de Flask (`app.py`) expuesta en `0.0.0.0:5000` (o superior). Actúa como puente entre la web y los sockets.
+ *Estructuras de Datos (en `socket_manager.py`):*
  + `messages`: Lista de diccionarios `{"chat_id": str, "html": str}` que representa el historial.
  + `joined_groups`: `set` que almacena los grupos multicast actuales.
  + `known_members`: Diccionario anidado que mapea las IPs detectadas y sus hostnames.
+ *Endpoints de la API Local:*
  + `GET /:` Interfaz principal.
  + `GET /mensajes:` Renderiza el fragmento de chat activo.
  + `GET /estado:` Retorna grupos y miembros en JSON.
  + `POST /enviar:` Procesa el envío llamando a la función correspondiente en sockets.
  + `POST /join_group:` Se registra en un grupo a nivel lógico enviando un payload al servidor central.

## 4. Capa de Concurrencia (Gestión de Hilos del Cliente)
+ Modelo Multi-hilos (Threading) en el cliente (`socket_manager.py`):
  + **Hilo Principal:** Ejecuta el servidor web Flask en `app.py`.
  + **Hilo TCP (`connect_to_server`):** Mantiene la conexión constante con el servidor central, recibe confirmaciones, mensajes Unicast, Multicast y Anycast vía TCP.
  + **Hilo UDP (`listen_udp`):** Escucha mensajes que llegan por datagramas UDP (Broadcast y Multicast de alta velocidad).
  + **Hilo de Descubrimiento (`discovery_broadcaster`):** Envía periódicamente "ping" (heartbeats) al servidor para anunciar que el cliente y sus rutas siguen activos.

## 5. Capa de Comunicación (Servidor Central - `servidor.py`)
A diferencia de un modelo P2P puro, este sistema utiliza un servidor central (`servidor.py`) que hace de router o hub para todos los clientes, permitiendo superar restricciones de red (como el bloqueo de multicast/broadcast en algunos routers).
+ **Modos de Enrutamiento Soportados por el Servidor:**
  + **Unicast (TCP/UDP):** Entrega directa. El servidor busca la IP destino en su diccionario de `clientes_registrados` y reenvía el paquete solo a ese socket.
  + **Multicast (TCP/UDP):** El servidor mantiene un diccionario `grupos` con las suscripciones. Cuando llega un mensaje a un grupo, el servidor lo duplica y reenvía a todos los miembros de ese grupo.
  + **Broadcast (TCP/UDP):** El servidor itera sobre todos los clientes registrados y reenvía el mensaje a todos (excepto al remitente original).
  + **Anycast (TCP/UDP):** El servidor elige aleatoriamente un cliente del pool de conectados y le entrega el mensaje en exclusiva, enviando un "acuse de recibo" (`anycast_receipt`) al remitente para informarle quién lo recibió.
+ **Formato del Payload:** JSON codificado en UTF-8 conteniendo campos como `{"type", "hostname", "message", "group", "mode", "sender_ip"}`.

---
# Resumen del Stack Técnico
+ *Lenguaje:* Python 3.8+
+ *Micro-framework:* Flask.
+ *Networking:* `socket` puro (TCP `SOCK_STREAM` y UDP `SOCK_DGRAM`).
+ *Concurrencia:* `threading`.
+ *Cliente:* Vanilla JS (`fetch` API), CSS3 (Flexbox).

---
## 6. Documentación de Código
Los archivos core del proyecto (`app.py`, `servidor.py`, y `socket_manager.py`) han sido comentados línea por línea de manera exhaustiva. El propósito principal de estas anotaciones es servir como material de estudio didáctico para comprender a fondo la implementación técnica, la lógica de red (TCP/UDP), la concurrencia con hilos, y los mecanismos de enrutamiento de mensajes.
