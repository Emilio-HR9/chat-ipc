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

/**
 * Realiza una solicitud al servidor para obtener grupos y miembros conocidos.
 */
function pollEstado() {
  fetch("/estado")
    .then((response) => response.json())
    .then((data) => {
      // Actualizar grupos
      const gruposLista = document.getElementById("grupos-lista");
      if (gruposLista) {
        gruposLista.innerHTML = "";
        data.grupos.forEach((grupo) => {
          const li = document.createElement("li");
          li.textContent = grupo;
          li.style.marginBottom = "5px";
          gruposLista.appendChild(li);
        });
        if (data.grupos.length === 0) {
          gruposLista.innerHTML = "<li><i>No hay grupos</i></li>";
        }
      }

      // Actualizar miembros
      const miembrosContainer = document.getElementById("miembros-container");
      if (miembrosContainer) {
        // save open details to preserve state across repaints
        const openGroups = new Set();
        miembrosContainer.querySelectorAll("details[open]").forEach((d) => {
          const summary = d.querySelector("summary");
          if (summary) openGroups.add(summary.textContent);
        });

        let html = "";
        let hasMembers = false;
        for (const [group, members] of Object.entries(data.miembros)) {
          if (Object.keys(members).length === 0) continue;
          hasMembers = true;
          const isOpen = openGroups.has(group) ? "open" : "";
          html += `<details ${isOpen} style="margin-bottom: 5px; cursor: pointer; border: 1px solid var(--border-color); padding: 5px; border-radius: 4px;">`;
          html += `<summary style="font-weight: bold; padding: 2px;">${group}</summary>`;
          html += `<ul style="list-style-type: none; padding-left: 10px; margin: 5px 0 0 0; border-top: 1px solid var(--border-color); padding-top: 5px;">`;
          for (const [ip, hostname] of Object.entries(members)) {
            html += `<li class="member-item" data-ip="${ip}" style="padding: 3px 0; color: var(--text-color); cursor: pointer;" onmouseover="this.style.textDecoration='underline'; this.style.color='#007bff';" onmouseout="this.style.textDecoration='none'; this.style.color='var(--text-color)';">${hostname} (${ip})</li>`;
          }
          html += `</ul></details>`;
        }

        if (!hasMembers) {
          html = "<i>No hay miembros conocidos</i>";
        }
        miembrosContainer.innerHTML = html;

        // Add event listeners to newly created items
        miembrosContainer.querySelectorAll(".member-item").forEach((item) => {
          item.addEventListener("click", (e) => {
            const selectedIp = e.target.getAttribute("data-ip");
            if (selectedIp) {
              const ipInput = document.getElementById("ip");
              const modeSelect = document.getElementById("mode");
              if (ipInput && modeSelect) {
                modeSelect.value = "unicast";
                ipInput.value = selectedIp;
                ipInput.disabled = false;
              }
            }
          });
        });
      }
    })
    .catch((err) => console.error("Error en polling de estado:", err));
}

// --- Event Listeners ---

// Se ejecuta cuando el DOM está completamente cargado
document.addEventListener("DOMContentLoaded", () => {
  // 1. Iniciar el polling de mensajes y estado
  setInterval(pollMessages, POLLING_INTERVAL);
  setInterval(pollEstado, POLLING_INTERVAL);
  pollEstado(); // Llamada inicial

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

  // 6. Configurar Modo Oscuro
  const darkModeToggle = document.getElementById("dark-mode-toggle");
  if (darkModeToggle) {
    // Revisar preferencia previa
    const isDarkMode = localStorage.getItem("darkMode") === "true";
    if (isDarkMode) {
      document.body.setAttribute("data-theme", "dark");
      darkModeToggle.checked = true;
    }

    // Escuchar cambios
    darkModeToggle.addEventListener("change", (e) => {
      if (e.target.checked) {
        document.body.setAttribute("data-theme", "dark");
        localStorage.setItem("darkMode", "true");
      } else {
        document.body.removeAttribute("data-theme");
        localStorage.setItem("darkMode", "false");
      }
    });
  }
});
