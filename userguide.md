# Guía de Usuario: Chat TCP con Interfaz Web

## 1. Descripción General

Esta aplicación es un sistema de chat punto a punto (P2P) que permite a los usuarios comunicarse directamente con otros a través de una red local. Utiliza una arquitectura "Socket-Web Bridge":

*   **Backend:** Un servidor web local escrito en Python con el micro-framework Flask.
*   **Frontend:** Una interfaz web simple y limpia para enviar y recibir mensajes.
*   **Comunicación:** Se basa en sockets TCP crudos para el intercambio de mensajes entre las máquinas de los usuarios.

La principal característica es que no depende de un servidor central para retransmitir mensajes. Cuando envías un mensaje, tu computadora establece una conexión TCP directa con la computadora del destinatario.

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

## 4. Cómo Ejecutar la Aplicación

Para iniciar el servidor de chat, ejecuta el siguiente comando en la terminal desde la carpeta del proyecto:

```bash
python app.py
```

Verás una salida similar a esta, lo que indica que el servidor está funcionando correctamente:

```
[*] Hilo TCP: Escuchando mensajes en el puerto 65432...
[*] Iniciando servidor web Flask...
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
```

## 5. Cómo Usar el Chat

Para probar el chat, necesitarás al menos dos computadoras (o puedes probarlo en una sola usando la IP de localhost `127.0.0.1`).

1.  **Inicia la aplicación en ambas máquinas** siguiendo los pasos de la sección "Cómo Ejecutar la Aplicación".

2.  **Abre un navegador web** (como Chrome, Firefox, etc.) en cada máquina.

3.  **Accede a la interfaz del chat** visitando la siguiente dirección en la barra de URL del navegador:
    ```
    http://localhost:5000
    ```
    o
    ```
    http://<la-IP-de-tu-maquina>:5000
    ```

4.  **Identifica las direcciones IP:**
    Cada usuario necesita conocer la dirección IP de la máquina a la que desea enviar un mensaje. Puedes encontrar la IP de tu máquina usando comandos como `ipconfig` en Windows o `ifconfig` / `ip addr` en macOS/Linux.

5.  **Envía un mensaje:**
    *   En el campo **"IP Destino"**, introduce la dirección IP de la otra máquina.
    *   En el campo **"Mensaje"**, escribe lo que quieras decir.
    *   Haz clic en el botón **"Enviar Mensaje"**.

6.  **Recibe mensajes:**
    Cuando alguien te envíe un mensaje, aparecerá automáticamente en el área del historial del chat. La interfaz se actualiza cada 2 segundos para mostrar los nuevos mensajes.

¡Y eso es todo! Ahora puedes chatear directamente con otros usuarios en tu red local.
