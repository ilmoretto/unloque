# Unloque

<p align="center">
  <strong>Ferramenta modular de alta performance para recuperação de senhas, auditoria criptográfica de arquivos ZIP e análise contextual de dicionários.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/SSE-Real--Time-06B6D4?style=for-the-badge" alt="SSE Real-Time">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

---

## Sumário

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Interface Gráfica Web (Web GUI)](#interface-gráfica-web-web-gui)
- [Como Funciona - Aspectos Técnicos](#como-funciona---aspectos-técnicos)
  - [1. Teoria da Quebra de Senhas em Arquivos ZIP](#1-teoria-da-quebra-de-senhas-em-arquivos-zip)
  - [2. Formulação Matemática e Algoritmos](#2-formulação-matemática-e-algoritmos)
- [Requisitos do Sistema](#requisitos-do-sistema)
- [Instalação](#instalação)
- [Guia de Utilização](#guia-de-utilização)
  - [1. Modo Gráfico (Web GUI)](#1-modo-gráfico-web-gui)
  - [2. Modo Linha de Comando (CLI)](#2-modo-linha-de-comando-cli)
  - [3. Geração de Amostras ZIP de Teste](#3-geração-de-amostras-zip-de-teste)
- [Testes Automatizados](#testes-automatizados)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Autores](#autores)
- [Aviso Legal e Diretrizes Éticas](#aviso-legal-e-diretrizes-éticas)

---

## Visão Geral

O **Unloque** é uma solução completa desenvolvida para fins de pesquisa em segurança da informação, auditoria de arquivos compactados e aplicações acadêmicas. O sistema integra um núcleo computacional multi-thread de alto rendimento com duas interfaces de operação:
1. **Interface de Linha de Comando (CLI)**: Projetada para automação, pipelines e auditorias com telemetria direta no terminal.
2. **Interface Gráfica Web (Web GUI)**: Painel SPA moderno construído com Flask e streaming de telemetria em tempo real via Server-Sent Events (SSE).

---

## Funcionalidades

- **Motor Criptográfico Multi-Core**: Paralelismo de threads (`ThreadPoolExecutor`) com processamento em lotes (_chunks_) e cancelamento atômico instantâneo.
- **Suporte Criptográfico Abrangente**:
  - Suporte nativo a **ZipCrypto** (cifra de fluxo tradicional PKZIP).
  - Suporte a **WinZip AES** (AES-128, AES-192 e AES-256) via biblioteca `pyzipper` com fallback para utilitários de sistema (`unzip` / `7z`).
- **Auditoria Criptográfica de Cabeçalhos (PKZIP Analyzer)**:
  - Inspeção de assinaturas binárias, extração de metadados, identificação da cifra e avaliação do nível de vulnerabilidade estrutural.
- **Profiler Contextual (Engenharia Social / OSINT)**:
  - Gerador de wordlists direcionadas combinando nome, sobrenome, anos, datas e palavras-chave com regras de capitalização e remoção de acentuação.
- **Mutador de Senhas**:
  - Expansão léxica baseada em regras de leetspeak ($a \rightarrow 4/@, e \rightarrow 3, i \rightarrow 1, s \rightarrow 5/\$), sufixos, prefixos, anos correntes e inversão de caracteres.
- **Varredura Inteligente de Diretórios**: Carregamento recursivo e desduplicação automática de múltiplos dicionários contidos na pasta `wordlists/`.
- **Interface Gráfica Web (Web GUI)**:
  - Painel responsivo em tema *Dark SecOps* com animações fluidas.
  - Suporte completo a _drag & drop_ para arquivos ZIP e arquivos `.txt`.
  - Telemetria contínua via Server-Sent Events (SSE): taxa de senhas por segundo, percentual, tempo decorrido, ETA e visualizador da senha testada em tempo real.
  - Controles de execução: Iniciar, Pausar, Retomar e Parar.
  - Terminal interativo com histórico de logs coloridos com timestamps.
  - Modal comemorativo de recuperação com cópia da senha para a área de transferência em um clique.
- **Suíte de Testes Automatizados**: Cobertura completa de testes unitários e de integração (`unittest`).

---

## Interface Gráfica Web (Web GUI)

A Web GUI do Unloque organiza as operações em 5 módulos:

| Aba | Descrição |
| :--- | :--- |
| **Recuperador (Cracker)** | Painel principal de ataque com seleção de alvos por drag & drop ou exemplos do servidor, configuração de workers, estratégias de wordlists e telemetria em tempo real. |
| **Auditoria Criptográfica** | Inspeção detalhada de cabeçalhos PKZIP, tabela de arquivos internos (comprimido, descomprimido, CRC-32) e parecer técnico de segurança. |
| **Profiler Contextual** | Gerador inteligente de dicionários para ataques direcionados baseados em dados de inteligência e perfil pessoal. |
| **Mutador de Senhas** | Ferramenta de transformação léxica com filtros de leetspeak, sufixos e permutações de caixa. |
| **Biblioteca & Exemplos** | Catálogo centralizado de wordlists e amostras ZIP protegidas para testes rápidos com um clique. |

---

## Como Funciona - Aspectos Técnicos

### 1. Teoria da Quebra de Senhas em Arquivos ZIP

O Unloque implementa ataque estruturado por dicionário e inspeção de cabeçalhos binários:

1. **Inspeção de Cabeçalhos Binários**:
   - Análise das assinaturas de formato ZIP (Local File Header `0x04034b50` e Central Directory Header `0x02014b50`).
   - Leitura da flag de propósito geral (_General Purpose Bit Flag_): o bit `0x0001` (bit 0) identifica a presença de criptografia.
   - Detecção de campos extras: a presença do identificador `0x9901` no cabeçalho extra especifica o uso de criptografia WinZip AES.
2. **Processo de Verificação no ZipCrypto**:
   - Decodificação do cabeçalho de inicialização de 12 bytes.
   - O algoritmo compara o 12º byte do cabeçalho com o byte mais significativo do CRC-32 (ou da data/hora do arquivo). Se a senha for inválida, a rotina rejeita a tentativa instantaneamente sem necessidade de descomprimir a totalidade do arquivo.
3. **Processo de Verificação no WinZip AES (128, 192 e 256 bits)**:
   - Utilização de PBKDF2-HMAC-SHA1 para derivação das chaves de criptografia e integridade.
   - Validação prévia dos 2 bytes de autenticação (_password verification value_) antes da decodificação do bloco de dados.
4. **Processamento Concorrente em Lotes (_Chunking_)**:
   - As entradas do dicionário são distribuídas em lotes entre múltiplos trabalhadores (_workers_) paralelos.
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

---

## Requisitos do Sistema

- **Interpretador**: Python 3.8 ou superior.
- **Sistemas Operacionais**: Linux, macOS ou Windows (Nativo ou WSL2).
- **Navegador Moderno**: Chrome, Firefox, Edge, Safari ou Brave (para a Web GUI).
- **Dependências Python**:
  - `Flask >= 3.0.0`
  - `pyzipper >= 0.3.6`
  - `Werkzeug >= 3.0.0`

---

## Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/ilmoretto/unloque.git
cd unloque

# 2. Criar e ativar ambiente virtual (recomendado)
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# 3. Instalar dependências
pip install -r requirements.txt
```

---

## Guia de Utilização

### 1. Modo Gráfico (Web GUI)

Para inicializar o servidor local e abrir a interface gráfica automaticamente no navegador:

```bash
python unloque/main.py --gui
# ou execute sem argumentos:
python unloque/main.py
```

O painel estará acessível no endereço: **`http://127.0.0.1:5000`**

---

### 2. Modo Linha de Comando (CLI)

```bash
# Execução padrão (utiliza todos os dicionários contidos na pasta wordlists/)
python unloque/main.py examples/teste_matrix.zip

# Especificando um arquivo ou diretório de wordlists
python unloque/main.py examples/teste_matrix.zip wordlists/senhas_brasil.txt
python unloque/main.py examples/teste_matrix.zip wordlists/
```

#### Parâmetros de Execução CLI:

- `-v`, `--verbose`: Exibe detalhadamente cada tentativa de senha linha a linha.
- `-d`, `--delay`: Define um intervalo (em segundos) entre as tentativas para demonstrações e análises didáticas.
- `-t`, `--threads`: Define manualmente a quantidade de threads/workers paralelos.
- `--gui`: Força a inicialização no modo Web GUI.

```bash
# Exemplo didático com modo detalhado e cadência de 0.05s
python unloque/main.py examples/teste_matrix.zip -v -d 0.05
```

---

### 3. Geração de Amostras ZIP de Teste

Para criar arquivos ZIP protegidos com senhas customizadas para testes práticos:

```bash
# Gerar arquivos de teste padrão ('matrix' e 'secret2024')
python examples/gerar_exemplos.py

# Gerar arquivo com senha específica
python examples/gerar_exemplos.py "senha_customizada" examples/teste_custom.zip
```

---

## Testes Automatizados

A suíte de testes cobre o motor de processamento, o auditor de cabeçalhos, o profiler, o mutador e todos os endpoints da API REST:

```bash
python -m unittest discover -s tests -v
```

---

## Estrutura do Repositório

```
unloque/
├── README.md                    # Documentação técnica e guia do projeto
├── requirements.txt             # Declaração de dependências do Python
├── setup.py                     # Configuração de empacotamento
├── unloque/
│   ├── main.py                  # Ponto de entrada unificado (CLI / Web GUI)
│   ├── cli.py                   # Interface de linha de comando e telemetria
│   ├── core/                    # Núcleo criptográfico de alta performance
│   │   ├── __init__.py
│   │   ├── engine.py            # Motor ZipEngine, paralelismo e eventos
│   │   ├── analyzer.py          # Auditor de cabeçalhos PKZIP e cifras
│   │   ├── profiler.py          # Gerador de wordlists contextuais (OSINT)
│   │   ├── mutator.py           # Regras de mutação e expansão léxica
│   │   └── checkpoint.py        # Gerenciamento e persistência de estado
│   └── web/                     # Servidor Web Flask e frontend SPA
│       ├── __init__.py
│       ├── app.py               # Fábrica da aplicação Flask
│       ├── routes.py            # Rotas REST e streaming SSE
│       ├── README.md            # Especificação técnica dos contratos da API
│       ├── static/              # Folhas de estilo e scripts frontend
│       │   ├── css/style.css    # Estilização Dark SecOps
│       │   └── js/app.js        # Lógica client-side e streaming SSE
│       └── templates/
│           └── index.html       # Estrutura HTML5 da interface gráfica
├── wordlists/                   # Dicionários de senhas e PINs
├── examples/                    # Amostras criptografadas e script gerador
└── tests/                       # Testes automatizados com unittest
```

---

## Autores

- **Alencar Morete**
- **Emily Chagas**

---

## Licença

Este projeto é distribuído sob a licença **MIT**. Consulte o arquivo `LICENSE` para mais detalhes.

---

## Aviso Legal e Diretrizes Éticas

> [!CAUTION]
> ### USO RESTRITO A FINS EDUCATIVOS E ACADÊMICOS
> 
> Esta ferramenta foi projetada, desenvolvida e disponibilizada estritamente para **fins educacionais, acadêmicos e de pesquisa em cibersegurança**.
> 
> A utilização deste software para recuperar senhas, auditar, tentar acessar, interceptar ou decifrar arquivos, dados ou sistemas de terceiros **sem a prévia, expressa e formal autorização do legítimo proprietário é expressamente proibida e configura crime**.
> 
> A violação de dispositivos e o acesso não autorizado a sistemas computacionais estão tipificados e sujeitos a rigorosas penalidades na legislação brasileira, incluindo, mas não se limitando a:
> 
> 1. **Lei nº 12.737/2012 (Lei dos Crimes Cibernéticos / "Lei Carolina Dieckmann")**:
>    - Altera o Código Penal Brasileiro (Decreto-Lei nº 2.848/1940), tipificando no **Artigo 154-A** o crime de **Invasão de Dispositivo Informático**:
>      > *"Invadir dispositivo informático de uso alheio, conectado ou não à rede de computadores, com ou sem violação indevida de mecanismo de segurança e a fim de obter, adulterar ou destruir dados ou informações sem autorização expressa ou tácita do usuário do dispositivo ou de instalar vulnerabilidades para obter vantagem ilícita."*
>      > **Pena**: Reclusão, de 1 (um) a 4 (quatro) anos, e multa, podendo ser agravada para 2 (dois) a 5 (cinco) anos caso decorra na obtenção de conteúdo de comunicações eletrônicas privadas, segredos comerciais ou industriais, informações sigilosas.
> 
> 2. **Marco Civil da Internet (Lei nº 12.965/2014)**:
>    - Estabelece os princípios, garantias, direitos e deveres para o uso da Internet no Brasil, assegurando a **inviolabilidade da intimidade e da vida privada, a inviolabilidade e o sigilo do fluxo de comunicações pela internet e das comunicações privadas armazenadas** (Art. 7º, incisos I, II e III).
> 
> 3. **Lei Geral de Proteção de Dados Pessoais - LGPD (Lei nº 13.709/2018)**:
>    - Protege os direitos fundamentais de liberdade, privacidade e o livre desenvolvimento da personalidade da pessoa natural contra o tratamento e acesso ilícito a dados pessoais.
> 
> Os desenvolvedores, mantenedores e colaboradores deste repositório **isentam-se de qualquer responsabilidade civil ou penal** decorrente do uso inadequado, antiético, ilícito ou criminoso das ferramentas, técnicas e códigos disponibilizados neste projeto. O usuário assume total responsabilidade pelas suas ações e pela conformidade com as leis vigentes.
