import sys
import os
import subprocess
import tempfile

def criar_zip_com_senha(senha: str, output_zip: str = None, conteudo: str = "Arquivo protegido de teste.") -> str:
    """Cria um arquivo ZIP protegido por senha."""
    if output_zip is None:
        safe_name = "".join(c for c in senha if c.isalnum() or c in ("-", "_")) or "custom"
        output_zip = os.path.join("examples", f"teste_{safe_name}.zip")
    
    os.makedirs(os.path.dirname(os.path.abspath(output_zip)), exist_ok=True)

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write(conteudo + "\n")
        tmp_name = tmp.name

    try:
        subprocess.run(["zip", "-P", senha, "-q", "-j", output_zip, tmp_name], check=True)
        print(f"[+] ZIP criado com sucesso:")
        print(f"    - Arquivo: {output_zip}")
        print(f"    - Senha:   '{senha}'")
        return output_zip
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

def criar_zips_padrao():
    """Gera os arquivos padrão de teste."""
    print("Gerando arquivos ZIP de teste padrão...")
    criar_zip_com_senha("matrix", "examples/teste_matrix.zip", "Parabéns! Senha 'matrix' recuperada.")
    criar_zip_com_senha("secret2024", "examples/teste_secret.zip", "Parabéns! Senha 'secret2024' recuperada.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        nova_senha = sys.argv[1]
        nome_arquivo = sys.argv[2] if len(sys.argv) > 2 else None
        criar_zip_com_senha(nova_senha, nome_arquivo)
    else:
        criar_zips_padrao()
