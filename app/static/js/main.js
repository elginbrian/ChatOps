document.addEventListener("DOMContentLoaded", () => {
  let activeConversationId = null;
  let conversations = [];

  const commandForm = document.getElementById("commandForm");
  const commandInput = document.getElementById("commandInput");
  const sendButton = document.getElementById("sendButton");
  const sendIcon = document.getElementById("sendIcon");
  const loadingIndicator = document.getElementById("loadingIndicator");
  const chatFeed = document.getElementById("chatFeed");
  const chatHeader = document.getElementById("chatHeader");

  const newChatButton = document.getElementById("newChatButton");
  const conversationList = document.getElementById("conversationList");

  const toggleGuideButton = document.getElementById("toggleGuideButton");
  const commandGuideModal = document.getElementById("commandGuideModal");
  const closeGuideButton = document.getElementById("closeGuideButton");
  const commandGuideContent = document.getElementById("commandGuideContent");

  const rawCommandGuide = JSON.parse(document.getElementById("command-guide-data").textContent);

  function showToast(message, isError = false) {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    const bgColor = isError ? "bg-red-800" : "bg-gray-200";
    const textColor = isError ? "text-white" : "text-black";
    toast.className = `animate-fadeIn ${bgColor} ${textColor} text-sm font-medium px-4 py-2 rounded-lg shadow-lg`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 3000);
  }

  function copyToClipboard(text, type = "Teks") {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        showToast(`${type} disalin: "${text}"`);
      })
      .catch((err) => {
        console.error("Gagal menyalin:", err);
        showToast("Gagal menyalin.", true);
      });
  }

  function createBaseMessageElement(extraClasses = "") {
    const template = document.getElementById("base-message-template").content.cloneNode(true);
    const article = template.querySelector(".chat-message");
    article.className += ` ${extraClasses}`;
    return article;
  }

  function configureIcon(element, iconName, colorClasses) {
    const iconContainer = element.querySelector(".icon-container");
    const icon = element.querySelector(".icon");
    iconContainer.className += ` ${colorClasses}`;
    icon.setAttribute("name", iconName);
  }

  function createUserMessageElement(text) {
    const element = createBaseMessageElement("self-end flex-row-reverse");
    configureIcon(element, "person-circle-outline", "bg-gray-700 text-white");
    const content = element.querySelector(".message-content");
    content.className = "bg-white text-black p-3 rounded-t-xl rounded-l-xl w-auto";
    content.textContent = text;
    return element;
  }

  function createBotTextMessage(text, type) {
    const element = createBaseMessageElement("self-start");
    const content = element.querySelector(".message-content");
    let iconName, iconColor, contentClass;
    switch (type) {
      case "bot-error":
        iconName = "warning-outline";
        iconColor = "bg-red-900/80 text-white";
        contentClass = "bg-[var(--bg-tertiary)] text-red-400 p-3 rounded-t-xl rounded-r-xl font-mono text-sm";
        break;
      case "system-info":
        iconName = "information-circle-outline";
        iconColor = "bg-gray-700 text-gray-200";
        contentClass = "bg-[var(--bg-tertiary)] text-gray-400 p-3 rounded-t-xl rounded-r-xl italic text-sm";
        break;
      case "gemini-output":
        iconName = "sparkles-outline";
        iconColor = "bg-indigo-800 text-white";
        contentClass = "gemini-content bg-[var(--bg-tertiary)] text-gray-300 p-3 rounded-t-xl rounded-r-xl text-sm leading-relaxed";
        content.innerHTML = marked.parse(text || "");
        break;
      default:
        iconName = "logo-docker";
        iconColor = "bg-blue-800 text-white";
        contentClass = "bg-[var(--bg-tertiary)] text-gray-300 p-3 rounded-t-xl rounded-r-xl";
        const pre = document.createElement("pre");
        pre.className = "whitespace-pre-wrap word-wrap break-word font-mono text-sm";
        pre.textContent = text;
        content.appendChild(pre);
        break;
    }
    configureIcon(element, iconName, iconColor);
    if (contentClass) content.className = contentClass;
    if (!content.hasChildNodes()) content.textContent = text;
    return element;
  }

  function createTableElement(headers, rows, noDataMessage) {
    const element = document.getElementById("table-template").content.cloneNode(true);
    const thead = element.querySelector("thead");
    const tbody = element.querySelector("tbody");
    const headerRow = document.createElement("tr");
    headers.forEach((h) => {
      const th = document.createElement("th");
      th.className = "p-3 " + (h.className || "");
      th.textContent = h.text;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    if (!rows || rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="${headers.length}" class="p-4 text-center text-gray-500">${noDataMessage}</td></tr>`;
    } else {
      rows.forEach((row) => tbody.appendChild(row));
    }
    return element;
  }

  function createTableRenderer(config) {
    return function (data) {
      const rows = data.map((item) => {
        const rowTemplate = document.getElementById(config.rowTemplateId).content.cloneNode(true);
        config.mapDataToRow(rowTemplate, item);
        return rowTemplate;
      });
      const table = createTableElement(config.headers, rows, config.noDataMessage);
      const messageElement = createBaseMessageElement("self-start w-full");
      configureIcon(messageElement, config.icon.name, config.icon.color);
      messageElement.querySelector(".message-content").appendChild(table);
      return messageElement;
    };
  }

  function createGeminiTable(data) {
    const headers = data.headers.map((h) => ({ text: h, className: "p-3" }));
    const rows = data.rows.map((rowData) => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-[var(--bg-secondary)]/50 transition-colors";

      rowData.forEach((cellData) => {
        const td = document.createElement("td");
        td.className = "p-3 align-middle text-gray-300";
        td.textContent = cellData;
        tr.appendChild(td);
      });
      return tr;
    });

    const table = createTableElement(headers, rows, "Tidak ada data untuk ditampilkan.");
    const messageElement = createBaseMessageElement("self-start w-full");
    // Gunakan ikon Gemini untuk tabel yang ia buat
    configureIcon(messageElement, "sparkles-outline", "bg-indigo-800 text-white");
    messageElement.querySelector(".message-content").appendChild(table);
    return messageElement;
  }

  const createContainerTable = createTableRenderer({
    rowTemplateId: "container-table-row-template",
    headers: [{ text: "Status" }, { text: "Name" }, { text: "Image", className: "hidden md:table-cell" }, { text: "Ports", className: "hidden lg:table-cell" }, { text: "Actions", className: "text-right" }],
    noDataMessage: "Tidak ada kontainer.",
    icon: { name: "logo-docker", color: "bg-blue-800 text-white" },
    mapDataToRow: (row, c) => {
      const isRunning = c.status.toLowerCase().startsWith("up") || c.status.toLowerCase().startsWith("running");
      const canInteract = isRunning && !c.is_self;
      row.querySelector(".status-indicator").classList.add(isRunning ? "bg-green-500" : "bg-gray-500");
      row.querySelector(".status-indicator").title = c.status;
      row.querySelector(".container-name").textContent = `${c.name}${c.is_self ? " (Ini)" : ""}`;
      row.querySelector(".container-id").textContent = c.id;
      row.querySelector(".container-image").textContent = c.image;
      row.querySelector(".container-ports").textContent = c.ports || "-";
      row.querySelector(".copy-button").onclick = () => copyToClipboard(c.name, "Nama");
      row.querySelector(".inspect-button").onclick = () => handleQuickAction("inspect container", c.name);
      const logsButton = row.querySelector(".logs-button");
      logsButton.onclick = () => handleQuickAction("lihat log", c.name);
      if (!canInteract) logsButton.disabled = true;
      const stopButton = row.querySelector(".stop-button");
      stopButton.onclick = () => handleQuickAction("stop", c.name);
      if (!canInteract) stopButton.disabled = true;
    },
  });

  const createImageTable = createTableRenderer({
    rowTemplateId: "image-table-row-template",
    headers: [{ text: "Repository" }, { text: "Tag" }, { text: "Image ID", className: "hidden sm:table-cell" }, { text: "Created", className: "hidden md:table-cell" }, { text: "Size (MB)", className: "text-right" }],
    noDataMessage: "Tidak ada image.",
    icon: { name: "logo-docker", color: "bg-blue-800 text-white" },
    mapDataToRow: (row, i) => {
      row.querySelector(".repository").textContent = i.repository;
      row.querySelector(".tag").textContent = i.tag;
      row.querySelector(".id").textContent = i.id;
      row.querySelector(".created").textContent = i.created;
      row.querySelector(".size").textContent = i.size;
    },
  });

  const createVolumeTable = createTableRenderer({
    rowTemplateId: "volume-table-row-template",
    headers: [{ text: "Volume Name" }, { text: "Driver", className: "hidden sm:table-cell" }, { text: "Created", className: "hidden md:table-cell" }, { text: "Actions", className: "text-right" }],
    noDataMessage: "Tidak ada volume.",
    icon: { name: "server-outline", color: "bg-purple-800 text-white" },
    mapDataToRow: (row, v) => {
      row.querySelector(".name").textContent = v.name;
      row.querySelector(".driver").textContent = v.driver;
      row.querySelector(".created_at").textContent = v.created_at;
      row.querySelector(".copy-button").onclick = () => copyToClipboard(v.name, "Nama Volume");
      row.querySelector(".inspect-button").onclick = () => handleQuickAction("inspect volume", v.name);
      row.querySelector(".remove-button").onclick = () => handleQuickAction("rm volume", v.name);
    },
  });

  const createNetworkTable = createTableRenderer({
    rowTemplateId: "network-table-row-template",
    headers: [{ text: "Network Name" }, { text: "Driver", className: "hidden sm:table-cell" }, { text: "Scope", className: "hidden md:table-cell" }, { text: "Actions", className: "text-right" }],
    noDataMessage: "Tidak ada network.",
    icon: { name: "git-network-outline", color: "bg-teal-800 text-white" },
    mapDataToRow: (row, n) => {
      row.querySelector(".name").textContent = n.name;
      row.querySelector(".id").textContent = n.id;
      row.querySelector(".driver").textContent = n.driver;
      row.querySelector(".scope").textContent = n.scope;
      row.querySelector(".copy-button").onclick = () => copyToClipboard(n.name, "Nama Network");
      row.querySelector(".inspect-button").onclick = () => handleQuickAction("inspect network", n.name);
    },
  });

  const createStatsTable = createTableRenderer({
    rowTemplateId: "stats-table-row-template",
    headers: [{ text: "Kontainer" }, { text: "CPU Usage" }, { text: "Memory Usage" }],
    noDataMessage: "Tidak ada statistik untuk ditampilkan.",
    icon: { name: "bar-chart-outline", color: "bg-green-800 text-white" },
    mapDataToRow: (row, s) => {
      row.querySelector(".container_name").textContent = s.container_name;
      row.querySelector(".cpu_usage").textContent = s.cpu_usage;
      row.querySelector(".mem_usage").textContent = s.mem_usage;
    },
  });

  const createLogsTable = createTableRenderer({
    rowTemplateId: "logs-table-row-template",
    headers: [
      { text: "Timestamp", className: "w-1/4" },
      { text: "Log Entry", className: "w-3/4" },
    ],
    noDataMessage: "Tidak ada log untuk ditampilkan.",
    icon: { name: "document-text-outline", color: "bg-yellow-800 text-white" },
    mapDataToRow: (row, l) => {
      row.querySelector(".timestamp").textContent = l.timestamp;
      row.querySelector(".log_entry").textContent = l.log_entry;
    },
  });

  function createInspectOutputElement(jsonDataString, objectName) {
    const element = createBaseMessageElement("self-start w-full");
    configureIcon(element, "code-slash-outline", "bg-purple-800 text-white");
    const template = document.getElementById("inspect-output-template").content.cloneNode(true);
    template.querySelector(".object-name").textContent = objectName;
    template.querySelector(".json-content").textContent = jsonDataString;
    template.querySelector(".copy-json-button").onclick = () => copyToClipboard(jsonDataString, "JSON");
    element.querySelector(".message-content").appendChild(template);
    return element;
  }

  function createActionReceiptElement(data) {
    const element = createBaseMessageElement("self-start");
    const template = document.getElementById("action-receipt-template").content.cloneNode(true);
    const actionIcons = {
      Run: { name: "play-circle-outline", color: "bg-green-800/80" },
      Stop: { name: "stop-circle-outline", color: "bg-yellow-800/80" },
      Start: { name: "play-circle-outline", color: "bg-green-800/80" },
      Remove: { name: "trash-outline", color: "bg-red-800/80" },
      Pull: { name: "arrow-down-circle-outline", color: "bg-sky-800/80" },
      Prune: { name: "build-outline", color: "bg-orange-800/80" },
      default: { name: "checkmark-circle-outline", color: "bg-gray-700" },
    };
    const statusColors = {
      "Berhasil Dijalankan": "border-green-500",
      "Berhasil Dihentikan": "border-yellow-500",
      "Berhasil Dihidupkan": "border-green-500",
      "Berhasil Dihapus": "border-red-500",
      "Berhasil Ditarik": "border-sky-500",
      "Sistem Berhasil Dibersihkan": "border-orange-500",
      default: "border-gray-500",
    };
    const iconInfo = actionIcons[data.action] || actionIcons.default;
    configureIcon(element, iconInfo.name, iconInfo.color + " text-white");
    const wrapper = template.querySelector(".wrapper");
    wrapper.classList.add(statusColors[data.status] || statusColors.default);
    template.querySelector(".status-text").textContent = data.status;
    template.querySelector(".resource-type").textContent = data.resource_type;
    template.querySelector(".resource-name").textContent = data.resource_name;
    const detailsList = template.querySelector(".details-list");
    if (data.details && data.details.length > 0) {
      data.details.forEach((detail) => {
        const item = document.createElement("p");
        item.className = "text-xs text-gray-400";
        item.innerHTML = `<span class="font-semibold">${detail.key}:</span> <span class="font-mono">${detail.value}</span>`;
        detailsList.appendChild(item);
      });
    } else {
      detailsList.remove();
    }
    element.querySelector(".message-content").appendChild(template);
    return element;
  }

  function createTypingIndicator() {
    const element = createBaseMessageElement("self-start");
    element.id = "typingIndicator";
    configureIcon(element, "logo-docker", "bg-blue-800 text-white");
    const content = element.querySelector(".message-content");
    content.className = "flex items-center gap-1.5 p-3";
    content.innerHTML = `<div class="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div><div class="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div><div class="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div>`;
    return element;
  }

  function createBotResponse(data) {
    if (data.error) {
      return createBotTextMessage(data.error, "bot-error");
    }

    const receivedCmd = data.received_command || "";

    switch (data.output_type) {
      case "table":
        if (!data.output || data.output.length === 0) {
          if (receivedCmd.includes("image")) return createImageTable([]);
          if (receivedCmd.includes("log")) return createLogsTable([]);
          if (receivedCmd.includes("stats")) return createStatsTable([]);
          if (receivedCmd.includes("volume")) return createVolumeTable([]);
          if (receivedCmd.includes("network")) return createNetworkTable([]);
          return createContainerTable([]);
        }
        const firstItem = data.output[0];
        if (firstItem.hasOwnProperty("status")) return createContainerTable(data.output);
        if (firstItem.hasOwnProperty("repository")) return createImageTable(data.output);
        if (firstItem.hasOwnProperty("cpu_usage")) return createStatsTable(data.output);
        if (firstItem.hasOwnProperty("log_entry")) return createLogsTable(data.output);
        if (firstItem.hasOwnProperty("driver") && firstItem.hasOwnProperty("created_at")) return createVolumeTable(data.output);
        if (firstItem.hasOwnProperty("driver") && firstItem.hasOwnProperty("scope")) return createNetworkTable(data.output);
        return createBotTextMessage("Tipe data tabel tidak dikenali.", "bot-error");

      case "action_receipt":
        return createActionReceiptElement(data.output);
      case "inspect":
        const objectName = receivedCmd.split(" ").slice(2).join(" ");
        return createInspectOutputElement(data.output, objectName);
      case "text":
        return createBotTextMessage(data.output, "bot-output");
      case "gemini_text":
        return createBotTextMessage(data.output, "gemini-output");

      case "gemini_table":
        return createGeminiTable(data.output);
      default:
        return createBotTextMessage(`Tipe output tidak dikenali: ${data.output_type}`, "bot-error");
    }
  }

  function appendToFeed(element) {
    if (!element) return;
    chatFeed.appendChild(element);
    setTimeout(() => {
      chatFeed.scrollTop = chatFeed.scrollHeight;
    }, 50);
  }

  function setLoadingState(isLoading) {
    sendIcon.classList.toggle("hidden", isLoading);
    loadingIndicator.classList.toggle("hidden", !isLoading);
    sendButton.disabled = isLoading;
    commandInput.disabled = isLoading;
    if (!isLoading) commandInput.focus();
  }

  function handleQuickAction(action, name) {
    let command = `${action} ${name}`;
    showToast(`Menjalankan: ${command}`);
    submitCommand(command);
  }

  function toggleModal(show) {
    if (show) {
      commandGuideModal.classList.remove("hidden");
      commandGuideModal.classList.add("opacity-100");
    } else {
      commandGuideModal.classList.remove("opacity-100");
      setTimeout(() => {
        commandGuideModal.classList.add("hidden");
      }, 300);
    }
  }
  function populateCommandGuide() {
    commandGuideContent.innerHTML =
      rawCommandGuide
        ?.map(
          (cmd) =>
            `<div class="p-3 bg-[var(--bg-tertiary)] rounded-lg border border-[var(--border-color)] hover:bg-white/5 hover:border-white/20 transition-all duration-200"><p class="text-gray-200">${cmd.description}</p><p class="text-gray-400 mt-2 text-xs">Contoh: <code class="font-mono bg-[var(--bg-secondary)] px-1.5 py-0.5 rounded">${cmd.example}</code></p></div>`
        )
        .join("") || '<p class="text-gray-500">Panduan perintah tidak tersedia.</p>';
  }

  function renderSidebar() {
    conversationList.innerHTML = "";
    conversations.forEach((conv) => {
      const template = document.getElementById("conversation-item-template").content.cloneNode(true);
      const link = template.querySelector(".conversation-link");
      link.dataset.id = conv.id;
      link.querySelector(".conversation-title").textContent = conv.title;

      if (conv.id === activeConversationId) {
        link.classList.add("bg-[var(--bg-tertiary)]");
      }

      link.addEventListener("click", (e) => {
        e.preventDefault();
        switchConversation(conv.id);
      });

      const deleteButton = template.querySelector(".delete-conversation-button");
      deleteButton.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await deleteConversation(conv.id);
      });

      conversationList.appendChild(template);
    });
  }

  async function loadConversationMessages(convId) {
    chatFeed.innerHTML = "";
    try {
      const response = await fetch(`/api/conversation/${convId}`);
      if (!response.ok) throw new Error("Gagal memuat percakapan.");
      const messages = await response.json();

      messages.forEach((entry) => {
        appendToFeed(createUserMessageElement(entry.user_command));
        const botResponseData = entry.bot_response;
        botResponseData.received_command = entry.user_command;
        appendToFeed(createBotResponse(botResponseData));
      });
    } catch (error) {
      console.error(error);
      appendToFeed(createBotTextMessage(error.message, "bot-error"));
    }
  }

  async function switchConversation(convId) {
    if (convId === activeConversationId) return;

    activeConversationId = convId;
    const activeConv = conversations.find((c) => c.id === convId);
    chatHeader.textContent = activeConv ? activeConv.title : "Percakapan";

    renderSidebar();
    await loadConversationMessages(convId);
  }

  function startNewChat() {
    activeConversationId = null;
    chatFeed.innerHTML = "";
    chatHeader.textContent = "Percakapan Baru";
    appendToFeed(createBotTextMessage("Selamat datang! Ketik perintah untuk memulai percakapan baru.", "system-info"));
    renderSidebar();
    commandInput.focus();
  }

  async function deleteConversation(convId) {
    if (!confirm("Anda yakin ingin menghapus percakapan ini?")) return;

    try {
      const response = await fetch(`/api/conversation/${convId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Gagal menghapus percakapan.");

      conversations = conversations.filter((c) => c.id !== convId);
      showToast("Percakapan dihapus.");

      if (convId === activeConversationId) {
        startNewChat();
      } else {
        renderSidebar();
      }
    } catch (error) {
      console.error(error);
      showToast(error.message, true);
    }
  }

  async function submitCommand(commandText) {
    if (!commandText) return;

    appendToFeed(createUserMessageElement(commandText));
    commandInput.value = "";
    appendToFeed(createTypingIndicator());
    setLoadingState(true);

    const removeIndicator = () => {
      const indicator = document.getElementById("typingIndicator");
      if (indicator) indicator.remove();
    };

    try {
      const payload = {
        command: commandText,
        conversation_id: activeConversationId,
      };

      const response = await fetch("/api/command", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      });

      removeIndicator();
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Server Error: ${response.status}`);
      }

      data.received_command = commandText;
      appendToFeed(createBotResponse(data));

      if (!activeConversationId && data.conversation_id) {
        activeConversationId = data.conversation_id;
        await init();
      }
    } catch (error) {
      removeIndicator();
      console.error("Fetch error:", error);
      appendToFeed(createBotTextMessage(error.message, "bot-error"));
    } finally {
      setLoadingState(false);
    }
  }

  async function init() {
    try {
      const response = await fetch("/api/conversations");
      if (!response.ok) throw new Error("Gagal mengambil daftar percakapan.");
      conversations = await response.json();

      const lastActive = conversations.find((c) => c.is_last_active);
      if (lastActive) {
        await switchConversation(lastActive.id);
      } else {
        startNewChat();
      }
    } catch (error) {
      console.error(error);
      startNewChat();
    }
  }

  commandForm.addEventListener("submit", (e) => {
    e.preventDefault();
    submitCommand(commandInput.value.trim());
  });

  newChatButton.addEventListener("click", startNewChat);

  toggleGuideButton.addEventListener("click", () => toggleModal(true));
  closeGuideButton.addEventListener("click", () => toggleModal(false));
  commandGuideModal.addEventListener("click", (event) => {
    if (event.target === commandGuideModal) toggleModal(false);
  });

  populateCommandGuide();
  init();
});
