# Unloque

Ferramenta modular de alta performance para recuperação de senhas, auditoria criptográfica de arquivos ZIP e análise contextual de dicionários. Desenvolvido para fins de pesquisa em segurança e aplicações acadêmicas, o Unloque oferece interface de linha de comando (CLI) com telemetria em tempo real e interface gráfica web local (Web GUI) baseada em Flask com streaming via Server-Sent Events (SSE).

---

## Funcionalidades

- **Motor Desacoplado Multi-Core**: Núcleo criptográfico puro em Python com paralelismo via `ThreadPoolExecutor` e processamento em lotes (_chunks_).
- **Suporte Criptográfico Abrangente**:
  - Suporte nativo a **ZipCrypto** (cifra de fluxo tradicional PKZIP).
  - Suporte a **WinZip AES** (AES-128, AES-192 e AES-256) via biblioteca `pyzipper` com fallback para utilitários de sistema (`unzip` / `7z`).
- **Varredura Inteligente de Diretórios**: Suporte para carregar diretórios inteiros de wordlists (`wordlists/`), consolidando e desduplicando termos automaticamente.
- **Interface de Linha de Comando (CLI)**:
  - Execução direta com passagem de arquivo ZIP e dicionário padrão.
  - Modo Detalhado (`-v` ou `--verbose`): Exibição sequencial das tentativas de senha.
  - Controle de Cadência (`-d` ou `--delay`): Ajuste de intervalo entre testes para apresentações e demonstrações didáticas.
  - Barra de progresso dinâmica em tempo real com indicador da senha atual.
- **Interface Gráfica Web (Flask + SSE)**:
  - Painel SPA com interface responsiva e moderna.
  - Suporte a arrastar e soltar (_drag & drop_) de arquivos ZIP e seleção de listas.
  - Telemetria contínua via Server-Sent Events (taxa de senhas/segundo, percentual, tempo decorrido e status).
- **Utilitário de Testes e Amostras**: Script integrado para criação de arquivos ZIP cifrados com senhas parametrizáveis.
- **Suíte de Testes Automatizados**: Cobertura de testes unitários para o motor criptográfico, inspeção de cabeçalhos e endpoints HTTP.

---

## Aviso Legal

Esta ferramenta foi desenvolvida estritamente para **fins educacionais e acadêmicos**. A utilização deste software para recuperação ou tentativa de acesso a arquivos sem a autorização prévia e expressa do proprietário é ilegal e contrária às normas éticas. Os autores não se responsabilizam por quaisquer danos ou utilizações indevidas decorrentes deste projeto.

---

## Como Funciona - Aspectos Técnicos

### 1. Teoria da Quebra de Senhas em Arquivos ZIP

O Unloque implementa um ataque de dicionário estruturado e inspeção de cabeçalhos contra arquivos ZIP:

1. **Inspeção de Cabeçalhos Binários**:
   - Análise das assinaturas do formato ZIP (Local File Header `0x04034b50` e Central Directory Header `0x02014b50`).
   - Leitura da flag de propósito geral (_General Purpose Bit Flag_): o bit `0x0001` (bit 0) identifica a presença de criptografia.
   - Detecção de campos extras: a presença do identificador `0x9901` no cabeçalho extra especifica o uso de criptografia WinZip AES.
2. **Processo de Verificação no ZipCrypto**:
   - Decodificação do cabeçalho de inicialização de 12 bytes.
   - O algoritmo compara o 12º byte do cabeçalho com o byte mais significativo do CRC-32 (ou da data/hora do arquivo). Se a senha for inválida, a rotina rejeita a tentativa instantaneamente sem necessidade de descomprimir a totalidade do arquivo.
3. **Processo de Verificação no WinZip AES (128, 192 e 256 bits)**:
   - Utilização de PBKDF2-HMAC-SHA1 para derivação das chaves de criptografia e integridade.
   - Validação prévia dos 2 bytes de autenticação (_password verification value_) antes da decodificação do bloco de dados.
   - Fallback de execução externa via comandos de sistema (`unzip -P` / `7z`) quando aplicável.
