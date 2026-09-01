# Unloque 🔓

Ferramenta modular de recuperação, auditoria criptográfica e geração contextual de senhas para arquivos ZIP protegidos.

## Características Principais

- **Core Desacoplado**: Motor criptográfico multithread e multiprocessing puro sem dependência de interface gráfica.
- **Suporte Criptográfico**: Suporte a ZipCrypto e WinZip AES (AES-128, AES-192, AES-256).
- **Interface Dual**:
  - **CLI**: Execução nativa no terminal com subcomandos (`crack`, `audit`, `profile`, `mutate`).
  - **Web GUI**: Dashboard moderna com Dark Theme, Drag & Drop e telemetria em tempo real via Server-Sent Events (SSE).
- **Auditoria de Segurança**: Análise detalhada de vulnerabilidades em cabeçalhos PKZIP.
- **Mutações Inteligentes & Profiler Contextual**: Geração de listas de senhas personalizadas baseadas em perfis e regras leetspeak/temporais.
- **Checkpoints**: Salvamento e retomada automática de ataques de longa duração.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso Rápido

### Modo Gráfico (Web GUI)
```bash
python unloque/main.py
# ou
python unloque/main.py --gui
```

### Modo Linha de Comando (CLI)
```bash
# Recuperação de senha por dicionário
python unloque/main.py crack -z arquivo.zip -w wordlist.txt

# Auditoria criptográfica de cabeçalhos
python unloque/main.py audit -z arquivo.zip

# Geração de wordlist contextual
python unloque/main.py profile -o custom_wordlist.txt

# Mutação de senhas com regras
python unloque/main.py mutate -i base.txt -o mutadas.txt
```

## Testes

```bash
python -m unittest discover -s tests -v
```
