"""
EXON Pro — lisans anahtari uretici.
EXON Robotik tarafindan gelistirilmistir.

Kullanim (jarvis klasorunde):
    python make_license.py yearly        # yillik anahtar
    python make_license.py monthly       # aylik anahtar
    python make_license.py lifetime      # omurluk anahtar
    python make_license.py monthly 90    # 90 gunluk ozel sure

Uretilen anahtari satin alan kisiye ver; o, EXON'da '✦ PRO'YA GEC' penceresine
girip Pro'yu acar. Aylik/yillik anahtarlar sureli; bitince yenisini vermen gerekir.
"""

import sys

from actions.license_manager import generate_key


def main() -> None:
    plan = sys.argv[1] if len(sys.argv) > 1 else "yearly"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else None
    key = generate_key(plan, days)
    print("\n  EXON Pro lisans anahtari:")
    print("  " + key + "\n")


if __name__ == "__main__":
    main()
