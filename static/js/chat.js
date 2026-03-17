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
