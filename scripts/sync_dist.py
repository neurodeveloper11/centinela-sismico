"""
scripts/sync_dist.py - Automated Synchronization and Verification Tool for QuakeMind Global.
Synchronizes pwa/ assets with docs/ (GitHub Pages) and root / (Hugging Face Space static SDK).
Verifies checksum parity, checks JS syntax with node, and executes unit tests.
"""

import os
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
    "sw.js",
    "manifest.json",
    "og-image.png",
    "icon-192.png",
    "icon-512.png",
    "apple-touch-icon.png"
]

def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def sync_assets():
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

        shutil.copy2(src, dst_docs)
        shutil.copy2(src, dst_root)

        src_hash = sha256_file(src)
        docs_hash = sha256_file(dst_docs)
        root_hash = sha256_file(dst_root)

        assert src_hash == docs_hash == root_hash, f"Hash mismatch for {filename}"
        print(f"✅ Sincronizado {filename:<14} -> docs/ & / (SHA-256: {src_hash[:12]}...)")

    print("\n🔍 Validando sintaxis JavaScript...")
    # Validate Service Worker with node -c
    sw_path = os.path.join(PWA_DIR, "sw.js")
    res_sw = subprocess.run(["node", "-c", sw_path], capture_output=True, text=True, encoding="utf-8")
    if res_sw.returncode != 0:
        print(f"❌ Error de sintaxis en sw.js: {res_sw.stderr}")
        sys.exit(1)
    print("✅ sw.js sintaxis válida.")

    # Validate inline script in index.html
    html_path = os.path.join(PWA_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    start_idx = html_content.find("<script>")
    end_idx = html_content.rfind("</script>")
    if start_idx != -1 and end_idx != -1:
        script_code = html_content[start_idx + 8:end_idx]
        node_check = subprocess.run(
            ["node", "-e", "let code = ''; process.stdin.on('data', c => code += c); process.stdin.on('end', () => { try { new Function(code); } catch(e) { console.error(e); process.exit(1); } });"],
            input=script_code,
            capture_output=True, text=True, encoding="utf-8"
        )
        if node_check.returncode != 0:
            print(f"❌ Error de sintaxis en index.html script:\n{node_check.stderr}")
            sys.exit(1)
        print("✅ index.html inline script sintaxis válida.")

    print("\n🧪 Ejecutando suite de pruebas automatizadas...")
    test_res = subprocess.run([sys.executable, "-m", "pytest", "tests/test_quakemind.py", "-v"], cwd=REPO_ROOT)
    if test_res.returncode != 0:
        print("❌ Pruebas unitarias fallaron.")
        sys.exit(1)

    print("\n🎉 ¡Todo sincronizado, verificado y probado con éxito!")
    print("=" * 65)

if __name__ == "__main__":
    sync_assets()
