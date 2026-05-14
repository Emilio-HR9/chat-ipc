# Guía de Usuario: Chat Multi-Modo con Interfaz Web

## 1. Descripción General

Esta aplicación es un sistema de chat que permite a los usuarios comunicarse a través de una red local utilizando múltiples esquemas de enrutamiento (Unicast, Broadcast, Multicast y Anycast). Utiliza una arquitectura "Socket-Web Bridge" bajo un modelo Cliente-Servidor:

*   **Servidor Central (`servidor.py`):** Actúa como router central enrutando mensajes por TCP y UDP hacia los clientes destino correspondientes, gestionando las desconexiones y grupos.
*   **Cliente Web (`app.py`):** Un servidor local escrito en Python con el micro-framework Flask que hace de puente entre los sockets y tu navegador.
*   **Frontend:** Una interfaz web moderna con soporte para múltiples salas de chat, notificaciones y modo oscuro.

La principal característica es que abstrae la complejidad de los sockets directos, permitiendo usar protocolos como UDP Multicast y TCP Anycast de forma transparente a través de un nodo central (el servidor).

> **Nota de Estudio:** El código fuente principal de este proyecto (`app.py`, `servidor.py`, `socket_manager.py`) está extensamente documentado y comentado línea por línea. Esto fue diseñado específicamente para facilitar el estudio y la comprensión técnica de la arquitectura de sockets y redes.

> Si buscas analizar y entender la estructura/arquitectura del código, te recomendamos leer `arquitectura.md`

## 2. Requisitos Previos

Antes de comenzar, asegúrate de tener instalado lo siguiente en tu sistema:

*   **Python:** Versión 3.8 o superior.
  * https://www.python.org/downloads/
*   **Pip:** El gestor de paquetes de Python (generalmente viene incluido con Python).
  * `python -m pip install pip` en terminal.
* **Flask (opcional):** Un microframework web para Python.
  * `pip install flask` para Instalar Flask de forma global.
  * ó en un entorno virtual: (recomendado, esto se hará en la siguiente sección)

## 3. Instalación

Sigue estos pasos para configurar el entorno del proyecto:

1.  **Clona o descarga el proyecto:** Si tienes Git, puedes clonar el repositorio. Si no, simplemente descarga y descomprime los archivos del proyecto en una carpeta.
    * Clonar el repositorio (recomendado):
      * `git clone https://github.com/Emilio-HR9/chat-ipc.git`
    * Descargar el proyecto (ZIP):
      * Descarga el archivo ZIP.
        * `https://github.com/Emilio-HR9/chat-ipc/archive/refs/heads/main.zip`
        * o directamente desde la página del repositorio con el botón "Code" verde en la parte superior.
      * Extrae el archivo ZIP en una carpeta de tu elección.
    
2.  **Navega a la carpeta del proyecto:**
    Abre una terminal o línea de comandos y muévete al directorio donde se encuentran los archivos del proyecto.
    ```bash
    cd ruta/a/tu/proyecto
    ```

3.  **Crea un entorno virtual (Recomendado):**
    Es una buena práctica aislar las dependencias del proyecto.
    ```bash
    python -m venv venv
    ```
    Y actívalo:
    *   En Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   En macOS y Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Instala las dependencias:**
    La única dependencia externa es Flask. Instálala usando pip:
    ```bash
    pip install Flask
    ```

## 4. Configuración de Red

Por defecto, la aplicación está configurada para probarse en la misma máquina (`127.0.0.1`). 
Si deseas usarla entre varias computadoras de una red local:

1. Averigua la dirección IP local de la computadora que hará de Servidor.
2. Abre el archivo `socket_manager.py`.
3. Modifica la variable `SERVER_IP` (actualmente configurada como `"192.168.43.140"` por defecto) reemplazándola con la IP actual de la computadora servidor.
4. Asegúrate de abrir el puerto `65432` en el Firewall de Windows usando los scripts incluidos en la carpeta `scripts_red`.

## 5. Cómo Ejecutar la Aplicación

Para que el sistema funcione, necesitas iniciar tanto el servidor central como al menos un cliente.

**Paso 1: Iniciar el Servidor Central**
Abre una terminal y ejecuta:
```bash
python servidor.py
```
Verás un mensaje indicando que el servidor ha iniciado en el puerto 65432. Déjalo corriendo.

**Paso 2: Iniciar el Cliente Web**
Abre *otra* terminal (o abre terminales en otras computadoras si configuraste la IP de red) y ejecuta:
```bash
python app.py
```

Verás una salida similar a esta:
```
[*] Iniciando servidor web Flask en puerto 5000...
[*] Accede a http://localhost:5000 desde el navegador.
```

## 6. Cómo Usar el Chat

Para probar el chat, asegúrate de que `servidor.py` esté corriendo y luego inicia tantas instancias de `app.py` como desees (si las inicias en la misma máquina, cada `app.py` tomará un puerto web diferente automáticamente, ej. 5000, 5001, 5002...).

1.  **Abre un navegador web** y accede al puerto que te indicó la consola, por ejemplo:
    ```
    http://localhost:5000
    ```

### La Interfaz

*   **Panel Central (Mensajes):** Muestra los mensajes de la conversación que tienes seleccionada actualmente.
*   **Panel Derecho (Chats):** Muestra todos los chats disponibles:
    *   **Broadcast (🌍):** Un canal general donde todos los clientes conectados pueden leer y escribir.
    *   **Grupos Multicast (👥):** Canales específicos a los que puedes unirte para hablar con un subgrupo de usuarios.
    *   **Usuarios (👤):** Conversaciones directas (Unicast/Anycast) con usuarios específicos.
*   **Panel Inferior (Envío):**
    *   **Modo:** Selecciona cómo quieres enviar tu mensaje (Unicast, Broadcast, Multicast, Anycast).
    *   **Protocolo:** Permite forzar el envío usando TCP (seguro) o UDP (rápido).
    *   **IP Destino:** La IP del usuario (Unicast) o del grupo (Multicast).
    *   **Mensaje:** Tu texto a enviar.

### Funciones Principales

*   **Chat General (Broadcast):** Selecciona "Broadcast" en el panel derecho. El servidor retransmitirá el mensaje a todos los clientes.
*   **Unirse a un Grupo (Multicast):** En la parte inferior del panel derecho, ingresa un nombre o IP Multicast (ej. `224.1.1.2`) y haz clic en "Unirse". Se creará un canal privado manejado por el servidor.
*   **Mensajes Privados (Unicast):** Escribe un mensaje indicando la IP destino en el panel inferior, selecciona "Unicast" y envíalo.
*   **Mensaje Aleatorio (Anycast):** Selecciona "Anycast", y el servidor le entregará el mensaje a un solo usuario al azar de la red.
*   **Notificaciones:** Cuando recibas un mensaje en un chat que no estás viendo, aparecerá una burbuja roja en el panel derecho.
