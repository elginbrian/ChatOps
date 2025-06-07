document.addEventListener("DOMContentLoaded", () => {
  const commandForm = document.getElementById("commandForm");
  const commandInput = document.getElementById("commandInput");
  const sendButton = document.getElementById("sendButton");
  const sendIcon = document.getElementById("sendIcon");
  const loadingIndicator = document.getElementById("loadingIndicator");
  const chatFeed = document.getElementById("chatFeed");
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

  // --- Element Creation Functions ---
  function createBaseMessageElement(extraClasses = "") {
    const template = document.getElementById("base-message-template").content.cloneNode(true);
    const article = template.querySelector(".chat-message");
    article.className += ` ${extraClasses}`;
    return template;
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
    content.className = "bg-white text-black p-3 rounded-t-xl rounded-l-xl";
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

  function createContainerTable(containers) {
    const headers = [{ text: "Status" }, { text: "Name" }, { text: "Image", className: "hidden md:table-cell" }, { text: "Ports", className: "hidden lg:table-cell" }, { text: "Actions", className: "text-right" }];
    const rows = containers.map((c) => {
      const rowTemplate = document.getElementById("container-table-row-template").content.cloneNode(true);
      const isRunning = c.status.toLowerCase().startsWith("up") || c.status.toLowerCase().startsWith("running");
      const canInteract = isRunning && !c.is_self;
      rowTemplate.querySelector(".status-indicator").classList.add(isRunning ? "bg-green-500" : "bg-gray-500");
      rowTemplate.querySelector(".status-indicator").title = c.status;
      rowTemplate.querySelector(".container-name").textContent = `${c.name}${c.is_self ? " (Ini)" : ""}`;
      rowTemplate.querySelector(".container-id").textContent = c.id;
      rowTemplate.querySelector(".container-image").textContent = c.image;
      rowTemplate.querySelector(".container-ports").textContent = c.ports || "-";
      rowTemplate.querySelector(".copy-button").onclick = () => copyToClipboard(c.name, "Nama");
      const inspectButton = rowTemplate.querySelector(".inspect-button");
      inspectButton.onclick = () => handleQuickAction("inspect container", c.name);
      const logsButton = rowTemplate.querySelector(".logs-button");
      logsButton.onclick = () => handleQuickAction("lihat log", c.name);
      if (!canInteract) logsButton.disabled = true;
      const stopButton = rowTemplate.querySelector(".stop-button");
      stopButton.onclick = () => handleQuickAction("stop", c.name);
      if (!canInteract) stopButton.disabled = true;
      return rowTemplate;
    });
    const table = createTableElement(headers, rows, "Tidak ada kontainer.");
    const element = createBaseMessageElement("self-start w-full");
    configureIcon(element, "logo-docker", "bg-blue-800 text-white");
    element.querySelector(".message-content").appendChild(table);
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
    const element = createBaseMessageElement();
    element.firstElementChild.id = "typingIndicator";
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
    switch (data.output_type) {
      case "table":
        if (data.output && data.output.length > 0 && data.output[0].hasOwnProperty("status")) {
          return createContainerTable(data.output);
        }
        return createBotTextMessage("Tipe tabel ini belum diimplementasikan di UI.", "bot-error");
      case "action_receipt":
        return createActionReceiptElement(data.output);
      case "inspect":
        return createBotTextMessage(data.output, "bot-output");
      case "text":
        return createBotTextMessage(data.output, "bot-output");
      default:
        return createBotTextMessage("Tipe output tidak dikenali.", "bot-error");
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
  async function submitCommand(commandText) {
    if (!commandText) return;
    appendToFeed(createUserMessageElement(commandText));
    commandInput.value = "";
    const typingIndicator = createTypingIndicator();
    appendToFeed(typingIndicator);
    setLoadingState(true);
    try {
      const response = await fetch("/api/command", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ command: commandText }) });
      const data = await response.json();
      data.received_command = commandText;
      typingIndicator.remove();
      if (!response.ok && !data.error) {
        data.error = `Server Error: ${response.status}`;
      }
      const botResponse = createBotResponse(data);
      if (botResponse) appendToFeed(botResponse);
    } catch (error) {
      typingIndicator.remove();
      console.error("Fetch error:", error);
      appendToFeed(createBotTextMessage(`Kesalahan Jaringan: ${error.message}.`, "bot-error"));
    } finally {
      setLoadingState(false);
    }
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

  commandForm.addEventListener("submit", (e) => {
    e.preventDefault();
    submitCommand(commandInput.value.trim());
  });
  toggleGuideButton.addEventListener("click", () => toggleModal(true));
  closeGuideButton.addEventListener("click", () => toggleModal(false));
  commandGuideModal.addEventListener("click", (event) => {
    if (event.target === commandGuideModal) toggleModal(false);
  });

  appendToFeed(createBotTextMessage("Selamat datang di ChatOps! Ketik perintah untuk mengelola Docker container Anda atau klik 'Panduan' untuk melihat daftar perintah.", "system-info"));
  populateCommandGuide();
  commandInput.focus();
});
