# Unloque 🔓

Ferramenta modular de recuperação, auditoria criptográfica e geração contextual de senhas para arquivos ZIP protegidos.

---

## 🚀 Características Principais

- **Core Desacoplado**: Motor criptográfico multithread e multiprocessing puro sem dependência de interface gráfica.
- **Suporte Criptográfico Completo**: Suporte a **ZipCrypto** e **WinZip AES** (AES-128, AES-192, AES-256).
- **Varredura Flexível de Dicionários**: Suporta arquivos `.txt` individuais ou **diretórios inteiros** (ex: `wordlists/`) com desduplicação automática.
- **Telemetria em Tempo Real**: Métricas instantâneas de velocidade (senhas/s), tempo decorrido, porcentagem e estimativa de término (ETA).
- **Interface Dual**:
  - **CLI**: Execução nativa no terminal com subcomandos (`crack`, `audit`, `profile`, `mutate`).
  - **Web GUI**: Dashboard moderna com Dark Theme, Drag & Drop e streaming via Server-Sent Events (SSE).
- **Auditoria de Segurança**: Análise detalhada de vulnerabilidades em cabeçalhos PKZIP.

---

## 📦 Instalação

```bash
# Instalação das dependências
pip install -r requirements.txt
```

---

## 🛠️ Comandos de Uso e Teste

### 1. Gerar Arquivos ZIP de Teste
Cria arquivos protegidos de exemplo na pasta `examples/` (inclui a senha `matrix` solicitada na disciplina):
```bash
python3 examples/gerar_exemplos.py
```

---

### 2. Executar a Suíte de Testes Automatizados
Roda todos os testes unitários do motor de recuperação:
```bash
python3 -m unittest discover -s tests -v
```

---

### 3. Recuperação de Senha com o Motor (`ZipEngine`)

#### A. Usando uma Wordlist Específica
```bash
python3 -c "
from unloque.core.engine import ZipEngine

engine = ZipEngine('examples/teste_matrix.zip')
result = engine.crack('wordlists/senhas_comuns.txt')

print(f'Status:           {result.status}')
print(f'Senha Encontrada: {result.password}')
print(f'Tempo Decorrido:  {result.elapsed:.4f}s')
print(f'Taxa de Teste:    {result.rate:.2f} senhas/s')
"
```

#### B. Passando a Pasta `wordlists/` Inteira (Varredura Consolidada)
```bash
python3 -c "
from unloque.core.engine import ZipEngine

engine = ZipEngine('examples/teste_matrix.zip')
result = engine.crack('wordlists/')

print(f'Status:           {result.status}')
print(f'Senha Encontrada: {result.password}')
print(f'Total Testadas:   {result.tested}/{result.total}')
print(f'Taxa de Teste:    {result.rate:.2f} senhas/s')
"
```

#### C. Acompanhamento de Telemetria em Tempo Real
```bash
python3 -c "
from unloque.core.engine import ZipEngine

engine = ZipEngine('examples/teste_matrix.zip')
for ev in engine.crack_generator('wordlists/', chunk_size=10):
    print(f'[{ev.status.upper()}] Testadas: {ev.tested}/{ev.total} | {ev.percent:.1f}% | Taxa: {ev.rate:.1f} s/s')
    if ev.found:
        print(f'>>> SUCESSO! Senha: {ev.password}')
"
```

---

### 4. Modo Linha de Comando (CLI)

```bash
# Recuperação de senha por arquivo ou pasta de wordlists
python unloque/main.py crack -z examples/teste_matrix.zip -w wordlists/

# Auditoria criptográfica de cabeçalhos PKZIP
python unloque/main.py audit -z examples/teste_matrix.zip

# Geração de wordlist contextual baseada em perfil
python unloque/main.py profile -o custom_wordlist.txt

# Mutação de senhas com regras inteligentes (leetspeak, anos, sufixos)
python unloque/main.py mutate -i wordlists/senhas_comuns.txt -o mutadas.txt
```

---

### 5. Modo Gráfico (Web GUI)

Inicia o servidor local Flask e abre automaticamente o navegador padrão:
```bash
python unloque/main.py
# ou
python unloque/main.py --gui
```
Ou para rodar apenas o servidor Flask de desenvolvimento:
```bash
python -m unloque.web.app
```
Acesse em: `http://127.0.0.1:5000`

---

## 📁 Estrutura do Projeto

```
unloque/
├── README.md                    # Este documento
├── requirements.txt             # Dependências Python
├── setup.py                     # Empacotamento do CLI
├── unloque/
│   ├── core/                    # Motor criptográfico desacoplado
│   │   ├── engine.py            # Motor de recuperação multithread
│   │   ├── analyzer.py          # Auditor de cabeçalhos PKZIP
│   │   ├── mutator.py           # Gerador de mutações de senha
│   │   └── profiler.py          # Gerador contextual de wordlists
│   ├── cli.py                   # Interface de linha de comando
│   ├── main.py                  # Ponto de entrada unificado
│   └── web/                     # Servidor Web Flask e SPA
├── wordlists/                   # Dicionários prontos (senhas comuns, Brasil, PINs, Top500)
├── examples/                    # Gerador de ZIPs e amostras para teste
└── tests/                       # Testes unitários com unittest
```
