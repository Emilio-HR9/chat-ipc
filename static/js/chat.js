// --- Constants ---
const POLLING_INTERVAL = 2000; // ms
const MULTICAST_IP_DEFAULT = "224.1.1.1";

// --- Functions ---

/**
 * Realiza una solicitud al servidor para obtener los últimos mensajes
 * y actualiza el cuadro de chat, manteniendo la posición del scroll.
 */
function pollMessages() {
  fetch("/mensajes")
    .then((response) => response.text())
    .then((html) => {
      const chatBox = document.getElementById("chat-box");
      if (!chatBox) return;

      const isScrolledToBottom =
        chatBox.scrollHeight - chatBox.clientHeight <= chatBox.scrollTop + 50;

      chatBox.innerHTML = html;

      if (isScrolledToBottom) {
        chatBox.scrollTop = chatBox.scrollHeight;
      }
    })
    .catch((err) => console.error("Error en polling:", err));
}

/**
 * Envía el formulario de chat de forma asíncrona.
 * @param {Event} e - El evento de submit del formulario.
 */
function handleFormSubmit(e) {
  e.preventDefault();
  const chatForm = e.target;
  const formData = new FormData(chatForm);

  fetch("/enviar", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "ok") {
        const messageInput = document.getElementById("message");
        if (messageInput) {
          messageInput.value = ""; // Limpiar el campo del mensaje
        }
      }
    })
    .catch((error) => console.error("Error enviando mensaje:", error));
}

/**
 * Ajusta el campo de IP en función del modo de comunicación seleccionado.
 * @param {Event} e - El evento de cambio del select.
 */
function handleModeChange(e) {
  const mode = e.target.value;
  const ipInput = document.getElementById("ip");
  if (!ipInput) return;

  switch (mode) {
    case "broadcast":
      ipInput.value = "255.255.255.255";
      ipInput.disabled = true;
      break;
    case "multicast":
      ipInput.value = MULTICAST_IP_DEFAULT;
      ipInput.disabled = false;
      break;
    case "unicast":
    case "anycast":
      ipInput.value = "127.0.0.1";
      ipInput.disabled = false;
      break;
  }
}

/**
 * Envía la petición para unirse a un nuevo grupo multicast.
 */
function handleJoinGroupSubmit(e) {
  e.preventDefault();
  const joinForm = e.target;
  const formData = new FormData(joinForm);

  fetch("/join_group", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "ok") {
        const groupIpInput = document.getElementById("group-ip");
        if (groupIpInput) groupIpInput.value = "";
        alert(data.message); // Notificar éxito
      } else {
        alert("Error: " + data.message);
      }
    })
    .catch((error) => {
      console.error("Error uniéndose al grupo:", error);
      alert("Ocurrió un error al intentar unirse al grupo.");
    });
}

// --- Event Listeners ---

// Se ejecuta cuando el DOM está completamente cargado
document.addEventListener("DOMContentLoaded", () => {
  // 1. Iniciar el polling de mensajes
  setInterval(pollMessages, POLLING_INTERVAL);

  // 2. Hacer scroll inicial
  const chatBox = document.getElementById("chat-box");
  if (chatBox) {
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  // 3. Manejar el envío del formulario principal
  const chatForm = document.getElementById("chat-form");
  if (chatForm) {
    chatForm.addEventListener("submit", handleFormSubmit);
  }

  // 4. Manejar el cambio de modo
  const modeSelect = document.getElementById("mode");
  if (modeSelect) {
    modeSelect.addEventListener("change", handleModeChange);
    // Disparar el evento al inicio para establecer el estado inicial correcto
    handleModeChange({ target: modeSelect });
  }

  // 5. Manejar unirse a grupo multicast
  const joinGroupForm = document.getElementById("join-group-form");
  if (joinGroupForm) {
    joinGroupForm.addEventListener("submit", handleJoinGroupSubmit);
  }
});
