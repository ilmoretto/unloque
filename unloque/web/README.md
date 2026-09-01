# Guia de Integração: Módulo Web (Flask API & SSE)

Este documento especifica os contratos de integração entre o backend Flask (`unloque.web`) e o frontend/interface visual. Use este guia para construir ou plugar qualquer interface gráfica (HTML/CSS/JS) sem quebrar o funcionamento do sistema.

---

## 1. Visão Geral da Integração

O módulo web atua como uma ponte de comunicação assíncrona entre a interface do usuário e o motor criptográfico (`unloque.core`).

```
[ Frontend (Browser / SPA) ]
       │            ▲
 REST Requests  SSE Stream (/api/crack/events)
       ▼            │
[ Flask Server (unloque.web) ]
       │
       ▼
[ Core Engine (unloque.core) ]
```

---

## 2. Contratos de API REST

Todos os endpoints retornam dados em formato JSON (exceto o stream SSE).

### A. Upload de Arquivos
* **Rota**: `POST /api/upload`
* **Content-Type**: `multipart/form-data`
* **Form Data**:
  * `file`: Arquivo `.zip` (alvo) ou `.txt` (wordlist)
* **Resposta de Sucesso (`200 OK`)**:
  ```json
  {
    "status": "success",
    "filepath": "/caminho/temporario/arquivo.zip",
    "filename": "arquivo.zip",
    "size_bytes": 1048576
  }
  ```
* **Resposta de Erro (`400 Bad Request`)**:
  ```json
  {
    "status": "error",
    "message": "Extensao de arquivo nao permitida. Apenas .zip e .txt sao suportados."
  }
  ```

---

### B. Auditoria Criptográfica
Inspeciona os cabeçalhos PKZIP e informa o tipo de cifra e vulnerabilidade.

* **Rota**: `POST /api/audit`
* **Content-Type**: `application/json`
* **Payload**:
  ```json
  {
    "filepath": "/caminho/temporario/arquivo.zip"
  }
  ```
* **Resposta de Sucesso (`200 OK`)**:
  ```json
  {
    "status": "success",
    "is_encrypted": true,
    "encryption_type": "WinZip AES-256",
    "vulnerability_level": "LOW",
    "entries_count": 3,
    "files": [
      {
        "filename": "documento.pdf",
        "compressed_size": 10240,
        "uncompressed_size": 20480,
        "is_encrypted": true
      }
    ],
    "recommendation": "Cifra AES-256 detectada. Recomenda-se ataque por dicionario com regras de mutacao."
  }
  ```

---

### C. Recuperação de Senha (Cracker)

#### Iniciar Ataque
* **Rota**: `POST /api/crack/start`
* **Content-Type**: `application/json`
* **Payload**:
  ```json
  {
    "zip_path": "/caminho/temporario/alvo.zip",
    "wordlist_path": "/caminho/temporario/senhas.txt",
    "use_mutations": false,
    "workers": 4
  }
  ```
  *(Nota: Se `wordlist_path` for omitido ou vazio, o backend usará a wordlist padrão `wordlists/senhas_comuns.txt`)*
* **Resposta de Sucesso (`200 OK`)**:
  ```json
  {
    "status": "started",
    "job_id": "job_001"
  }
  ```

#### Controles do Processo (Pausar / Retomar / Parar)
* **Rotas**:
  * `POST /api/crack/pause`
  * `POST /api/crack/resume`
  * `POST /api/crack/stop`
* **Content-Type**: `application/json`
* **Payload**:
  ```json
  {
    "job_id": "job_001"
  }
  ```
* **Resposta de Sucesso (`200 OK`)**:
  ```json
  {
    "status": "paused" // ou "resumed" ou "stopped"
  }
  ```

---

### D. Profiler & Mutações

#### Gerador de Wordlist Contextual (Profiler)
* **Rota**: `POST /api/profile/generate`
* **Content-Type**: `application/json`
* **Payload**:
  ```json
  {
    "name": "João",
    "surname": "Silva",
    "birth_year": "1995",
    "keywords": ["financeiro", "empresa", "2024"]
  }
  ```
* **Resposta de Sucesso (`200 OK`)**:
  ```json
  {
    "status": "success",
    "total_generated": 150,
    "words": ["joao1995", "Silva@1995", "financeiro2024"]
  }
  ```

#### Gerador de Mutações de Senha
* **Rota**: `POST /api/mutate/generate`
* **Content-Type**: `application/json`
* **Payload**:
  ```json
  {
    "base_words": ["admin", "teste"],
    "rules": ["leetspeak", "years", "suffixes"]
  }
  ```
* **Resposta de Sucesso (`200 OK`)**:
  ```json
  {
    "status": "success",
    "total_generated": 84,
    "words": ["adm1n", "@dmin2026!", "t3st3!"]
  }
  ```

---

## 3. Contrato de Telemetria em Tempo Real (SSE)

A comunicação de progresso e resultados da recuperação é enviada via **Server-Sent Events** (SSE).

* **Rota**: `GET /api/crack/events`
* **Header**: `Content-Type: text/event-stream`

### Formatos de Mensagem (`data:`):

1. **Progresso Periódico**:
   ```json
   {
     "type": "progress",
     "tested": 2500,
     "total": 10000,
     "rate": 450.2,
     "percent": 25.0,
     "elapsed_sec": 5.5,
     "eta_sec": 16.5
   }
   ```

2. **Senha Encontrada com Sucesso**:
   ```json
   {
     "type": "found",
     "password": "matrix",
     "elapsed_sec": 4.2,
     "tested": 1520
   }
   ```

3. **Processo Finalizado (Senha não encontrada)**:
   ```json
   {
     "type": "finished",
     "found": false,
     "total_tested": 10000,
     "elapsed_sec": 22.1
   }
   ```

4. **Erro durante o processamento**:
   ```json
   {
     "type": "error",
     "message": "Arquivo ZIP corrompido ou formato incompatível."
   }
   ```

---

## 4. Exemplo de Conexão no Frontend (JavaScript)

```javascript
// 1. Ouvir telemetria em tempo real
const eventSource = new EventSource('/api/crack/events');

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);

  if (data.type === 'progress') {
    console.log(`Progresso: ${data.percent}% | Taxa: ${data.rate} senhas/s`);
  } else if (data.type === 'found') {
    console.log(`Senha encontrada: ${data.password}`);
    eventSource.close();
  } else if (data.type === 'finished') {
    console.log('Fim do processamento (senha não encontrada)');
    eventSource.close();
  }
};

// 2. Disparar início de ataque
async function iniciarAtaque(zipPath, wordlistPath) {
  const response = await fetch('/api/crack/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ zip_path: zipPath, wordlist_path: wordlistPath })
  });
  return await response.json();
}
```

---

## 5. Como Executar o Servidor para Testes de Integração

```bash
# Iniciar o servidor Flask localmente
python -m unloque.web.app
```
O servidor estará acessível em: **`http://127.0.0.1:5000`**
