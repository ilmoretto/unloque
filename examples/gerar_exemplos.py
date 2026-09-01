import os
import subprocess
import zipfile
import tempfile

def criar_zips_exemplo(output_dir="examples"):
    os.makedirs(output_dir, exist_ok=True)

    # 1. ZIP de teste com senha 'matrix' (requisito do IFRO)
    matrix_zip = os.path.join(output_dir, "teste_matrix.zip")
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write("Conteudo confidencial recuperado com sucesso.\n")
        tmp_name = tmp.name
    
    try:
        subprocess.run(["zip", "-P", "matrix", "-q", "-j", matrix_zip, tmp_name], check=True)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

    # 2. ZIP de teste com senha 'secret2024'
    secret_zip = os.path.join(output_dir, "teste_secret.zip")
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write("Arquivo de auditoria de segredo.\n")
        tmp_name = tmp.name
    
    try:
        subprocess.run(["zip", "-P", "secret2024", "-q", "-j", secret_zip, tmp_name], check=True)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

    print(f"Exemplos criados em {output_dir}/:")
    print(f" - {matrix_zip} (senha: 'matrix')")
    print(f" - {secret_zip} (senha: 'secret2024')")

if __name__ == "__main__":
    criar_zips_exemplo()