4. **Processamento Concorrente em Lotes (_Chunking_)**:
   - As entradas do dicionário são distribuídas em blocos entre múltiplos trabalhadores (_workers_) paralelos.
   - Ao identificar a chave correta, um sinal atômico (`threading.Event`) interrompe imediatamente as demais tarefas em execução.

---

### 2. Formulação Matemática e Algoritmos

#### A. Cifra ZipCrypto (PKZIP Tradicional)

O algoritmo ZipCrypto tradicional baseia-se em um gerador de números pseudoaleatórios (PRNG) composto por três registradores internos de 32 bits ($Key_0, Key_1, Key_2$).

**Sequência de Inicialização das Chaves:**

$$
\begin{aligned}
Key_0 &= \text{0x12345678} \\
Key_1 &= \text{0x23456789} \\
Key_2 &= \text{0x34567890}
\end{aligned}
$$

Para cada byte $b$ da senha fornecida, os registradores são atualizados recursivamente:

$$
\begin{aligned}
Key_0 &\leftarrow \text{CRC32}(Key_0, b) \\
Key_1 &\leftarrow (Key_1 + (Key_0 \ \& \ \text{0xFF})) \times \text{0x08088405} + 1 \\
Key_2 &\leftarrow \text{CRC32}(Key_2, Key_1 \gg 24)
\end{aligned}
$$

O fluxo de chave (_keystream_) é derivado a partir de $Key_2$:

$$
\begin{aligned}
temp &= Key_2 \mid 2 \\
K_i &= (temp \times (temp \oplus 1)) \gg 8
\end{aligned}
$$

A decifração do texto cifrado ($C_i$) para obtenção do texto original ($P_i$) ocorre via operação XOR:
$$P_i = C_i \oplus K_i$$

#### B. Vulnerabilidade de Texto Claro Conhecido (_Known-Plaintext Attack_)

A fragilidade estrutural do ZipCrypto decorre da previsibilidade dos primeiros 12 bytes do fluxo cifrado. Caso um atacante possua ao menos 13 bytes contíguos de texto claro conhecido (como cabeçalhos de extensões padronizadas), a relação linear:
$$K_i = P_i \oplus C_i$$
permite reconstruir os estados internos de $Key_0, Key_1, Key_2$ sem necessidade de busca exaustiva da senha original (método de Biham e Kocher).

---

#### C. WinZip AES (Advanced Encryption Standard)

Arquivos protegidos por WinZip AES utilizam a cifra de bloco Rijndael associada à derivação de chave pelo padrão PBKDF2:

1. **Derivação de Chave (PBKDF2)**:
   $$K_{enc} \parallel K_{auth} \parallel V = \text{PBKDF2-HMAC-SHA1}(\text{senha}, \text{salt}, 1000, \text{key\_len})$$
   - $K_{enc}$: Chave de cifra AES.
   - $K_{auth}$: Chave de integridade HMAC-SHA1.
   - $V$: Verificador de autenticação de 2 bytes.
2. **Transformações do AES no Campo Finito $\text{GF}(2^8)$**:
   - **SubBytes**: Substituição não-linear via matriz S-Box: $S(a_{i,j})$.
   - **ShiftRows**: Deslocamento cíclico dos vetores da matriz de estado.
   - **MixColumns**: Multiplicação polinomial modular sobre $\text{GF}(2^8)$.
   - **AddRoundKey**: Operação XOR com a subchave de rodada correspondente.

---

#### D. Complexidade Computacional e Estimativa de Tempo

A complexidade temporal do ataque de dicionário sobre um conjunto de $N$ termos é expressa por:
$$T = N \times t_{teste}$$

Para processamento concorrente em $P$ núcleos de execução:
$$T_{paralelo} = \frac{N \times t_{teste}}{P} + \epsilon$$

Onde $\epsilon$ representa a latência de escalonamento e troca de contexto entre threads.

- **ZipCrypto**: $t_{teste} \approx c_1 \cdot L + c_2$ (onde $L$ é o tamanho da senha e $c_1, c_2$ são constantes de ciclo de clock para operações CRC32).
- **WinZip AES**: $t_{teste} \approx 1000 \times t_{\text{SHA1}} + c_3 \cdot \text{Rounds}_{AES}$, exigindo consideravelmente mais ciclos de processamento devido às 1.000 iterações de hashing criptográfico.

