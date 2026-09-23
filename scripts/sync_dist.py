"""
scripts/sync_dist.py - Automated Synchronization and Verification Tool for QuakeMind Global.
Synchronizes pwa/ assets with docs/ (GitHub Pages) and root / (Hugging Face Space static SDK).
Verifies checksum parity, checks JS syntax with node, and executes unit tests.

Usage:
    python scripts/sync_dist.py          # copy pwa/ -> docs/ and / , then verify and test
    python scripts/sync_dist.py --check  # verify only (CI): fails if any copy drifted from pwa/
"""

import os
import re
import sys
import shutil
import hashlib
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PWA_DIR = os.path.join(REPO_ROOT, "pwa")
DOCS_DIR = os.path.join(REPO_ROOT, "docs")

FILES_TO_SYNC = [
    "index.html",
    "seismic-core.js",
    "sw.js",
    "manifest.json",
    "og-image.png",
    "icon-192.png",
    "icon-512.png",
    "apple-touch-icon.png"
]

JS_TEST_GLOB = "tests/js/*.test.mjs"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def sync_assets(check_only: bool = False):
    print("=" * 65)
    print("🚀 QuakeMind Global — Sincronizador Maestro y Verificador")
    print("=" * 65)

    os.makedirs(DOCS_DIR, exist_ok=True)

    for filename in FILES_TO_SYNC:
        src = os.path.join(PWA_DIR, filename)
        dst_docs = os.path.join(DOCS_DIR, filename)
        dst_root = os.path.join(REPO_ROOT, filename)

        if not os.path.exists(src):
            print(f"❌ Error: Archivo fuente no encontrado: {src}")
            sys.exit(1)

        # Guard: never publish an un-smudged Git LFS pointer instead of the real image
        # (that is what broke the icons and the Open Graph card on GitHub Pages).
        for path in (src,) if not check_only else (src, dst_docs, dst_root):
            if filename.endswith(".png") and os.path.exists(path):
                with open(path, "rb") as f:
                    if f.read(8) != PNG_SIGNATURE:
                        print(f"❌ {os.path.relpath(path, REPO_ROOT)} no es un PNG real (¿puntero Git LFS sin descargar?). "
                              f"Ejecuta 'git lfs pull' antes de sincronizar.")
                        sys.exit(1)

        if not check_only:
            shutil.copy2(src, dst_docs)
            shutil.copy2(src, dst_root)

        src_hash = sha256_file(src)
        docs_hash = sha256_file(dst_docs) if os.path.exists(dst_docs) else "missing"
        root_hash = sha256_file(dst_root) if os.path.exists(dst_root) else "missing"

        if not (src_hash == docs_hash == root_hash):
            print(f"❌ {filename}: docs/ o la raíz difieren de pwa/ — ejecuta 'python scripts/sync_dist.py'")
            sys.exit(1)
        verb = "Verificado" if check_only else "Sincronizado"
        print(f"✅ {verb} {filename:<16} -> docs/ & / (SHA-256: {src_hash[:12]}...)")

    print("\n🔍 Validando sintaxis JavaScript...")
    for js_file in ("sw.js", "seismic-core.js"):
        res = subprocess.run(["node", "--check", os.path.join(PWA_DIR, js_file)],
                             capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            print(f"❌ Error de sintaxis en {js_file}: {res.stderr}")
            sys.exit(1)
        print(f"✅ {js_file} sintaxis válida.")

    # Validate every inline <script> block in index.html
    html_path = os.path.join(PWA_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    inline_scripts = re.findall(r"<script>(.*?)</script>", html_content, re.S)
    for idx, script_code in enumerate(inline_scripts):
        node_check = subprocess.run(
            ["node", "-e", "let code = ''; process.stdin.on('data', c => code += c); process.stdin.on('end', () => { try { new Function(code); } catch(e) { console.error(e); process.exit(1); } });"],
            input=script_code,
            capture_output=True, text=True, encoding="utf-8"
        )
        if node_check.returncode != 0:
            print(f"❌ Error de sintaxis en index.html script #{idx}:\n{node_check.stderr}")
            sys.exit(1)
    print(f"✅ index.html: {len(inline_scripts)} bloque(s) inline con sintaxis válida.")

    print("\n🧪 Ejecutando pruebas del núcleo JavaScript (node --test)...")
    js_res = subprocess.run(["node", "--test", JS_TEST_GLOB], cwd=REPO_ROOT)
    if js_res.returncode != 0:
        print("❌ Pruebas JavaScript fallaron.")
        sys.exit(1)

    print("\n🧪 Ejecutando suite de pruebas automatizadas (pytest)...")
    test_res = subprocess.run([sys.executable, "-m", "pytest", "tests/test_quakemind.py", "-q"], cwd=REPO_ROOT)
    if test_res.returncode != 0:
        print("❌ Pruebas unitarias fallaron.")
        sys.exit(1)

    print("\n🎉 ¡Todo sincronizado, verificado y probado con éxito!")
    print("=" * 65)


if __name__ == "__main__":
    sync_assets(check_only="--check" in sys.argv)
