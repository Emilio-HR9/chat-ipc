// Polling usando fetch para no interrumpir la escritura en el formulario
setInterval(function () {
  fetch("/mensajes")
    .then((response) => response.text())
    .then((html) => {
      const chatBox = document.getElementById("chat-box");
      // Solo auto-scrollear si estábamos cerca del final
      const isScrolledToBottom =
        chatBox.scrollHeight - chatBox.clientHeight <= chatBox.scrollTop + 50;
      chatBox.innerHTML = html;
      if (isScrolledToBottom) {
        chatBox.scrollTop = chatBox.scrollHeight;
      }
    })
    .catch((err) => console.error("Error en polling:", err));
}, 2000);

// Hacer scroll automático hacia abajo al cargar la página por primera vez
window.onload = function () {
  const chatBox = document.getElementById("chat-box");
  chatBox.scrollTop = chatBox.scrollHeight;

  // Manejar el envío del formulario de manera asíncrona (sin recargar la página)
  const chatForm = document.getElementById("chat-form");
  if (chatForm) {
    chatForm.addEventListener("submit", function (e) {
      e.preventDefault(); // Evitar la recarga de la página

      const formData = new FormData(chatForm);

      fetch("/enviar", {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.status === "ok") {
            // Limpiar el campo del mensaje para poder escribir otro
            document.getElementById("message").value = "";
          }
        })
        .catch((error) => console.error("Error enviando mensaje:", error));
    });
  }
};
