// --- Constants ---
const POLLING_INTERVAL = 2000; // ms
const MULTICAST_IP_DEFAULT = "224.1.1.1";

// --- State ---
let currentChat = "Broadcast";
let messageCounts = {};
let unreadCounts = {};
let allMessagesHtml = "";

// --- Functions ---

/**
 * Filtra y renderiza los mensajes para el chat seleccionado.
 */
function renderMessages() {
  const chatBox = document.getElementById("chat-box");
  if (!chatBox) return;

  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = allMessagesHtml;
  const messages = tempDiv.querySelectorAll(".message[data-chat]");

  const filtered = Array.from(messages).filter(
    (msg) => msg.getAttribute("data-chat") === currentChat,
  );

  const isScrolledToBottom =
    chatBox.scrollHeight - chatBox.clientHeight <= chatBox.scrollTop + 50;

  if (filtered.length > 0) {
    chatBox.innerHTML = filtered.map((msg) => msg.outerHTML).join("");
  } else {
    chatBox.innerHTML =
      '<div class="message"><i>No hay mensajes aún en este chat. ¡Comienza a chatear!</i></div>';
  }

  if (isScrolledToBottom) {
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

/**
 * Realiza una solicitud al servidor para obtener los últimos mensajes
 * y actualiza el cuadro de chat, manteniendo la posición del scroll.
 */
function pollMessages() {
  fetch("/mensajes")
    .then((response) => response.text())
    .then((html) => {
      allMessagesHtml = html;

      const tempDiv = document.createElement("div");
      tempDiv.innerHTML = html;
      const messages = tempDiv.querySelectorAll(".message[data-chat]");
      let newCounts = {};

      messages.forEach((msg) => {
        const chatId = msg.getAttribute("data-chat");
        if (chatId) {
          newCounts[chatId] = (newCounts[chatId] || 0) + 1;
        }
      });

      let unreadChanged = false;
      for (const chat in newCounts) {
        const oldC = messageCounts[chat] || 0;
        if (newCounts[chat] > oldC) {
          if (chat !== currentChat) {
            unreadCounts[chat] =
              (unreadCounts[chat] || 0) + (newCounts[chat] - oldC);
            unreadChanged = true;
          }
        }
      }
      messageCounts = newCounts;

      renderMessages();

      if (unreadChanged) {
        renderChatsList(); // Force update badges
      }
    })
    .catch((err) => console.error("Error en polling:", err));
}

let lastEstadoData = null;

/**
 * Renderiza la lista de chats en el panel derecho.
 */
function renderChatsList() {
  if (!lastEstadoData) return;
  const data = lastEstadoData;
  const chatsList = document.getElementById("chats-list");
  if (!chatsList) return;

  // save open details to preserve state across repaints
  const openGroups = new Set();
  chatsList.querySelectorAll("details[open]").forEach((d) => {
    const summary = d.querySelector("summary");
    if (summary) openGroups.add(summary.getAttribute("data-group-id"));
  });

  let html = `<ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px;">`;

  const createChatNode = (id, label, icon, isGroup = false, members = {}) => {
    const isSelected = currentChat === id;
    const bg = isSelected ? "var(--btn-bg)" : "transparent";
    const color = isSelected ? "var(--btn-text)" : "inherit";
    const unread = unreadCounts[id] || 0;
    const badge =
      unread > 0
        ? `<span style="background: red; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.8em; margin-left: auto;">${unread}</span>`
        : "";

    let nodeHtml = `<li style="background: ${bg}; color: ${color}; border-radius: 4px; overflow: hidden; border: 1px solid var(--border-color);">`;

    if (isGroup) {
      const isOpen = openGroups.has(id) ? "open" : "";
      nodeHtml += `<details ${isOpen} style="width: 100%;">`;
      nodeHtml += `<summary data-group-id="${id}" class="chat-item" data-id="${id}" style="padding: 8px; cursor: pointer; display: flex; align-items: center; font-weight: ${isSelected ? "bold" : "normal"};">
            <span style="margin-right: 8px;">${icon}</span>
            <span style="flex: 1;">${label}</span>
            ${badge}
        </summary>`;
      if (Object.keys(members).length > 0) {
        nodeHtml += `<ul style="list-style: none; padding: 5px 10px 5px 30px; margin: 0; background: var(--input-bg); color: var(--text-color); font-size: 0.9em; border-top: 1px solid var(--border-color);">`;
        for (const [ip, hostname] of Object.entries(members)) {
          nodeHtml += `<li style="padding: 3px 0; border-bottom: 1px solid var(--border-color);">${hostname} (${ip})</li>`;
        }
        nodeHtml += `</ul>`;
      } else {
        nodeHtml += `<div style="padding: 5px 10px 5px 30px; background: var(--input-bg); color: var(--text-color); font-size: 0.8em; font-style: italic; border-top: 1px solid var(--border-color);">Sin miembros conocidos</div>`;
      }
      nodeHtml += `</details>`;
    } else {
      nodeHtml += `<div class="chat-item" data-id="${id}" style="padding: 8px; cursor: pointer; display: flex; align-items: center; font-weight: ${isSelected ? "bold" : "normal"};">
            <span style="margin-right: 8px;">${icon}</span>
            <span style="flex: 1;">${label}</span>
            ${badge}
        </div>`;
    }
    nodeHtml += `</li>`;
    return nodeHtml;
  };

  // 1. Broadcast
  html += createChatNode("Broadcast", "Broadcast", "🌍");

  // 2. Grupos Multicast
  data.grupos.forEach((grupo) => {
    const members = data.miembros[grupo] || {};
    html += createChatNode(grupo, grupo, "👥", true, members);
  });

  // 3. Usuarios Unicast
  const unicastUsers = data.miembros["Unicast/Anycast"] || {};
  for (const [ip, hostname] of Object.entries(unicastUsers)) {
    html += createChatNode(ip, `${hostname} (${ip})`, "👤");
  }

  html += `</ul>`;
  chatsList.innerHTML = html;

  // Add event listeners to chat items
  chatsList.querySelectorAll(".chat-item").forEach((item) => {
    item.addEventListener("click", (e) => {
      // prevent details toggle if clicking exactly on the chat logic area
      // but details summary handles its own toggle.
      const id = item.getAttribute("data-id");
      if (id) {
        selectChat(id);
      }
    });
  });
}

/**
 * Cambia el chat seleccionado.
 */
function selectChat(id) {
  if (currentChat !== id) {
    currentChat = id;
    unreadCounts[id] = 0; // Clear notifications
    renderChatsList();
    renderMessages();

    // Update form
    const modeSelect = document.getElementById("mode");
    const ipInput = document.getElementById("ip");
    if (modeSelect && ipInput) {
      if (id === "Broadcast") {
        modeSelect.value = "broadcast";
        handleModeChange({ target: modeSelect });
      } else if (id.includes(".")) {
        // Determine if multicast or unicast based on first octet
        const firstOctet = parseInt(id.split(".")[0]);
        if (firstOctet >= 224 && firstOctet <= 239) {
          modeSelect.value = "multicast";
          ipInput.value = id;
          ipInput.disabled = false;
        } else {
          modeSelect.value = "unicast";
          ipInput.value = id;
          ipInput.disabled = false;
        }
      }
    }
  }
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
        pollMessages(); // Force update
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
      // Solo sobreescribir si no es ya un multicast válido
      const firstO = parseInt(ipInput.value.split(".")[0]);
      if (isNaN(firstO) || firstO < 224 || firstO > 239) {
        ipInput.value = MULTICAST_IP_DEFAULT;
      }
      ipInput.disabled = false;
      break;
    case "unicast":
    case "anycast":
      if (
        ipInput.value === "255.255.255.255" ||
        ipInput.value === MULTICAST_IP_DEFAULT
      ) {
        ipInput.value = "127.0.0.1";
      }
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
        const newGroup = groupIpInput ? groupIpInput.value : null;
        if (groupIpInput) groupIpInput.value = "";
        alert(data.message); // Notificar éxito
        if (newGroup) {
          selectChat(newGroup);
        }
        pollEstado(); // Update chats list immediately
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
      lastEstadoData = data;
      renderChatsList();
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
  pollMessages(); // Cargar mensajes inicialmente

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
