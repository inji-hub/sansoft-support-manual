"""Streamlit entrypoint: unpack a verified manual snapshot and render it."""
from pathlib import Path
import hashlib
import runpy
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
PAYLOAD_SHA256 = "460dca57ba57aea0cd717ce5e779d2b11869f8e62bf1b7768dca2f14d11d63f7"


def prepare_runtime():
    archive = ROOT / "manual-content.zip"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != PAYLOAD_SHA256:
        raise RuntimeError("매뉴얼 파일이 일치하지 않습니다. app.py와 manual-content.zip을 함께 업데이트해 주세요.")
    runtime = ROOT / ".manual_runtime" / PAYLOAD_SHA256[:16]
    ready = runtime / ".ready"
    if not ready.exists():
        runtime.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                target = (runtime / item.filename).resolve()
                if not target.is_relative_to(runtime.resolve()):
                    raise RuntimeError("잘못된 매뉴얼 경로입니다.")
            z.extractall(runtime)
        ready.write_text(PAYLOAD_SHA256, encoding="ascii")
    return runtime


def main():
    runtime = prepare_runtime()
    sys.path.insert(0, str(runtime)) if str(runtime) not in sys.path else None
    for name in ("cases", "home", "glossary", "presentation", "update_history", "visuals"):
        module = sys.modules.get(name)
        if module and Path(getattr(module, "__file__", "")).parent != runtime:
            del sys.modules[name]
    runpy.run_path(str(runtime / "app.py"), run_name="__main__")


if __name__ == "__main__":
    main()
