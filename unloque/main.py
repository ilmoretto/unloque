import sys
import os

# Adiciona o diretório raiz ao PYTHONPATH se necessário
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from unloque.cli import cli_entrypoint

def main():
    sys.exit(cli_entrypoint())

if __name__ == "__main__":
    main()
