let uploadedZipPath = "examples/teste_matrix.zip";
let eventSource = null;

const zipInput = document.getElementById("zipInput");
const zipLabel = document.getElementById("zipLabel");
const wordlistSelect = document.getElementById("wordlistSelect");
const btnStart = document.getElementById("btnStart");
const btnStop = document.getElementById("btnStop");

const valPercent = document.getElementById("valPercent");
const valRate = document.getElementById("valRate");
const valTested = document.getElementById("valTested");
const valElapsed = document.getElementById("valElapsed");
const progressBar = document.getElementById("progressBar");

const resultBox = document.getElementById("resultBox");
const resultPassword = document.getElementById("resultPassword");
const resultDetails = document.getElementById("resultDetails");
const logTerminal = document.getElementById("logTerminal");
const headerStatus = document.getElementById("headerStatus");

function log(msg, type = "muted") {
    const line = document.createElement("div");
    line.className = `log-line text-${type}`;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    logTerminal.appendChild(line);
    logTerminal.scrollTop = logTerminal.scrollHeight;
}

// Upload de arquivo ZIP
zipInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    zipLabel.textContent = `⏳ Enviando ${file.name}...`;
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        const data = await res.json();
        if (data.status === "success") {
            uploadedZipPath = data.filepath;
            zipLabel.textContent = `✅ ${file.name} (${(data.size_bytes / 1024).toFixed(1)} KB)`;
            log(`Arquivo ${file.name} carregado com sucesso.`, "info");
        } else {
            zipLabel.textContent = "❌ Falha no upload.";
            log(`Erro no upload: ${data.message}`, "danger");
        }
    } catch (err) {
        log(`Erro de conexão: ${err.message}`, "danger");
    }
});

btnStart.addEventListener("click", async () => {
    resultBox.style.display = "none";
    progressBar.style.width = "0%";
    valPercent.textContent = "0.0%";
    valRate.textContent = "0 s/s";
    
    btnStart.disabled = true;
    btnStop.disabled = false;
    headerStatus.innerHTML = '<span class="status-dot" style="background:#58a6ff;"></span> Recuperando...';

    log(`Iniciando ataque contra: ${uploadedZipPath}`, "info");

    try {
        const res = await fetch("/api/crack/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                zip_path: uploadedZipPath,
                wordlist_path: wordlistSelect.value
            })
        });
        const data = await res.json();
        if (data.status !== "started") {
            log(`Erro ao iniciar: ${data.message}`, "danger");
            resetButtons();
            return;
        }

        // Conectar SSE para telemetria em tempo real
        if (eventSource) eventSource.close();
        eventSource = new EventSource("/api/crack/events");

        eventSource.onmessage = (e) => {
            const ev = JSON.parse(e.data);
            if (ev.type === "heartbeat") return;

            if (ev.type === "progress") {
                valPercent.textContent = `${ev.percent}%`;
                valRate.textContent = `${ev.rate} s/s`;
                valTested.textContent = `${ev.tested.toLocaleString()} / ${ev.total.toLocaleString()}`;
                valElapsed.textContent = `${ev.elapsed}s`;
                progressBar.style.width = `${ev.percent}%`;
            } else if (ev.type === "found") {
                progressBar.style.width = "100%";
                valPercent.textContent = "100.0%";
                resultPassword.textContent = ev.password;
                resultDetails.textContent = `Recuperado em ${ev.elapsed || 0}s (${(ev.rate || 0)} senhas/s)`;
                resultBox.style.display = "block";
                log(`SENHA ENCONTRADA: ${ev.password}`, "success");
                headerStatus.innerHTML = '<span class="status-dot" style="background:#2ea043;"></span> Sucesso';
                eventSource.close();
                resetButtons();
            } else if (ev.type === "finished") {
                log("Processamento concluído. Senha não encontrada no dicionário.", "danger");
                headerStatus.innerHTML = '<span class="status-dot" style="background:#f85149;"></span> Não encontrada';
                eventSource.close();
                resetButtons();
            } else if (ev.type === "stopped") {
                log("Ataque interrompido pelo usuário.", "muted");
                eventSource.close();
                resetButtons();
            }
        };

        eventSource.onerror = () => {
            if (eventSource) eventSource.close();
            resetButtons();
        };

    } catch (err) {
        log(`Erro de rede: ${err.message}`, "danger");
        resetButtons();
    }
});

btnStop.addEventListener("click", async () => {
    await fetch("/api/crack/stop", { method: "POST" });
    if (eventSource) eventSource.close();
    resetButtons();
    log("Solicitação de parada enviada.", "muted");
});

function resetButtons() {
    btnStart.disabled = false;
    btnStop.disabled = true;
}
