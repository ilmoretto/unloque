# Unloque 🔓

Ferramenta modular de recuperação, auditoria criptográfica e geração contextual de senhas para arquivos ZIP protegidos.

---

## 🚀 Uso Simplificado (Linha de Comando)

Você pode passar **apenas o arquivo ZIP** (o programa usará a pasta `wordlists/` por padrão) ou especificar um arquivo/pasta de dicionários:

```bash
# 1. Recuperação padrão com barra de progresso e senha atual em tempo real
python3 unloque/main.py examples/teste_matrix.zip

# 2. Modo Visual Detalhado (exibe cada senha testada linha a linha)
python3 unloque/main.py examples/teste_matrix.zip -v

# 3. Modo Demonstração ao Vivo em Aula (com delay para visualização clara no projetor)
python3 unloque/main.py examples/teste_matrix.zip -v -d 0.05
```

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
# Gera os arquivos padrão ('matrix' e 'secret2024')
python3 examples/gerar_exemplos.py

# Ou cria um ZIP de teste com a senha que você quiser:
python3 examples/gerar_exemplos.py "minhasenha" examples/teste_custom.zip
```

### 2. Executar a Suíte de Testes Automatizados
Roda todos os testes unitários do motor e da API:
```bash
python3 -m unittest discover -s tests -v
```

### 3. Modo Gráfico (Web GUI)
Inicia o servidor local Flask e abre automaticamente o navegador padrão:
```bash
python3 unloque/main.py --gui
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
│   ├── cli.py                   # Interface de linha de comando simplificada
│   ├── main.py                  # Ponto de entrada unificado
│   └── web/                     # Servidor Web Flask e SPA
├── wordlists/                   # Dicionários prontos (senhas comuns, Brasil, PINs, Top500)
├── examples/                    # Gerador de ZIPs e amostras para teste
└── tests/                       # Testes unitários com unittest
```
