/**
 * Unloque - Frontend Application Logic & SSE Streaming
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- Application State ---
    const state = {
        activeZip: null,           // { filepath, filename, size_bytes }
        activeWordlist: {
            type: 'all_wordlists', // 'all_wordlists' | 'server_file' | 'custom_upload' | 'generated_pool'
            filepath: null,
            filename: null,
            size_bytes: 0
        },
        generatedWords: [],
        jobId: null,
        jobStatus: 'idle',         // 'idle' | 'running' | 'paused' | 'stopped' | 'found' | 'finished'
        eventSource: null,
        serverWordlists: [],
        serverExamples: []
    };

    // --- DOM Elements Cache ---
    const elements = {
        // Tabs
        tabButtons: document.querySelectorAll('.tab-btn'),
        tabPanes: document.querySelectorAll('.tab-pane'),
        globalStatusDot: document.getElementById('global-status-dot'),
        globalStatusText: document.getElementById('global-status-text'),

        // Cracker Inputs
        zipDropzone: document.getElementById('zip-dropzone'),
        zipFileInput: document.getElementById('zip-file-input'),
        zipDropzoneEmpty: document.getElementById('zip-dropzone-empty'),
        zipSelectedBox: document.getElementById('zip-selected-box'),
        selectedZipName: document.getElementById('selected-zip-name'),
        selectedZipSize: document.getElementById('selected-zip-size'),
        btnRemoveZip: document.getElementById('btn-remove-zip'),
        selectZipExample: document.getElementById('select-zip-example'),

        // Wordlist Strategy
        wordlistRadios: document.querySelectorAll('input[name="wordlist-source"]'),
        radioCardGenerated: document.getElementById('radio-card-generated'),
        generatedPoolCount: document.getElementById('generated-pool-count'),
        containerServerWordlist: document.getElementById('container-server-wordlist'),
        selectServerWordlist: document.getElementById('select-server-wordlist'),
        containerCustomUpload: document.getElementById('container-custom-upload'),
        wordlistDropzone: document.getElementById('wordlist-dropzone'),
        wordlistFileInput: document.getElementById('wordlist-file-input'),
        wordlistDropzoneEmpty: document.getElementById('wordlist-dropzone-empty'),
        wordlistSelectedBox: document.getElementById('wordlist-selected-box'),
        selectedWordlistName: document.getElementById('selected-wordlist-name'),
        selectedWordlistSize: document.getElementById('selected-wordlist-size'),
        btnRemoveWordlist: document.getElementById('btn-remove-wordlist'),

        // Settings
        sliderWorkers: document.getElementById('slider-workers'),
        valWorkers: document.getElementById('val-workers'),
        toggleMutations: document.getElementById('toggle-mutations'),

        // Buttons
        btnStartCrack: document.getElementById('btn-start-crack'),
        btnPauseCrack: document.getElementById('btn-pause-crack'),
        btnResumeCrack: document.getElementById('btn-resume-crack'),
        btnStopCrack: document.getElementById('btn-stop-crack'),

        // Telemetry
        statPercent: document.getElementById('stat-percent'),
        statRate: document.getElementById('stat-rate'),
        statTested: document.getElementById('stat-tested'),
        statElapsed: document.getElementById('stat-elapsed'),
        statRemaining: document.getElementById('stat-remaining'),
        statEta: document.getElementById('stat-eta'),
        statStatusText: document.getElementById('stat-status-text'),
        progressBarFill: document.getElementById('progress-bar-fill'),
        progressBarLabel: document.getElementById('progress-bar-label'),
        currentTestedPassword: document.getElementById('current-tested-password'),
        terminalLogs: document.getElementById('terminal-logs'),
        btnClearLogs: document.getElementById('btn-clear-logs'),

        // Analyzer
        btnRunAudit: document.getElementById('btn-run-audit'),
        analyzerTargetDisplay: document.getElementById('analyzer-target-display'),
        auditResultsContainer: document.getElementById('audit-results-container'),
        auditEncryptionType: document.getElementById('audit-encryption-type'),
        auditVulnerabilityLevel: document.getElementById('audit-vulnerability-level'),
        auditEntriesCount: document.getElementById('audit-entries-count'),
        auditIsEncrypted: document.getElementById('audit-is-encrypted'),
        auditRecommendationText: document.getElementById('audit-recommendation-text'),
        auditFilesTableBody: document.getElementById('audit-files-table-body'),
        btnUseAuditedInCracker: document.getElementById('btn-use-audited-in-cracker'),

        // Profiler
        formProfiler: document.getElementById('form-profiler'),
        profName: document.getElementById('prof-name'),
        profSurname: document.getElementById('prof-surname'),
        profYear: document.getElementById('prof-year'),
        profKeywords: document.getElementById('prof-keywords'),
        profResultsCount: document.getElementById('prof-results-count'),
        profWordsPreview: document.getElementById('prof-words-preview'),
        btnUseProfilerInCracker: document.getElementById('btn-use-profiler-in-cracker'),
        btnDownloadProfilerTxt: document.getElementById('btn-download-profiler-txt'),

        // Mutator
        formMutator: document.getElementById('form-mutator'),
        mutBaseWords: document.getElementById('mut-base-words'),
        ruleLeetspeak: document.getElementById('rule-leetspeak'),
        ruleYears: document.getElementById('rule-years'),
        ruleSuffixes: document.getElementById('rule-suffixes'),
        rulePrefixes: document.getElementById('rule-prefixes'),
        ruleCasing: document.getElementById('rule-casing'),
        ruleReverse: document.getElementById('rule-reverse'),
        mutResultsCount: document.getElementById('mut-results-count'),
        mutWordsPreview: document.getElementById('mut-words-preview'),
        btnUseMutatorInCracker: document.getElementById('btn-use-mutator-in-cracker'),
        btnDownloadMutatorTxt: document.getElementById('btn-download-mutator-txt'),

        // Library
        libraryWordlistsList: document.getElementById('library-wordlists-list'),
        libraryExamplesList: document.getElementById('library-examples-list'),

        // Modal
        successModal: document.getElementById('success-modal'),
        modalPasswordText: document.getElementById('modal-password-text'),
        modalTimeText: document.getElementById('modal-time-text'),
        modalTestedText: document.getElementById('modal-tested-text'),
        btnCopyPassword: document.getElementById('btn-copy-password'),
        btnCloseModal: document.getElementById('btn-close-modal'),

        // Toast Container
        toastContainer: document.getElementById('toast-container')
    };

    // --- Helper Functions ---
    function formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function formatTime(seconds) {
        if (!seconds || isNaN(seconds) || seconds < 0) return '00:00.0';
        const mins = Math.floor(seconds / 60);
        const secs = (seconds % 60).toFixed(1);
        const minsStr = mins < 10 ? '0' + mins : mins;
        const secsStr = secs < 10 ? '0' + secs : secs;
        return `${minsStr}:${secsStr}`;
    }

    function getTimestamp() {
        const d = new Date();
        const hh = String(d.getHours()).padStart(2, '0');
        const mm = String(d.getMinutes()).padStart(2, '0');
        const ss = String(d.getSeconds()).padStart(2, '0');
        return `[${hh}:${mm}:${ss}]`;
    }

    function logToTerminal(message, type = 'info') {
        const line = document.createElement('div');
        line.className = `log-line ${type}`;
        line.textContent = `${getTimestamp()} ${message}`;
        elements.terminalLogs.appendChild(line);
        elements.terminalLogs.scrollTop = elements.terminalLogs.scrollHeight;
    }

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        elements.toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    function playSuccessChime() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
            osc.frequency.setValueAtTime(880, ctx.currentTime + 0.1); // A5
            gain.gain.setValueAtTime(0.2, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.4);
        } catch (e) {
            // AudioContext not allowed or unsupported
        }
    }

    // --- Tab Navigation ---
    elements.tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            elements.tabButtons.forEach(b => b.classList.remove('active'));
            elements.tabPanes.forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            const activePane = document.getElementById(targetTab);
            if (activePane) activePane.classList.add('active');

            // Se for tab de auditoria, atualiza label do alvo
            if (targetTab === 'tab-analyzer') {
                updateAnalyzerTargetDisplay();
            }
        });
    });

    function switchTab(tabId) {
        const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
        if (btn) btn.click();
    }

    // --- Global Status Indicator ---
    function setGlobalStatus(status, label) {
        state.jobStatus = status;
        elements.globalStatusDot.className = `status-dot ${status}`;
        elements.globalStatusText.textContent = label || status.toUpperCase();
    }

    // --- Workers Slider ---
    elements.sliderWorkers.addEventListener('input', (e) => {
        elements.valWorkers.textContent = e.target.value;
    });

    // --- Wordlist Strategy Selection ---
    elements.wordlistRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const val = e.target.value;
            state.activeWordlist.type = val;

            elements.containerServerWordlist.classList.toggle('hidden', val !== 'server_file');
            elements.containerCustomUpload.classList.toggle('hidden', val !== 'custom_upload');
        });
    });

    // --- File Upload Logic (ZIP & TXT) ---
    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                return data;
            } else {
                throw new Error(data.message || 'Falha no envio do arquivo.');
            }
        } catch (err) {
            showToast(err.message, 'error');
            logToTerminal(`[-] Erro no upload: ${err.message}`, 'error');
            return null;
        }
    }

    function selectZipTarget(filepath, filename, size_bytes) {
        state.activeZip = { filepath, filename, size_bytes };
        elements.selectedZipName.textContent = filename;
        elements.selectedZipSize.textContent = formatBytes(size_bytes);
        elements.zipDropzoneEmpty.classList.add('hidden');
        elements.zipSelectedBox.classList.remove('hidden');
        logToTerminal(`[*] Alvo ZIP carregado: ${filename} (${formatBytes(size_bytes)})`, 'info');
        updateAnalyzerTargetDisplay();
    }

    function clearZipTarget() {
        state.activeZip = null;
        elements.zipFileInput.value = '';
        elements.selectZipExample.value = '';
        elements.zipSelectedBox.classList.add('hidden');
        elements.zipDropzoneEmpty.classList.remove('hidden');
        updateAnalyzerTargetDisplay();
        logToTerminal('[*] Alvo ZIP removido.', 'info');
    }

    elements.btnRemoveZip.addEventListener('click', (e) => {
        e.stopPropagation();
        clearZipTarget();
    });

    // Drag and Drop for ZIP
    elements.zipDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.zipDropzone.classList.add('dragover');
    });
    elements.zipDropzone.addEventListener('dragleave', () => {
        elements.zipDropzone.classList.remove('dragover');
    });
    elements.zipDropzone.addEventListener('drop', async (e) => {
        e.preventDefault();
        elements.zipDropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            if (!file.name.toLowerCase().endsWith('.zip')) {
                showToast('Apenas arquivos .zip são aceitos como alvo.', 'error');
                return;
            }
            logToTerminal(`[*] Enviando ${file.name}...`, 'info');
            const res = await uploadFile(file);
            if (res) {
                selectZipTarget(res.filepath, res.filename, res.size_bytes);
                showToast(`Arquivo ${file.name} carregado com sucesso!`, 'success');
            }
        }
    });

    elements.zipFileInput.addEventListener('change', async (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            logToTerminal(`[*] Enviando ${file.name}...`, 'info');
            const res = await uploadFile(file);
            if (res) {
                selectZipTarget(res.filepath, res.filename, res.size_bytes);
                showToast(`Arquivo ${file.name} carregado com sucesso!`, 'success');
            }
        }
    });

    // Drag and Drop for Wordlist TXT
    function selectWordlistTarget(filepath, filename, size_bytes) {
        state.activeWordlist.filepath = filepath;
        state.activeWordlist.filename = filename;
        state.activeWordlist.size_bytes = size_bytes;
        elements.selectedWordlistName.textContent = filename;
        elements.selectedWordlistSize.textContent = formatBytes(size_bytes);
        elements.wordlistDropzoneEmpty.classList.add('hidden');
        elements.wordlistSelectedBox.classList.remove('hidden');
        logToTerminal(`[*] Wordlist personalizada carregada: ${filename}`, 'info');
    }

    function clearWordlistTarget() {
        state.activeWordlist.filepath = null;
        state.activeWordlist.filename = null;
        elements.wordlistFileInput.value = '';
        elements.wordlistSelectedBox.classList.add('hidden');
        elements.wordlistDropzoneEmpty.classList.remove('hidden');
    }

    elements.btnRemoveWordlist.addEventListener('click', (e) => {
        e.stopPropagation();
        clearWordlistTarget();
    });

    elements.wordlistDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.wordlistDropzone.classList.add('dragover');
    });
    elements.wordlistDropzone.addEventListener('dragleave', () => {
        elements.wordlistDropzone.classList.remove('dragover');
    });
    elements.wordlistDropzone.addEventListener('drop', async (e) => {
        e.preventDefault();
        elements.wordlistDropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            if (!file.name.toLowerCase().endsWith('.txt')) {
                showToast('Apenas arquivos de texto .txt são aceitos como wordlist.', 'error');
                return;
            }
            const res = await uploadFile(file);
            if (res) {
                selectWordlistTarget(res.filepath, res.filename, res.size_bytes);
                showToast(`Wordlist ${file.name} enviada!`, 'success');
            }
        }
    });

    elements.wordlistFileInput.addEventListener('change', async (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            const res = await uploadFile(file);
            if (res) {
                selectWordlistTarget(res.filepath, res.filename, res.size_bytes);
                showToast(`Wordlist ${file.name} enviada!`, 'success');
            }
        }
    });

    // --- Load Server Wordlists and Examples ---
    async function loadServerData() {
        try {
            // Wordlists
            const wlRes = await fetch('/api/wordlists');
            const wlData = await wlRes.json();
            if (wlData.status === 'success') {
                state.serverWordlists = wlData.wordlists;
                populateServerWordlists(wlData.wordlists);
            }

            // Examples
            const exRes = await fetch('/api/examples');
            const exData = await exRes.json();
            if (exData.status === 'success') {
                state.serverExamples = exData.examples;
                populateServerExamples(exData.examples);
            }
        } catch (err) {
            console.error('Erro ao carregar dados do servidor:', err);
        }
    }

    function populateServerWordlists(wordlists) {
        elements.selectServerWordlist.innerHTML = '';
        elements.libraryWordlistsList.innerHTML = '';

        if (wordlists.length === 0) {
            elements.selectServerWordlist.innerHTML = '<option value="">Nenhuma wordlist encontrada</option>';
            elements.libraryWordlistsList.innerHTML = '<span class="empty-state-text">Nenhuma wordlist encontrada em wordlists/</span>';
            return;
        }

        wordlists.forEach(wl => {
            const opt = document.createElement('option');
            opt.value = wl.filepath;
            opt.textContent = `${wl.filename} (${wl.lines_count.toLocaleString()} termos - ${formatBytes(wl.size_bytes)})`;
            elements.selectServerWordlist.appendChild(opt);

            // Item na aba Biblioteca
            const card = document.createElement('div');
            card.className = 'library-item-card';
            card.innerHTML = `
                <div class="lib-meta-col">
                    <span class="lib-item-title">${wl.filename}</span>
                    <span class="lib-item-details">${wl.lines_count.toLocaleString()} linhas | ${formatBytes(wl.size_bytes)}</span>
                </div>
                <button type="button" class="btn btn-secondary btn-sm" data-wl-path="${wl.filepath}" data-wl-name="${wl.filename}">
                    Usar no Recuperador
                </button>
            `;
            card.querySelector('button').addEventListener('click', () => {
                document.querySelector('input[name="wordlist-source"][value="server_file"]').checked = true;
                elements.containerServerWordlist.classList.remove('hidden');
                elements.containerCustomUpload.classList.add('hidden');
                elements.selectServerWordlist.value = wl.filepath;
                state.activeWordlist.type = 'server_file';
                state.activeWordlist.filepath = wl.filepath;
                showToast(`Wordlist ${wl.filename} selecionada!`, 'info');
                switchTab('tab-cracker');
            });
            elements.libraryWordlistsList.appendChild(card);
        });
    }

    function populateServerExamples(examples) {
        elements.selectZipExample.innerHTML = '<option value="">-- Selecionar arquivo de teste --</option>';
        elements.libraryExamplesList.innerHTML = '';

        if (examples.length === 0) {
            elements.libraryExamplesList.innerHTML = '<span class="empty-state-text">Nenhum exemplo encontrado em examples/</span>';
            return;
        }

        examples.forEach(ex => {
            const opt = document.createElement('option');
            opt.value = ex.filepath;
            opt.textContent = `${ex.filename} (${formatBytes(ex.size_bytes)})`;
            elements.selectZipExample.appendChild(opt);

            // Item na aba Biblioteca
            const card = document.createElement('div');
            card.className = 'library-item-card';
            card.innerHTML = `
                <div class="lib-meta-col">
                    <span class="lib-item-title">${ex.filename}</span>
                    <span class="lib-item-details">Exemplo protegido | ${formatBytes(ex.size_bytes)}</span>
                </div>
                <div style="display:flex;gap:6px;">
                    <button type="button" class="btn btn-secondary btn-sm btn-load-ex-cracker" data-path="${ex.filepath}">Recuperar</button>
                    <button type="button" class="btn btn-secondary btn-sm btn-load-ex-audit" data-path="${ex.filepath}">Auditar</button>
                </div>
            `;
            card.querySelector('.btn-load-ex-cracker').addEventListener('click', () => {
                selectZipTarget(ex.filepath, ex.filename, ex.size_bytes);
                elements.selectZipExample.value = ex.filepath;
                showToast(`Arquivo ${ex.filename} carregado!`, 'info');
                switchTab('tab-cracker');
            });
            card.querySelector('.btn-load-ex-audit').addEventListener('click', () => {
                selectZipTarget(ex.filepath, ex.filename, ex.size_bytes);
                switchTab('tab-analyzer');
                elements.btnRunAudit.click();
            });
            elements.libraryExamplesList.appendChild(card);
        });
    }

    elements.selectZipExample.addEventListener('change', (e) => {
        const val = e.target.value;
        if (val) {
            const found = state.serverExamples.find(x => x.filepath === val);
            if (found) {
                selectZipTarget(found.filepath, found.filename, found.size_bytes);
            }
        }
    });

    // --- Cracking Controller (Start / Pause / Resume / Stop / SSE) ---
    function resetTelemetry() {
        elements.statPercent.textContent = '0.0%';
        elements.statRate.textContent = '0 /s';
        elements.statTested.textContent = '0 / 0';
        elements.statElapsed.textContent = '00:00.0';
        elements.statRemaining.textContent = '0 restantes';
        elements.statEta.textContent = 'ETA: --:--';
        elements.statStatusText.textContent = 'Em execução...';
        elements.progressBarFill.style.width = '0%';
        elements.progressBarLabel.textContent = '0.0%';
        elements.currentTestedPassword.textContent = 'Iniciando threads...';
    }

    function setControlsRunning() {
        setGlobalStatus('running', 'RECUPERANDO');
        elements.btnStartCrack.disabled = true;
        elements.btnPauseCrack.disabled = false;
        elements.btnPauseCrack.classList.remove('hidden');
        elements.btnResumeCrack.classList.add('hidden');
        elements.btnStopCrack.disabled = false;
    }

    function setControlsPaused() {
        setGlobalStatus('paused', 'PAUSADO');
        elements.btnPauseCrack.classList.add('hidden');
        elements.btnResumeCrack.classList.remove('hidden');
        elements.statStatusText.textContent = 'Recuperação pausada';
    }

    function setControlsIdle() {
        setGlobalStatus('ready', 'PRONTO');
        elements.btnStartCrack.disabled = false;
        elements.btnPauseCrack.disabled = true;
        elements.btnPauseCrack.classList.remove('hidden');
        elements.btnResumeCrack.classList.add('hidden');
        elements.btnStopCrack.disabled = true;
    }

    function connectSSE() {
        if (state.eventSource) {
            state.eventSource.close();
        }

        state.eventSource = new EventSource('/api/crack/events');

        state.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleSSEEvent(data);
            } catch (e) {
                console.error('Erro ao interpretar evento SSE:', e);
            }
        };

        state.eventSource.onerror = (err) => {
            console.warn('Conexão SSE desconectada ou finalizada.');
            if (state.jobStatus === 'running') {
                // Se ainda deveria estar rodando, tenta manter estado
            }
        };
    }

    function handleSSEEvent(data) {
        if (data.type === 'heartbeat') {
            return;
        }

        if (data.type === 'progress') {
            const percent = (data.percent || 0).toFixed(1);
            elements.statPercent.textContent = `${percent}%`;
            elements.progressBarFill.style.width = `${percent}%`;
            elements.progressBarLabel.textContent = `${percent}%`;

            elements.statRate.textContent = `${(data.rate || 0).toLocaleString()} /s`;
            elements.statTested.textContent = `${(data.tested || 0).toLocaleString()} / ${(data.total || 0).toLocaleString()}`;
            
            const remaining = Math.max(0, (data.total || 0) - (data.tested || 0));
            elements.statRemaining.textContent = `${remaining.toLocaleString()} restantes`;
            elements.statElapsed.textContent = formatTime(data.elapsed_sec || 0);
            elements.statEta.textContent = data.eta_sec ? `ETA: ${formatTime(data.eta_sec)}` : 'ETA: --:--';

            if (data.current_password) {
                elements.currentTestedPassword.textContent = data.current_password;
            }
        } else if (data.type === 'found') {
            if (state.eventSource) state.eventSource.close();
            setGlobalStatus('ready', 'CONCLUÍDO');
            setControlsIdle();

            elements.statPercent.textContent = '100.0%';
            elements.progressBarFill.style.width = '100%';
            elements.progressBarLabel.textContent = '100.0%';
            elements.statStatusText.textContent = 'SENHA ENCONTRADA!';
            elements.currentTestedPassword.textContent = data.password;

            logToTerminal(`[+] =====================================================`, 'success');
            logToTerminal(`[+] SENHA ENCONTRADA: "${data.password}"`, 'success');
            logToTerminal(`[+] Tempo: ${data.elapsed_sec || 0}s | Tentativas: ${data.tested || 0}`, 'success');
            logToTerminal(`[+] =====================================================`, 'success');

            playSuccessChime();
            showSuccessModal(data.password, data.elapsed_sec, data.tested);
        } else if (data.type === 'finished') {
            if (state.eventSource) state.eventSource.close();
            setGlobalStatus('ready', 'FINALIZADO');
            setControlsIdle();

            elements.statPercent.textContent = '100.0%';
            elements.progressBarFill.style.width = '100%';
            elements.statStatusText.textContent = 'Wordlist esgotada';
            logToTerminal(`[-] Wordlist esgotada. Nenhuma senha correspondente encontrada.`, 'warning');
            showToast('Wordlist esgotada sem correspondência.', 'info');
        } else if (data.type === 'stopped') {
            if (state.eventSource) state.eventSource.close();
            setGlobalStatus('stopped', 'INTERROMPIDO');
            setControlsIdle();
            elements.statStatusText.textContent = 'Interrompido';
            logToTerminal(`[-] Processo de recuperação cancelado pelo usuário.`, 'warning');
            showToast('Processo cancelado.', 'info');
        } else if (data.type === 'error') {
            if (state.eventSource) state.eventSource.close();
            setGlobalStatus('error', 'ERRO');
            setControlsIdle();
            logToTerminal(`[-] ERRO: ${data.message}`, 'error');
            showToast(`Erro: ${data.message}`, 'error');
        }
    }

    // Iniciar Ataque
    elements.btnStartCrack.addEventListener('click', async () => {
        if (!state.activeZip || !state.activeZip.filepath) {
            showToast('Selecione ou envie um arquivo ZIP primeiro!', 'error');
            return;
        }

        let wordlistPath = null;
        let customWords = null;

        const strategy = state.activeWordlist.type;
        if (strategy === 'all_wordlists') {
            wordlistPath = null; // backend assume wordlists/
        } else if (strategy === 'server_file') {
            wordlistPath = elements.selectServerWordlist.value;
            if (!wordlistPath) {
                showToast('Selecione uma wordlist do servidor válida.', 'error');
                return;
            }
        } else if (strategy === 'custom_upload') {
            wordlistPath = state.activeWordlist.filepath;
            if (!wordlistPath) {
                showToast('Envie um arquivo .txt de wordlist antes de iniciar.', 'error');
                return;
            }
        } else if (strategy === 'generated_pool') {
            if (!state.generatedWords || state.generatedWords.length === 0) {
                showToast('Nenhum termo gerado disponível no pool.', 'error');
                return;
            }
            customWords = state.generatedWords;
        }

        const workers = parseInt(elements.sliderWorkers.value, 10) || 8;
        const useMutations = elements.toggleMutations.checked;

        resetTelemetry();
        setControlsRunning();
        logToTerminal(`[*] Iniciando ataque contra "${state.activeZip.filename}" (${workers} threads)...`, 'attempt');

        try {
            connectSSE();

            const res = await fetch('/api/crack/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    zip_path: state.activeZip.filepath,
                    wordlist_path: wordlistPath,
                    custom_words: customWords,
                    use_mutations: useMutations,
                    workers: workers
                })
            });

            const data = await res.json();
            if (!res.ok || data.status !== 'started') {
                throw new Error(data.message || 'Erro ao iniciar job de recuperação.');
            }

            state.jobId = data.job_id;
            logToTerminal(`[*] Job registrado (${data.job_id}). Aguardando processamento multi-core...`, 'info');
        } catch (err) {
            setControlsIdle();
            if (state.eventSource) state.eventSource.close();
            showToast(err.message, 'error');
            logToTerminal(`[-] Falha ao disparar motor: ${err.message}`, 'error');
        }
    });

    // Pausar
    elements.btnPauseCrack.addEventListener('click', async () => {
        try {
            await fetch('/api/crack/pause', { method: 'POST' });
            setControlsPaused();
            logToTerminal('[*] Recuperação pausada.', 'warning');
        } catch (e) {
            console.error(e);
        }
    });

    // Retomar
    elements.btnResumeCrack.addEventListener('click', async () => {
        try {
            await fetch('/api/crack/resume', { method: 'POST' });
            setControlsRunning();
            logToTerminal('[*] Recuperação retomada.', 'info');
        } catch (e) {
            console.error(e);
        }
    });

    // Parar
    elements.btnStopCrack.addEventListener('click', async () => {
        try {
            await fetch('/api/crack/stop', { method: 'POST' });
            if (state.eventSource) state.eventSource.close();
            setControlsIdle();
            setGlobalStatus('stopped', 'PARADO');
            logToTerminal('[-] Parada forçada solicitada.', 'warning');
        } catch (e) {
            console.error(e);
        }
    });

    // Clear Terminal Logs
    elements.btnClearLogs.addEventListener('click', () => {
        elements.terminalLogs.innerHTML = '';
        logToTerminal('[*] Log limpo pelo operador.', 'info');
    });

    // --- Analyzer Logic ---
    function updateAnalyzerTargetDisplay() {
        if (state.activeZip) {
            elements.analyzerTargetDisplay.textContent = `Arquivo alvo atual: ${state.activeZip.filename} (${formatBytes(state.activeZip.size_bytes)})`;
        } else {
            elements.analyzerTargetDisplay.textContent = 'Arquivo alvo atual: Nenhum selecionado';
        }
    }

    elements.btnRunAudit.addEventListener('click', async () => {
        if (!state.activeZip || !state.activeZip.filepath) {
            showToast('Selecione ou envie um arquivo ZIP primeiro!', 'error');
            return;
        }

        elements.btnRunAudit.disabled = true;
        elements.btnRunAudit.innerHTML = '<span>Inspecionando cabeçalhos...</span>';

        try {
            const res = await fetch('/api/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filepath: state.activeZip.filepath })
            });
            const data = await res.json();

            if (!res.ok || data.status !== 'success') {
                throw new Error(data.message || 'Falha ao auditar arquivo ZIP.');
            }

            renderAuditResults(data);
            showToast('Auditoria criptográfica concluída!', 'success');
        } catch (err) {
            showToast(err.message, 'error');
            logToTerminal(`[-] Erro na auditoria: ${err.message}`, 'error');
        } finally {
            elements.btnRunAudit.disabled = false;
            elements.btnRunAudit.innerHTML = `
                <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <span>Executar Auditoria Criptográfica</span>
            `;
        }
    });

    function renderAuditResults(data) {
        elements.auditResultsContainer.classList.remove('hidden');
        elements.auditEncryptionType.textContent = data.encryption_type || 'Nenhuma';
        
        // Vulnerability Level
        const vLevel = data.vulnerability_level || 'NONE';
        elements.auditVulnerabilityLevel.textContent = vLevel;
        if (vLevel === 'HIGH') {
            elements.auditVulnerabilityLevel.className = 'badge-value' + ' ' + 'highlight-green'; // Vulnerável / Alta taxa
            elements.auditVulnerabilityLevel.style.color = '#ef4444';
        } else if (vLevel === 'MEDIUM') {
            elements.auditVulnerabilityLevel.style.color = '#f59e0b';
        } else {
            elements.auditVulnerabilityLevel.style.color = '#06b6d4';
        }

        elements.auditEntriesCount.textContent = `${data.entries_count || 0} arquivos`;
        elements.auditIsEncrypted.textContent = data.is_encrypted ? 'SIM (Protegido)' : 'NÃO';
        elements.auditIsEncrypted.className = data.is_encrypted ? 'badge-value highlight-cyan' : 'badge-value';

        elements.auditRecommendationText.textContent = data.recommendation || '';

        // Tabela de Arquivos Internos
        elements.auditFilesTableBody.innerHTML = '';
        if (data.files && data.files.length > 0) {
            data.files.forEach(f => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${f.filename}</strong></td>
                    <td>${formatBytes(f.uncompressed_size)}</td>
                    <td>${formatBytes(f.compressed_size)}</td>
                    <td>${f.is_encrypted ? '<span style="color:#ef4444">Sim</span>' : '<span style="color:#10b981">Não</span>'}</td>
                    <td>${f.encryption_type || 'N/A'}</td>
                    <td><code>${f.crc}</code></td>
                `;
                elements.auditFilesTableBody.appendChild(tr);
            });
        } else {
            elements.auditFilesTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Nenhum arquivo encontrado no cabeçalho.</td></tr>';
        }
    }

    elements.btnUseAuditedInCracker.addEventListener('click', () => {
        switchTab('tab-cracker');
    });

    // --- Profiler Logic ---
    elements.formProfiler.addEventListener('submit', async (e) => {
        e.preventDefault();

        const name = elements.profName.value.trim();
        const surname = elements.profSurname.value.trim();
        const birthYear = elements.profYear.value.trim();
        const keywords = elements.profKeywords.value.split(',').map(k => k.trim()).filter(Boolean);

        if (!name && !surname && !birthYear && keywords.length === 0) {
            showToast('Preencha ao menos um campo para gerar o perfil.', 'error');
            return;
        }

        elements.profWordsPreview.innerHTML = '<span class="empty-state-text">Gerando permutações...</span>';

        try {
            const res = await fetch('/api/profile/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    surname: surname,
                    birth_year: birthYear,
                    keywords: keywords
                })
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                state.generatedWords = data.words;
                elements.profResultsCount.textContent = `${data.total_generated.toLocaleString()} termos gerados`;
                elements.profWordsPreview.innerHTML = data.words.slice(0, 500).map(w => `<div>${w}</div>`).join('');
                if (data.words.length > 500) {
                    elements.profWordsPreview.innerHTML += `<div style="color:var(--text-dim);">... e mais ${(data.words.length - 500).toLocaleString()} termos</div>`;
                }

                elements.btnUseProfilerInCracker.disabled = false;
                elements.btnDownloadProfilerTxt.disabled = false;
                showToast(`${data.total_generated} palavras geradas com sucesso!`, 'success');
            }
        } catch (err) {
            showToast('Erro ao gerar dicionário: ' + err.message, 'error');
        }
    });

    function downloadWordsAsTxt(words, filename) {
        const blob = new Blob([words.join('\n')], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    elements.btnDownloadProfilerTxt.addEventListener('click', () => {
        if (state.generatedWords.length > 0) {
            downloadWordsAsTxt(state.generatedWords, 'wordlist_perfil.txt');
            showToast('Download da wordlist iniciado!', 'info');
        }
    });

    elements.btnUseProfilerInCracker.addEventListener('click', () => {
        if (state.generatedWords.length > 0) {
            elements.radioCardGenerated.style.display = 'flex';
            elements.generatedPoolCount.textContent = `${state.generatedWords.length.toLocaleString()} termos do profiler`;
            document.querySelector('input[name="wordlist-source"][value="generated_pool"]').checked = true;
            state.activeWordlist.type = 'generated_pool';
            elements.containerServerWordlist.classList.add('hidden');
            elements.containerCustomUpload.classList.add('hidden');
            showToast('Wordlist do profiler ativada para o ataque!', 'success');
            switchTab('tab-cracker');
        }
    });

    // --- Mutator Logic ---
    elements.formMutator.addEventListener('submit', async (e) => {
        e.preventDefault();

        const baseWords = elements.mutBaseWords.value.split('\n').map(w => w.trim()).filter(Boolean);
        if (baseWords.length === 0) {
            showToast('Insira ao menos uma palavra base para mutação.', 'error');
            return;
        }

        const rules = [];
        if (elements.ruleLeetspeak.checked) rules.push('leetspeak');
        if (elements.ruleYears.checked) rules.push('years');
        if (elements.ruleSuffixes.checked) rules.push('suffixes');
        if (elements.rulePrefixes.checked) rules.push('prefixes');
        if (elements.ruleCasing.checked) rules.push('casing');
        if (elements.ruleReverse.checked) rules.push('reverse');

        elements.mutWordsPreview.innerHTML = '<span class="empty-state-text">Processando mutações léxicas...</span>';

        try {
            const res = await fetch('/api/mutate/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    base_words: baseWords,
                    rules: rules
                })
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                state.generatedWords = data.words;
                elements.mutResultsCount.textContent = `${data.total_generated.toLocaleString()} termos mutados`;
                elements.mutWordsPreview.innerHTML = data.words.slice(0, 500).map(w => `<div>${w}</div>`).join('');
                if (data.words.length > 500) {
                    elements.mutWordsPreview.innerHTML += `<div style="color:var(--text-dim);">... e mais ${(data.words.length - 500).toLocaleString()} termos</div>`;
                }

                elements.btnUseMutatorInCracker.disabled = false;
                elements.btnDownloadMutatorTxt.disabled = false;
                showToast(`${data.total_generated} termos gerados por mutação!`, 'success');
            }
        } catch (err) {
            showToast('Erro ao aplicar mutações: ' + err.message, 'error');
        }
    });

    elements.btnDownloadMutatorTxt.addEventListener('click', () => {
        if (state.generatedWords.length > 0) {
            downloadWordsAsTxt(state.generatedWords, 'wordlist_mutacoes.txt');
            showToast('Download da wordlist iniciado!', 'info');
        }
    });

    elements.btnUseMutatorInCracker.addEventListener('click', () => {
        if (state.generatedWords.length > 0) {
            elements.radioCardGenerated.style.display = 'flex';
            elements.generatedPoolCount.textContent = `${state.generatedWords.length.toLocaleString()} termos mutados`;
            document.querySelector('input[name="wordlist-source"][value="generated_pool"]').checked = true;
            state.activeWordlist.type = 'generated_pool';
            elements.containerServerWordlist.classList.add('hidden');
            elements.containerCustomUpload.classList.add('hidden');
            showToast('Wordlist mutada ativada para o ataque!', 'success');
            switchTab('tab-cracker');
        }
    });

    // --- Success Modal & Copy Password ---
    function showSuccessModal(password, elapsed, tested) {
        elements.modalPasswordText.textContent = password;
        elements.modalTimeText.textContent = `${elapsed || 0}s`;
        elements.modalTestedText.textContent = (tested || 0).toLocaleString();
        elements.successModal.classList.remove('hidden');
    }

    elements.btnCloseModal.addEventListener('click', () => {
        elements.successModal.classList.add('hidden');
    });

    elements.btnCopyPassword.addEventListener('click', () => {
        const pwd = elements.modalPasswordText.textContent;
        navigator.clipboard.writeText(pwd).then(() => {
            showToast('Senha copiada para a área de transferência!', 'success');
        }).catch(() => {
            showToast('Falha ao copiar senha.', 'error');
        });
    });

    // --- Initial Load ---
    loadServerData();
});
