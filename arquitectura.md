# Arquitectura del Sistema: Socket-Web Bridge Multi-Protocolo

## 1. Estructura del Proyecto (Modular)
El proyecto ha sido diseñado para separar responsabilidades en distintos archivos y directorios:
```text
Tarea7/
├── app.py                 # Inicialización de Flask y enrutamiento (API y render_template).
├── socket_manager.py      # Lógica core: Listeners TCP/UDP, envíos y estado en memoria.
├── scripts_red/           # Scripts .bat para abrir/cerrar el firewall en Windows.
├── static/
│   ├── css/
│   │   └── style.css      # Estilos visuales (modo claro/oscuro, flexbox panels).
│   └── js/
│       └── chat.js        # Lógica de cliente: Polling, cambio de salas y notificaciones.
└── templates/
    ├── index.html         # Plantilla base (layout, formularios de chat y grupos).
    └── mensajes.html      # Fragmento HTML renderizado por Jinja para la lista de mensajes.
```

## 2. Capa de Presentación (Frontend)
+ *Interfaz*: Documento HTML dinámico. Se compone de un diseño en 3 paneles principales: Lista de mensajes, Selector de Chats y Controles de envío.
+ *Componentes Clave*:
  + **Gestor de Salas (chat.js):** Controla qué "chat" (Unicast, Multicast, o Broadcast) está activo en el DOM filtrando dinámicamente el HTML recibido.
  + **Notificaciones:** Un sistema local en el cliente rastrea los incrementos en la lista de mensajes (por `chat_id`) para renderizar "burbujas" rojas de no leídos en chats inactivos.
+ *Mecanismo de Actualización*:
  + *Polling Asíncrono Dual*: `chat.js` ejecuta `setInterval()` hacia dos endpoints:
    1. `/mensajes`: Obtiene todo el historial HTML de mensajes. El cliente se encarga de filtrar y mostrar solo los que corresponden al grupo seleccionado.
    2. `/estado`: Obtiene en JSON la lista actualizada de grupos multicast a los que se ha unido y los miembros descubiertos en la red.

## 3. Capa de Aplicación (Backend - Flask)
+ *Servidor Web Local:* Instancia de Flask (`app.py`) expuesta en `0.0.0.0:5000`.
+ *Estructuras de Datos (en `socket_manager.py`):*
  + `messages`: Lista de diccionarios `{"chat_id": str, "html": str}` que representa todo el historial global.
  + `joined_groups`: `set` para evitar unirse múltiples veces a la misma IP multicast.
  + `known_members`: Diccionario anidado que mapea las IPs detectadas y sus hostnames a cada grupo.
+ *Endpoints:*
  + `GET /:` Interfaz principal.
  + `GET /mensajes:` Renderiza `mensajes.html`.
  + `GET /estado:` Retorna la topología conocida (grupos y miembros) en formato JSON.
  + `POST /enviar:` Procesa el envío despachando a la función correspondiente en sockets.
  + `POST /join_group:` Ejecuta la llamada a sistema a nivel de socket para suscribir la interfaz de red a un grupo Multicast IP.

## 4. Capa de Concurrencia (Gestión de Procesos)
+ Modelo Multi-hilos (Threading):
  + **Hilo Principal:** Ejecuta el servidor Flask (Web UI).
  + **Hilo TCP (Daemon):** Un proceso secundario ejecutando `tcp_listener()` dedicado en exclusiva a recibir conexiones 1-a-1 (Unicast/Anycast).
  + **Hilo UDP (Daemon):** Un proceso secundario ejecutando `udp_listener()` dedicado a recibir y procesar datagramas de difusión general (Broadcast) o de suscripción (Multicast).

## 5. Capa de Comunicación (Redes - Sockets Crudos)
El backend opera a nivel de transporte y red sin depender de servidores MQTT/WebSockets externos.
+ **Modos de Direccionamiento Soportados:**
  + **Unicast & Anycast (TCP):** Se utiliza `socket.SOCK_STREAM`. Garantiza entrega directa P2P para mensajes privados.
  + **Broadcast (UDP):** Se utiliza `socket.SOCK_DGRAM` con el flag `SO_BROADCAST`. El script calcula matemáticamente la dirección de *Directed Broadcast* leyendo la máscara de subred del SO mediante llamadas a `subprocess` para evitar enviar datagramas nulos `255.255.255.255` que algunos routers modernos bloquean.
  + **Multicast (UDP):** Se utiliza `socket.SOCK_DGRAM`. Usa IGMP (Internet Group Management Protocol) subyacente del SO. Configura opciones a nivel IP (`socket.IPPROTO_IP`) como `IP_ADD_MEMBERSHIP` para suscribirse, `IP_MULTICAST_TTL` para el alcance, y define explícitamente `IP_MULTICAST_IF` para forzar la salida por la interfaz correcta.
+ **Formato del Payload:** Para permitir descubrimiento automático de miembros, se abandonó el texto plano en favor de enviar un JSON codificado en UTF-8 conteniendo `{"hostname", "message", "group"}` en cada envío de socket.

---
# Resumen del Stack Técnico
+ *Lenguaje:* Python 3.8+
+ *Micro-framework:* Flask.
+ *Networking:* `socket`, `struct`, `ipaddress`.
+ *Concurrencia:* `threading`.
+ *Cliente:* Vanilla JS (`fetch` API), CSS3 (Flexbox).
