"""Auditor criptográfico e inspecionador de cabeçalhos PKZIP."""
import os
import zipfile
from typing import Dict, Any, List

def analyze_zip(zip_path: str) -> Dict[str, Any]:
    """
    Inspeciona os cabeçalhos de um arquivo ZIP e retorna detalhes sobre cifra,
    arquivos internos, vulnerabilidades e recomendações.
    """
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {zip_path}")

    if not zipfile.is_zipfile(zip_path):
        raise ValueError("O arquivo especificado não é um arquivo ZIP válido.")

    files_info: List[Dict[str, Any]] = []
    is_encrypted = False
    encryption_type = "Nenhuma"
    has_aes = False
    has_zipcrypto = False
    aes_strength = "AES-256"

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            member_encrypted = bool(member.flag_bits & 0x1)
            member_aes = False
            member_enc_type = "Nenhuma"

            if member_encrypted:
                is_encrypted = True
                # Verifica campo extra WinZip AES (ID 0x9901 -> b"\x01\x99")
                if hasattr(member, "extra") and member.extra:
                    extra = member.extra
                    idx = 0
                    while idx + 4 <= len(extra):
                        header_id = extra[idx:idx+2]
                        data_size = int.from_bytes(extra[idx+2:idx+4], "little")
                        if header_id == b"\x01\x99" and data_size >= 7:
                            member_aes = True
                            has_aes = True
                            mode = extra[idx+8] if (idx+8) < len(extra) else 3
                            if mode == 1:
                                aes_strength = "AES-128"
                            elif mode == 2:
                                aes_strength = "AES-192"
                            else:
                                aes_strength = "AES-256"
                            member_enc_type = f"WinZip {aes_strength}"
                            break
                        idx += 4 + data_size

                if not member_aes:
                    has_zipcrypto = True
                    member_enc_type = "ZipCrypto (PKZIP Stream Cipher)"

            files_info.append({
                "filename": member.filename,
                "compressed_size": member.compress_size,
                "uncompressed_size": member.file_size,
                "is_encrypted": member_encrypted,
                "encryption_type": member_enc_type,
                "crc": f"0x{member.CRC:08X}" if member.CRC else "N/A",
                "is_dir": member.is_dir()
            })

    if has_aes:
        encryption_type = f"WinZip {aes_strength}"
        vulnerability_level = "LOW" if aes_strength == "AES-256" else "MEDIUM"
        recommendation = (
            f"Cifra {encryption_type} com derivação de chave PBKDF2-HMAC-SHA1 detectada. "
            "Resistente a ataques de texto claro conhecido. Recomenda-se ataque por dicionário "
            "com mutações heurísticas e palavras-chave contextuais."
        )
    elif has_zipcrypto:
        encryption_type = "ZipCrypto (PKZIP Stream Cipher)"
        vulnerability_level = "HIGH"
        recommendation = (
            "Cifra clássica ZipCrypto detectada! Apresenta vulnerabilidade estrutural conhecida "
            "(Known-Plaintext Attack de Biham-Kocher). Ataques por dicionário e força bruta direta "
            "são executados em altíssima velocidade computacional."
        )
    else:
        encryption_type = "Nenhuma (Sem Criptografia)"
        vulnerability_level = "NONE"
        recommendation = "O arquivo não está protegido por senha. O conteúdo pode ser extraído diretamente."

    return {
        "status": "success",
        "filepath": zip_path,
        "filename": os.path.basename(zip_path),
        "is_encrypted": is_encrypted,
        "encryption_type": encryption_type,
        "vulnerability_level": vulnerability_level,
        "entries_count": len(files_info),
        "files": files_info,
        "recommendation": recommendation
    }
