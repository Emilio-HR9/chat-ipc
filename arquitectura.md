# Arquitectura del Sistema: Socket-Web Bridge (Chat Inter-procesos)
## 1. Capa de Presentación (Frontend)
+ *Interfaz*: Documento HTML dinámico renderizado por el servidor.
+ *Componentes*:
  + Área de historial de mensajes con scroll automático.
  + Formulario de entrada de texto (`<input>`) y botón de envío.
+ *Mecanismo de Actualización*: * *Estrategia*: Polling asíncrono en segundo plano mediante `fetch()` en JavaScript que consulta un endpoint específico para actualizar únicamente el área (frame) del historial de mensajes tanto entrantes como salientes, sin recargar la página entera (para evitar borrar el texto que se está escribiendo en el `<input>`).

## 2. Capa de Aplicación (Backend - Flask)
+ *Servidor Web Local:* Instancia de Flask corriendo en `localhost:5000`.
+ *Gestión de Estado:* Estructura de datos tipo `list` (hilo-segura para lecturas) que almacena los mensajes en memoria (RAM).
+ *Endpoints:*
  + `GET /:` Retorna el HTML principal inicial de la interfaz web.
  + `GET /mensajes:` Retorna el fragmento HTML exclusivo del historial de mensajes (consumido por `fetch()` para actualizar el frame en tiempo real).
  + `POST /enviar:` Captura el mensaje del usuario y dispara el *Cliente de Sockets*.

## 3. Capa de Concurrencia (Gestión de Procesos)
+ Modelo Multi-hilos (Threading):
  + Hilo A (Principal): Ejecuta el servidor Flask y atiende las peticiones del navegador.
  + Hilo B (Daemon): Un proceso en segundo plano que mantiene el socket en estado `LISTEN` perpetuo para no bloquear la interfaz web.

## 4. Capa de Comunicación (Redes - Sockets Crudos)
*Protocolo:* TCP (o UDP, según elijas) sobre IPv4.
+ *Componente Servidor (Receiver):*
  + Usa `socket.bind()` y `socket.accept()`.
  + Decodifica bytes a UTF-8 y actualiza la lista compartida en el Hilo A.
+ Componente Cliente (Sender):
  + Se activa solo al enviar un mensaje.
  + Usa `socket.connect()` a la IP de la máquina remota y cierra la conexión tras el `sendall()`.

---
# Resumen del Stack Técnico
+ *Lenguaje:* Python 3.12+
+ *Framework:* Flask (Micro-framework).
+ *Librerías Core:* socket (Network IPC), threading (Concurrency).
