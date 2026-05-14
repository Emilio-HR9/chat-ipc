# 💬 Guía de Instalación Rápida del Chat

¡Hola! Esta es una guía paso a paso para que cualquier persona, sin importar si sabe de programación o no, pueda instalar y usar esta aplicación de chat en su computadora.

---

## 🛠️ Paso 1: Instalar Python

El chat necesita un programa llamado "Python" para poder funcionar. Si ya lo tienes, puedes saltar este paso.

1. Ve a la página oficial de descargas: [python.org/downloads](https://www.python.org/downloads/)
2. Haz clic en el botón amarillo que dice **"Download Python"**.
3. Abre el archivo que se descargó.
4. **¡MUY IMPORTANTE!** En la primera pantalla de instalación, asegúrate de marcar la casilla en la parte de abajo que dice **"Add python.exe to PATH"** (o "Agregar Python al PATH").
5. Haz clic en **"Install Now"** y espera a que termine.

---

## 📥 Paso 2: Descargar el Chat

1. Ve a la página de este proyecto en GitHub: [https://github.com/Emilio-HR9/chat-ipc](https://github.com/Emilio-HR9/chat-ipc)
2. Haz clic en el botón verde de la derecha que dice **"<> Code"**.
3. En el pequeño menú que se abre, selecciona **"Download ZIP"**.
4. Se descargará un archivo comprimido. Búscalo en tu carpeta de Descargas.
5. Haz clic derecho sobre el archivo ZIP y selecciona **"Extraer todo..."** (o "Extract All").
6. Elige una carpeta fácil de encontrar, como tu Escritorio o tus Documentos, y extrae los archivos allí.

---

## ⚙️ Paso 3: Instalar un pequeño requisito

El chat necesita una pequeña herramienta llamada "Flask" para mostrar la página web. Instalarla es muy fácil:

1. Abre la carpeta donde extrajiste los archivos del chat (deberías ver archivos adentro como `app.py`, `servidor.py`, etc.).
2. Haz clic en la **barra de direcciones** de la carpeta (en la parte superior de la ventana, donde dice la ruta de la carpeta).
3. Borra todo lo que dice ahí, escribe la palabra `cmd` y presiona **Enter**.
4. Se abrirá una ventana negra. Escribe exactamente lo siguiente y presiona **Enter**:
   ```
   pip install Flask
   ```
5. Verás que se descargan algunas cosas. Cuando termine y vuelva a aparecer texto normal para escribir, puedes cerrar esa ventana negra.

---

## 🚀 Paso 4: ¡Iniciar el Chat!

Para que el chat funcione, necesitamos abrir dos cosas: el "Servidor Central" (que conecta los mensajes) y tu "Ventana de Chat".

**1. Encender el Servidor Central:**
1. En la carpeta del chat, haz doble clic en el archivo que se llama `servidor.py`.
2. Se abrirá una ventana negra que dirá algo como "Servidor IPC iniciado...". **No cierres esta ventana**, déjala abierta en el fondo para que el chat funcione.

**2. Abrir tu Ventana de Chat:**
1. Vuelve a la carpeta del chat y haz doble clic en el archivo que se llama `app.py`.
2. Se abrirá otra ventana negra que dirá "Iniciando servidor web Flask...". **Tampoco la cierres**.
3. Ahora, abre tu navegador de internet favorito (Chrome, Edge, Firefox, etc.).
4. En la barra de direcciones de arriba (donde normalmente escribes google.com), escribe esto y presiona Enter:
   ```
   http://localhost:5000
   ```
5. ¡Listo! Deberías estar viendo la pantalla del chat.

*(Si quieres probar el chat abriendo la cuenta de otra persona simulada en tu misma computadora, vuelve a hacer doble clic en `app.py` de nuevo. En la nueva ventana negra que se abre, fíjate qué dirección web te da, probablemente sea `http://localhost:5001`. Entra a esa dirección en tu navegador).*

---

## 🌐 Paso Extra: Chatear con otras computadoras en tu casa

Si quieres que alguien más en tu casa (conectado a tu mismo WiFi) se conecte a tu chat:

1. Elige una computadora para que sea el **Servidor Central**. En esa computadora, abre el menú inicio, busca "cmd" y ábrelo. Escribe `ipconfig` y presiona Enter. Busca donde dice **"Dirección IPv4"** (ejemplo: `192.168.1.15`) y anota ese número.
2. En los archivos del chat que descargaste, abre el archivo `socket_manager.py` (puedes usar el Bloc de Notas para abrirlo).
3. Busca la línea que dice `SERVER_IP = "..."` (está casi al principio del archivo) y cambia el número que está entre las comillas por el número que anotaste en el paso 1. Guarda el archivo.
4. Sigue el **Paso 4** normal en esa computadora principal (abrir `servidor.py` y luego `app.py`).
5. En las otras computadoras de tu casa, repite los pasos 1, 2 y 3 de esta guía (descargar Python, descargar el chat, instalar Flask y cambiar la IP en `socket_manager.py`).
6. En esas computadoras adicionales, **solo abre `app.py`** (no abras `servidor.py` porque ya lo abriste en la computadora principal). Y luego entra a `http://localhost:5000` en sus propios navegadores.