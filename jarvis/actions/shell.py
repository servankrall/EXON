"""
Terminal komutu çalıştırma — Windows CMD / PowerShell
macOS bash yerine Windows cmd.exe kullanır.
Servan Kanğal tarafından yapılmıştır
Windows portu: bash → cmd.exe / powershell
"""

import subprocess
import sys

# Tehlikeli komutları engelle (Windows eşdeğerleri)
BLOCKED = [
    "format c:",
    "format d:",
    "del /f /s /q c:\\",
    "rd /s /q c:\\",
    "rmdir /s /q c:\\",
    "diskpart",
    "shutdown /r",
    "shutdown /s",
    "reg delete hklm",
    "reg delete hkcu",
    "bcdedit",
    "bootrec",
    "cipher /w:c",
    ":(){:|:&};:",   # fork bomb
    "rm -rf /",      # unix style
    "sudo rm -rf",
]


def shell_run(command: str, timeout: int = 30) -> str:
    if not command:
        return "Komut belirtilmedi."

    cmd_lower = command.lower().strip()
    stripped = command.strip()

    # Tehlikeli prefix kontrolü
    if stripped.lower().startswith(("del ", "rmdir ", "rd ", "reg ", "format ", "net user ", "net localgroup ")):
        return (
            "Güvenlik: Dosya silme, kayıt defteri veya kullanıcı değiştiren komutlar "
            "doğrudan çalıştırılmıyor. Daha dar kapsamlı bir komut dene."
        )

    for blocked in BLOCKED:
        if blocked in cmd_lower:
            return f"Güvenlik: Bu komut engellendi → {blocked}"

    # PowerShell komutu mu?
    use_ps = stripped.lower().startswith(("get-", "set-", "new-", "remove-", "invoke-",
                                           "write-", "read-", "select-", "where-",
                                           "powershell"))
    try:
        if use_ps:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", stripped],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
        else:
            result = subprocess.run(
                stripped,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )

        output = (result.stdout + result.stderr).strip()
        if not output:
            return "Komut başarıyla çalıştı (çıktı yok)."
        if len(output) > 800:
            output = output[:800] + "\n... (çıktı kısaltıldı)"
        return output

    except subprocess.TimeoutExpired:
        return f"Komut zaman aşımına uğradı ({timeout}s)."
    except Exception as e:
        return f"Hata: {e}"
