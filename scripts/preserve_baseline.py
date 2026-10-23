"""One-time source preservation. Never reads runtime credentials or touches devices."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = Path.home() / "Documents"
OLD = DOCS / "Lone_Smart_Room_v1.4"
ANDROID = DOCS / "Android-LoneSmartRoom"
AGENT = DOCS / "Windows-Agent"
RECORDS = []


def preserve(source, destination):
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    shutil.copy2(source, destination)
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == before
    RECORDS.append({"source": str(source), "copy": str(destination.relative_to(ROOT)),
                    "sha256": before, "bytes": source.stat().st_size})


def android_sources(base):
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if any(part in {".idea", ".gradle", ".git", "build"} for part in rel.parts):
            continue
        if path.name == "local.properties":
            continue
        if path.suffix in {".kt", ".kts", ".properties", ".xml", ".js", ".html", ".css", ".md"}:
            yield path, rel


for name in ("app.js", "index.html", "styles.css", "main.cjs", "preload.cjs",
             "package.json", "start-windows.bat", "build-windows.bat", "LEIA-ME.md",
             "assets/icon.ico", "assets/icon.png", "assets/icon.svg"):
    preserve(OLD / name, ROOT / "apps/windows-ui" / name)
    preserve(OLD / name, ROOT / "recovery/sources/electron-v1.4" / name)

for source, rel in android_sources(ANDROID):
    preserve(source, ROOT / "apps/android" / rel)
    preserve(source, ROOT / "recovery/sources/android-working" / rel)
for source, rel in android_sources(OLD / "Android-LoneSmartRoom"):
    preserve(source, ROOT / "recovery/sources/android-v1.4" / rel)

for name in ("agent.py", "test_agent.py", "CONFIGURAR_FIREWALL.ps1", "INICIAR_AGENTE.bat",
             "INSTALAR_INICIO_AUTOMATICO.bat", "REMOVER_INICIO_AUTOMATICO.bat", "MOSTRAR_CHAVE.bat"):
    preserve(AGENT / name, ROOT / "agent/windows" / name)
    preserve(AGENT / name, ROOT / "recovery/sources/windows-agent-v1.5" / name)

for source in (Path.home() / "Downloads").glob("Lone_Smart_Room*.zip"):
    preserve(source, ROOT / "recovery/archives" / source.name)
for source in (ANDROID / "app/build").rglob("*.apk"):
    preserve(source, ROOT / "recovery/artifacts/android" / source.relative_to(ANDROID / "app/build"))

(ROOT / "recovery/manifest.json").write_text(json.dumps(RECORDS, indent=2), encoding="utf-8")
summary = [{"copy": r["copy"], "sha256": r["sha256"], "bytes": r["bytes"]} for r in RECORDS]
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs/baseline-inventory.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(f"Preserved and hash-verified {len(RECORDS)} copies; runtime configuration excluded.")
