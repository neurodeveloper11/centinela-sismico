"""
scripts/verify_all.py - Success-criteria gate for Centinela Sísmico.

Runs every automated check and maps it to the project's success criteria.
Prints one line per criterion and a final signal:  🟢 ÉXITO  or  🔴 FALLO.

    python scripts/verify_all.py            # full gate (needs Node + Chrome for E2E)
    python scripts/verify_all.py --no-e2e   # unit/integration criteria only
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NPM = "npm.cmd" if os.name == "nt" else "npm"


def run(cmd, env=None):
    t0 = time.perf_counter()
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", env=env)
    return res.returncode == 0, time.perf_counter() - t0, (res.stdout or "") + (res.stderr or "")


def pytest_k(expr):
    ok, _, out = run([sys.executable, "-m", "pytest", "tests/test_quakemind.py", "-q", "-p", "no:cacheprovider", "-k", expr])
    passed = re.search(r"(\d+) passed", out)
    return ok and bool(passed), f"pytest[{expr}]: {passed.group(0) if passed else 'sin pruebas'}"


def node_pattern(pattern):
    ok, _, out = run(["node", "--test", f"--test-name-pattern={pattern}", "tests/js/*.test.mjs"])
    passed = re.search(r"ℹ pass (\d+)", out)
    n = int(passed.group(1)) if passed else 0
    return ok and n > 0, f"node[{pattern}]: {n} passed"


def e2e_checks(report, *keywords):
    matched = [r for r in report if any(k in r["name"] for k in keywords)]
    ok = bool(matched) and all(r["ok"] for r in matched)
    detail = "; ".join(f"{'✓' if r['ok'] else '✗'} {r['name']}" + (f" ({r['detail']})" if r["detail"] and len(r["detail"]) < 60 else "")
                       for r in matched) or "sin verificaciones E2E"
    return ok, detail


def static_security():
    problems = []
    html = open(os.path.join(REPO_ROOT, "pwa", "index.html"), encoding="utf-8").read()
    if 'http-equiv="Content-Security-Policy"' not in html:
        problems.append("falta CSP")
    if "}, 130);" in html:
        problems.append("baliza > 3 Hz")
    if re.search(r"title=\"\$\{ev\.place\}\"|>\$\{ev\.place\}<", html):
        problems.append("ev.place sin escapar")
    ok, _, out = run(["git", "grep", "-nE", r"ghp_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}", "--", "."])
    if ok and out.strip():
        problems.append("posibles tokens en archivos versionados")
    return not problems, "CSP ✓, baliza ≤3 Hz ✓, escape HTML ✓, sin tokens versionados ✓" if not problems else ", ".join(problems)


def main():
    use_e2e = "--no-e2e" not in sys.argv
    print("=" * 72)
    print("🛡️  Centinela Sísmico — Verificación de criterios de éxito")
    print("=" * 72)

    ok_sync, t_sync, out_sync = run([sys.executable, "scripts/sync_dist.py", "--check"])
    report = []
    t_e2e = 0.0
    if use_e2e:
        report_path = os.path.join(tempfile.gettempdir(), "centinela_e2e_report.json")
        env = dict(os.environ, E2E_REPORT=report_path)
        if os.path.exists(report_path):
            os.remove(report_path)
        _, t_e2e, out_e2e = run([NPM, "run", "test:e2e"], env=env)
        if os.path.exists(report_path):
            report = json.load(open(report_path, encoding="utf-8"))
        else:
            report = [{"name": "E2E ejecutado", "ok": False, "detail": out_e2e[-300:]}]

    criteria = []

    def criterion(code, title, parts):
        ok = all(p[0] for p in parts)
        criteria.append((code, title, ok, [p[1] for p in parts]))

    criterion("C1", "Precisión científica (IPE Allen 2012 = OpenQuake; Python ≡ JavaScript)", [
        pytest_k("IntensityPredictionEquation or PythonJavaScriptParity"),
        node_pattern("IPE|MMI recortada|profundidad importa"),
    ])
    criterion("C2", "Datos correctos de las agencias (profundidad EMSC, fusión USGS+EMSC)", [
        pytest_k("emsc_depth or websocket_payload or merges_same_quake or cache_used or offline_sample"),
        node_pattern("EMSC|USGS: normalización"),
        *([e2e_checks(report, "sismo profundo")] if use_e2e else []),
    ])
    criterion("C3", "Señal correcta (en camino / ya sentido / calma; una sola alerta; cero fatiga)", [
        pytest_k("AlertDecision"),
        node_pattern("decisión|una sola alerta|cero fatiga"),
        *([e2e_checks(report, "Señal", "Sin duplicados", "Cero fatiga", "Cuenta regresiva")] if use_e2e else []),
    ])
    criterion("C4", "Velocidad (decisión < 1 ms/evento; alerta visible < 500 ms; carga < 1.5 s)", [
        node_pattern("velocidad"),
        *([e2e_checks(report, "Velocidad", "Carga rápida", "WebSocket")] if use_e2e else []),
    ])
    criterion("C5", "Seguridad (XSS, CSP, baliza fotosegura, sin secretos versionados)", [
        static_security(),
        *([e2e_checks(report, "Seguridad")] if use_e2e else []),
    ])
    criterion("C6", "Integridad (3 distribuciones idénticas, PNG reales, sintaxis, todas las pruebas)", [
        (ok_sync, f"sync_dist --check en {t_sync:.1f}s" + ("" if ok_sync else f": {out_sync[-400:]}")),
    ])
    if use_e2e:
        criterion("C7", "Experiencia real en Chrome (sin errores, offline, idioma, SW sin recargas)", [
            e2e_checks(report, "Sin errores", "Offline", "Idioma", "Primera instalación"),
        ])

    for code, title, ok, details in criteria:
        print(f"\n{'✅' if ok else '❌'} {code} — {title}")
        for d in details:
            print(f"     · {d}")

    all_ok = all(c[2] for c in criteria)
    print("\n" + "=" * 72)
    passed = sum(1 for c in criteria if c[2])
    extra = f" • E2E {t_e2e:.1f}s" if use_e2e else " • E2E omitido"
    if all_ok:
        print(f"🟢 ÉXITO — {passed}/{len(criteria)} criterios cumplidos{extra}")
    else:
        print(f"🔴 FALLO — {passed}/{len(criteria)} criterios cumplidos{extra}")
    print("=" * 72)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
