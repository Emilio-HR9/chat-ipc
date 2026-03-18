# Guía de Usuario: Chat Multi-Modo con Interfaz Web

## 1. Descripción General

Esta aplicación es un sistema de chat local que permite a los usuarios comunicarse a través de una red local utilizando múltiples esquemas de enrutamiento (Unicast, Broadcast, Multicast y Anycast). Utiliza una arquitectura "Socket-Web Bridge":

*   **Backend:** Un servidor web local escrito en Python con el micro-framework Flask.
*   **Frontend:** Una interfaz web moderna con soporte para múltiples salas de chat, notificaciones y modo oscuro.
*   **Comunicación:** Se basa en sockets en bruto (TCP para Unicast/Anycast y UDP para Broadcast/Multicast) para el intercambio de mensajes entre las máquinas.

La principal característica es que no depende de un servidor central para retransmitir mensajes; todas las conexiones son directas entre pares (P2P) o a través de grupos de red.

## 2. Requisitos Previos

Antes de comenzar, asegúrate de tener instalado lo siguiente en tu sistema:

*   **Python:** Versión 3.8 o superior.
*   **Pip:** El gestor de paquetes de Python (generalmente viene incluido con Python).

## 3. Instalación

Sigue estos pasos para configurar el entorno del proyecto:

1.  **Clona o descarga el proyecto:**
    Si tienes Git, puedes clonar el repositorio. Si no, simplemente descarga y descomprime los archivos del proyecto en una carpeta.

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

## 4. Configuración del Firewall (Usuarios de Windows)

Para que el chat funcione correctamente entre diferentes computadoras en la misma red (especialmente para recibir mensajes entrantes y usar Multicast/Broadcast), es **necesario abrir el puerto 65432** en el Firewall de Windows.

En la carpeta `scripts_red` se proporcionan dos utilidades para facilitar esto:

1.  **Para abrir los puertos:**
    *   Navega a la carpeta `scripts_red`.
    *   Haz clic derecho sobre el archivo `abrir_puertos.bat` y selecciona **"Ejecutar como administrador"**.
    *   El script creará las reglas necesarias en el Firewall para TCP y UDP.

2.  **Para cerrar los puertos (cuando termines de usar la app):**
    *   Navega a la carpeta `scripts_red`.
    *   Haz clic derecho sobre el archivo `cerrar_puertos.bat` y selecciona **"Ejecutar como administrador"**.
    *   El script eliminará las reglas creadas, manteniendo tu equipo seguro.

*(Usuarios de Linux/macOS: deberán abrir el puerto 65432 TCP/UDP en sus respectivos firewalls, ej. `ufw allow 65432` en Ubuntu).*

## 5. Cómo Ejecutar la Aplicación

Para iniciar el servidor de chat, ejecuta el siguiente comando en la terminal desde la carpeta del proyecto:

```bash
python app.py
```

Verás una salida similar a esta, indicando que los hilos de escucha y el servidor web están listos:

```
[*] Hilo TCP: Escuchando mensajes en el puerto 65432...
[*] Hilo UDP: Escuchando broadcasts y multicasts en el puerto 65432...
[*] Iniciando servidor web Flask...
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5000
```

## 6. Cómo Usar el Chat

Para probar el chat, necesitarás al menos dos computadoras en la misma red local con los puertos configurados (o puedes probarlo en una sola usando diferentes pestañas).

1.  **Inicia la aplicación** en las máquinas deseadas.
2.  **Abre un navegador web** y accede a:
    ```
    http://localhost:5000
    ```
    *(Si accedes desde otra máquina a tu servidor web, usa `http://<la-IP-de-tu-maquina>:5000`)*

### La Interfaz

*   **Panel Central (Mensajes):** Muestra los mensajes de la conversación que tienes seleccionada actualmente.
*   **Panel Derecho (Chats):** Muestra todos los chats disponibles:
    *   **Broadcast (🌍):** Un canal general donde todos los miembros de la subred pueden leer y escribir.
    *   **Grupos Multicast (👥):** Canales específicos a los que puedes unirte. Puedes hacer clic en la flecha de la pestaña para ver qué miembros han estado activos en ese grupo.
    *   **Usuarios (👤):** Conversaciones directas (Unicast) con usuarios específicos que te han enviado un mensaje o a los que les has enviado.
*   **Panel Inferior (Envío):**
    *   **Modo:** Selecciona cómo quieres enviar tu mensaje (Unicast, Broadcast, Multicast, Anycast). Al seleccionar un chat del panel derecho, este modo se auto-configura.
    *   **IP Destino:** La IP del usuario (Unicast) o del grupo (Multicast).
    *   **Mensaje:** Tu texto a enviar.

### Funciones Principales

*   **Chat General (Broadcast):** Selecciona "Broadcast" en el panel derecho. Cualquier mensaje que envíes aquí será recibido por todas las instancias del chat en tu red local.
*   **Unirse a un Grupo (Multicast):** En la parte inferior del panel derecho, ingresa una IP Multicast (por ejemplo, `224.1.1.2`) y haz clic en "Unirse". Esto creará un nuevo canal privado donde solo los suscritos a esa IP recibirán los mensajes.
*   **Mensajes Privados (Unicast):** Selecciona el modo "Unicast" en el panel inferior, introduce la IP del destino y envía un mensaje. Se creará automáticamente un nuevo chat directo con ese usuario.
*   **Notificaciones:** Cuando recibas un mensaje de un chat que no estás viendo en ese momento, aparecerá una burbuja roja en el panel derecho indicando cuántos mensajes nuevos tienes.