#### E. Probabilidade de Sucesso

A probabilidade de sucesso do ataque por dicionário é modelada pela razão entre o espaço amostral do dicionário ($D$) e o espaço de escolhas do usuário ($S_{alvo}$):
$$P(\text{sucesso}) = \frac{|D \cap S_{alvo}|}{|S_{alvo}|}$$

Dicionários contextuais e especializados reduzem o espaço de busca e maximizam a probabilidade de convergência em menor tempo computacional.

---

## Requisitos do Sistema

- **Interpretador**: Python 3.8 ou superior.
- **Sistemas Operacionais**: Linux, macOS ou Windows (WSL2 / nativo).
- **Dependências Python**:
  - `Flask >= 3.0.0`
  - `pyzipper >= 0.3.6`

---

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/ilmoretto/unloque.git
cd unloque

# Instalar dependências
pip install -r requirements.txt
```

---

## Guia de Utilização

### 1. Modo Linha de Comando (CLI)

```bash
# Execução padrão (utiliza todos os dicionários contidos na pasta wordlists/)
python3 unloque/main.py examples/teste_matrix.zip

# Especificando um arquivo ou diretório de wordlists
python3 unloque/main.py examples/teste_matrix.zip wordlists/senhas_brasil.txt
python3 unloque/main.py examples/teste_matrix.zip wordlists/
```

#### Parâmetros de Execução:

- `-v`, `--verbose`: Exibe detalhadamente cada senha testada em tempo real.
- `-d`, `--delay`: Define um intervalo (em segundos) entre as tentativas para demonstrações e análises didáticas.
- `-t`, `--threads`: Define manualmente a quantidade de workers paralelos.

```bash
# Demonstração com modo detalhado e intervalo de 0.05 segundos
python3 unloque/main.py examples/teste_matrix.zip -v -d 0.05
```

---

### 2. Modo Gráfico (Web GUI)

Para inicializar o servidor local e abrir a interface web no navegador:

```bash
python3 unloque/main.py --gui
# ou execute sem argumentos:
python3 unloque/main.py
```

Acesse o endereço local: `http://127.0.0.1:5000`

---

### 3. Geração de Arquivos ZIP de Teste

Para criar arquivos ZIP protegidos com senhas customizadas para testes:

```bash
# Gerar arquivos de teste padrão ('matrix' e 'secret2024')
python3 examples/gerar_exemplos.py

# Gerar arquivo com senha específica
python3 examples/gerar_exemplos.py "senha_customizada" examples/teste_custom.zip
```

---

## Testes Automatizados

Para executar a suíte de testes unitários:

```bash
python3 -m unittest discover -s tests -v
```

---

## Estrutura do Repositório

```
unloque/
├── README.md                    # Documentação técnica do projeto
├── requirements.txt             # Declaração de dependências
├── setup.py                     # Configuração de empacotamento
├── unloque/
│   ├── main.py                  # Ponto de entrada unificado
│   ├── cli.py                   # Interface de linha de comando
│   ├── core/                    # Núcleo de processamento criptográfico
│   │   ├── __init__.py
│   │   ├── engine.py            # Motor ZipEngine e controle de threads
│   │   ├── analyzer.py          # Analisador de cabeçalhos PKZIP
│   │   ├── mutator.py           # Regras de mutação de termos
│   │   ├── profiler.py          # Gerador contextual
│   │   └── checkpoint.py        # Persistência de estado
│   └── web/                     # Servidor Web Flask e assets da interface
│       ├── app.py               # Configuração da aplicação Flask
│       ├── routes.py            # Endpoints REST e fluxo SSE
│       ├── INSTRUCOES.md        # Especificação técnica da API
│       ├── static/              # Folhas de estilo e scripts frontend
│       └── templates/           # Estrutura HTML da interface gráfica
├── wordlists/                   # Bases de dicionários
├── examples/                    # Utilitários de geração de amostras
└── tests/                       # Testes automatizados com unittest
```

---

## Autores

- **Alencar Morete**
- **Emily Chagas**   

---

## Licença

Este projeto é distribuído sob a licença **MIT**. Consulte o arquivo `LICENSE` para mais detalhes.
