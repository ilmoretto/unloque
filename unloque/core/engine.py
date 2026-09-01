import os
import time
import zipfile
import shutil
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional, Callable, Iterable, List, Union

try:
    import pyzipper
    HAS_PYZIPPER = True
except ImportError:
    HAS_PYZIPPER = False


@dataclass
class ProgressStats:
    tested: int = 0
    total: int = 0
    rate: float = 0.0
    percent: float = 0.0
    elapsed: float = 0.0
    eta: float = 0.0
    found: bool = False
    password: Optional[str] = None
    status: str = "idle"
    message: str = ""


class ZipEngine:
    """Motor de recuperação e ataque por dicionário para arquivos ZIP."""

    def __init__(self, zip_path: str):
        self.zip_path = os.path.abspath(zip_path)
        if not os.path.exists(self.zip_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.zip_path}")
        
        self.is_aes = False
        self.target_member = None
        self._inspect_zip()

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()

    def _inspect_zip(self) -> None:
        """Inspeciona o arquivo ZIP e localiza a primeira entrada encriptada."""
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            for member in zf.infolist():
                if member.flag_bits & 0x1:
                    self.target_member = member.filename
                    if hasattr(member, "extra") and b"\x01\x99" in member.extra:
                        self.is_aes = True
                    break
        
        if not self.target_member:
            raise ValueError("O arquivo ZIP fornecido não contém entradas protegidas por senha.")

    def test_password(self, password: str) -> bool:
        """Testa uma única senha contra o arquivo ZIP."""
        if not password:
            return False

        if HAS_PYZIPPER:
            try:
                with pyzipper.AESZipFile(self.zip_path, "r") as zf:
                    zf.pwd = password.encode("utf-8")
                    with zf.open(self.target_member, "r") as f:
                        f.read(1)
                    return True
            except Exception:
                return False

        if not self.is_aes:
            try:
                with zipfile.ZipFile(self.zip_path, "r") as zf:
                    with zf.open(self.target_member, "r", pwd=password.encode("utf-8")) as f:
                        f.read(1)
                    return True
            except (RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile):
                return False
            except Exception:
                return False

        if shutil.which("unzip"):
            try:
                cmd = ["unzip", "-P", password, "-t", self.zip_path]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return res.returncode == 0
            except Exception:
                return False

        return False

    def _test_batch(self, passwords: List[str]) -> Optional[str]:
        """Testa um lote de senhas sequencialmente."""
        for pwd in passwords:
            if self._stop_event.is_set():
                return None
            self._pause_event.wait()
            if self.test_password(pwd):
                return pwd
        return None

    def pause(self) -> None:
        """Pausa a recuperação."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Retoma a recuperação pausada."""
        self._pause_event.set()

    def stop(self) -> None:
        """Interrompe a recuperação."""
        self._stop_event.set()
        self._pause_event.set()

    def _load_wordlist(self, wordlist: Union[str, Iterable[str]]) -> List[str]:
        """Carrega e consolida senhas de arquivos, diretórios inteiros ou iteráveis."""
        words = []
        seen = set()

        if isinstance(wordlist, str):
            if os.path.isdir(wordlist):
                for root, _, files in os.walk(wordlist):
                    for file in sorted(files):
                        if file.endswith(".txt"):
                            file_path = os.path.join(root, file)
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                for line in f:
                                    w = line.strip()
                                    if w and w not in seen:
                                        seen.add(w)
                                        words.append(w)
                if not words:
                    raise ValueError(f"Nenhum arquivo .txt válido encontrado no diretório: {wordlist}")
                return words

            if not os.path.exists(wordlist):
                raise FileNotFoundError(f"Wordlist não encontrada: {wordlist}")
            with open(wordlist, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    w = line.strip()
                    if w and w not in seen:
                        seen.add(w)
                        words.append(w)
            return words

        for item in wordlist:
            item_str = str(item).strip()
            if not item_str:
                continue
            if os.path.isfile(item_str):
                with open(item_str, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        w = line.strip()
                        if w and w not in seen:
                            seen.add(w)
                            words.append(w)
            elif item_str not in seen:
                seen.add(item_str)
                words.append(item_str)
        return words

    def crack(
        self,
        wordlist: Union[str, Iterable[str]],
        workers: Optional[int] = None,
        callback: Optional[Callable[[ProgressStats], None]] = None,
        chunk_size: int = 100
    ) -> ProgressStats:
        """Executa a recuperação completa sobre a wordlist ou diretório."""
        for stats in self.crack_generator(wordlist, workers=workers, chunk_size=chunk_size):
            if callback:
                callback(stats)
            if stats.status in ("found", "exhausted", "stopped", "error"):
                return stats
        return ProgressStats(status="exhausted")

    def crack_generator(
        self,
        wordlist: Union[str, Iterable[str]],
        workers: Optional[int] = None,
        chunk_size: int = 100
    ):
        """Gerador que executa a recuperação e emite eventos de progresso."""
        self._stop_event.clear()
        self._pause_event.set()

        try:
            passwords = self._load_wordlist(wordlist)
        except Exception as e:
            yield ProgressStats(status="error", message=str(e))
            return

        total = len(passwords)
        if total == 0:
            yield ProgressStats(status="exhausted", message="Wordlist vazia.")
            return

        workers = workers or min(32, (os.cpu_count() or 1) * 4)
        chunks = [passwords[i:i + chunk_size] for i in range(0, total, chunk_size)]

        tested = 0
        start_time = time.time()
        found_password = None

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_chunk = {executor.submit(self._test_batch, chunk): chunk for chunk in chunks}

            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                tested += len(chunk)
                elapsed = max(0.001, time.time() - start_time)
                rate = tested / elapsed
                percent = min(100.0, (tested / total) * 100.0)
                eta = (total - tested) / rate if rate > 0 else 0.0

                result = future.result()
                if result:
                    found_password = result
                    self._stop_event.set()
                    yield ProgressStats(
                        tested=tested,
                        total=total,
                        rate=rate,
                        percent=percent,
                        elapsed=elapsed,
                        eta=0.0,
                        found=True,
                        password=found_password,
                        status="found",
                        message=f"Senha encontrada: {found_password}"
                    )
                    return

                if self._stop_event.is_set():
                    yield ProgressStats(
                        tested=tested,
                        total=total,
                        rate=rate,
                        percent=percent,
                        elapsed=elapsed,
                        eta=eta,
                        status="stopped",
                        message="Processo interrompido pelo usuário."
                    )
                    return

                yield ProgressStats(
                    tested=tested,
                    total=total,
                    rate=rate,
                    percent=percent,
                    elapsed=elapsed,
                    eta=eta,
                    status="running" if self._pause_event.is_set() else "paused"
                )

        elapsed = max(0.001, time.time() - start_time)
        rate = tested / elapsed
        yield ProgressStats(
            tested=tested,
            total=total,
            rate=rate,
            percent=100.0,
            elapsed=elapsed,
            eta=0.0,
            found=False,
            status="exhausted",
            message="Wordlist esgotada. Senha não encontrada."
        )
