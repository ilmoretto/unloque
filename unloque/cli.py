import sys
import os
import time
import argparse
from unloque.core.engine import ZipEngine

def format_rate(rate: float) -> str:
    if rate >= 1000:
        return f"{rate/1000:.1f}k/s"
    return f"{rate:.1f}/s"

def run_crack(zip_path: str, wordlist_target: str = "wordlists", workers: int = None, verbose: bool = False, delay: float = None):
    if not os.path.exists(zip_path):
        print(f"[-] Erro: Arquivo ZIP não encontrado: {zip_path}")
        sys.exit(1)

    if not os.path.exists(wordlist_target):
        repo_wordlists = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wordlists")
        if os.path.exists(repo_wordlists):
            wordlist_target = repo_wordlists
        else:
            print(f"[-] Erro: Wordlist ou pasta não encontrada: {wordlist_target}")
            sys.exit(1)

    # No modo verbose, define uma velocidade visual confortável (0.04s por tentativa) se o delay não for especificado
    if verbose:
        if delay is None:
            delay = 0.04
    else:
        if delay is None:
            delay = 0.0

    print("=" * 65)
    print(" 🔓 UNLOQUE - Recuperador de Senhas ZIP")
    print("=" * 65)
    print(f" [*] Alvo:       {zip_path}")
    print(f" [*] Dicionário: {wordlist_target}")
    if verbose:
        print(f" [*] Modo:       Visual Detalhado (Velocidade ajustada: {delay}s por teste)")
    print(" [*] Iniciando processamento...")
    print("-" * 65)

    try:
        engine = ZipEngine(zip_path)
    except Exception as e:
        print(f"[-] Erro ao inspecionar ZIP: {e}")
        sys.exit(1)

    last_print = 0

    try:
        for stats in engine.crack_generator(wordlist_target, workers=workers, chunk_size=1 if verbose else 20):
            if delay > 0:
                time.sleep(delay)

            current_pwd = (stats.current_password[:18] + "..") if len(stats.current_password) > 20 else stats.current_password

            if verbose:
                if stats.found:
                    print(f" [+] [{stats.tested:5d}/{stats.total:5d}] TESTANDO: '{stats.current_password}' -> \033[92mSUCESSO!\033[0m")
                else:
                    print(f" [-] [{stats.tested:5d}/{stats.total:5d}] Testando: '{stats.current_password}' -> Falhou")
            else:
                now = time.time()
                if now - last_print > 0.04 or stats.found or stats.status in ("exhausted", "stopped", "error"):
                    last_print = now
                    bar_len = 18
                    filled = int(bar_len * (stats.percent / 100.0))
                    bar = "█" * filled + "░" * (bar_len - filled)
                    
                    status_line = f"\r [{bar}] {stats.percent:5.1f}% | {stats.tested:,}/{stats.total:,} | {format_rate(stats.rate):>8} | \033[36m'{current_pwd}'\033[0m       "
                    sys.stdout.write(status_line)
                    sys.stdout.flush()

            if stats.found:
                print("\n" + "=" * 65)
                print(f" [+] \033[92mSENHA ENCONTRADA COM SUCESSO!\033[0m")
                print(f" [+] Senha:          \033[1;92m{stats.password}\033[0m")
                print(f" [+] Tempo decorrido: {stats.elapsed:.4f}s")
                print(f" [+] Taxa média:      {format_rate(stats.rate)}")
                print(f" [+] Senhas testadas: {stats.tested:,} de {stats.total:,}")
                print("=" * 65)
                return 0

            if stats.status == "exhausted":
                print("\n" + "-" * 65)
                print(f" [-] Wordlist esgotada. Nenhuma senha correspondente encontrada.")
                print(f" [-] Total testado: {stats.tested:,} em {stats.elapsed:.2f}s ({format_rate(stats.rate)})")
                print("-" * 65)
                return 1

            if stats.status == "error":
                print(f"\n[-] Erro durante a recuperação: {stats.message}")
                return 1

    except KeyboardInterrupt:
        engine.stop()
        print("\n[-] Processo interrompido pelo usuário.")
        return 130

    return 0

def cli_entrypoint():
    parser = argparse.ArgumentParser(
        description="Unloque - Recuperador de senhas para arquivos ZIP",
        usage="%(prog)s [arquivo_zip] [wordlist_ou_pasta] [opcoes]"
    )
    
    parser.add_argument("zip_file", nargs="?", help="Caminho do arquivo ZIP protegido.")
    parser.add_argument("wordlist", nargs="?", default="wordlists", help="Caminho do arquivo .txt ou pasta de wordlists (padrão: 'wordlists/').")
    parser.add_argument("-t", "--threads", type=int, default=None, help="Número de threads/workers paralelos.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostra visualmente todas as senhas testadas linha a linha em velocidade desacelerada.")
    parser.add_argument("-d", "--delay", type=float, default=None, help="Ajusta o delay manual (em segundos) entre cada teste.")
    parser.add_argument("--gui", action="store_true", help="Inicia a interface Web GUI.")

    args, unknown = parser.parse_known_args()

    if args.gui or (not args.zip_file and len(sys.argv) == 1):
        try:
            import webbrowser
            from unloque.web.app import create_app
            print("[*] Iniciando interface Web em http://127.0.0.1:5000 ...")
            app = create_app()
            webbrowser.open("http://127.0.0.1:5000")
            app.run(host="127.0.0.1", port=5000)
            return 0
        except Exception as e:
            print(f"[-] Erro ao iniciar interface web: {e}")
            print("[*] Use 'python unloque/main.py <arquivo.zip>' para modo terminal.")
            return 1

    if not args.zip_file:
        parser.print_help()
        return 1

    if args.zip_file == "crack":
        if args.wordlist and args.wordlist != "wordlists":
            zip_target = args.wordlist
            wl_target = unknown[0] if unknown else "wordlists"
            return run_crack(zip_target, wl_target, workers=args.threads, verbose=args.verbose, delay=args.delay)
        else:
            print("[-] Informe o arquivo ZIP: python unloque/main.py crack <arquivo.zip>")
            return 1

    return run_crack(args.zip_file, args.wordlist, workers=args.threads, verbose=args.verbose, delay=args.delay)
