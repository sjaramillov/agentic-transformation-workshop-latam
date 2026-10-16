#!/usr/bin/env python3
"""Local workshop helpers. Python 3.11+, standard library, no AWS calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile

SNAPSHOT_SHA256 = "adb4440ce3a709a2b4f6718beb1115bf56f443c82b4cce8200b7d867b47271ce"
SERVICES = ("booking-service", "notification-service", "payment-gateway")
MAX_BYTES = 512 * 1024 * 1024


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fresh_destination(path):
    path = Path(path).expanduser().absolute()
    if path.exists() or path.is_symlink():
        raise ValueError(f"El destino ya existe; elige uno nuevo: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def restore(archive, destination, expected=SNAPSHOT_SHA256):
    archive = Path(archive).expanduser()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("SHA-256 esperado inválido")
    if digest(archive) != expected:
        raise ValueError("SHA-256 no coincide: archivo diferente o incompleto")
    destination = fresh_destination(destination)
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        seen, total = set(), 0
        for member in members:
            name = PurePosixPath(member.name)
            allowed = (name == PurePosixPath("apps") or
                       name.parts[:2] == ("apps", "travelcorp-portfolio") or
                       name.parts[:1] in (("orchestrator",), ("reports",)))
            if (name.is_absolute() or ".." in name.parts or "\\" in member.name or
                    not allowed or not (member.isfile() or member.isdir()) or
                    str(name) in seen):
                raise ValueError(f"Entrada insegura o duplicada en el archivo: {member.name}")
            seen.add(str(name))
            total += member.size
            if total > MAX_BYTES or len(members) > 20000:
                raise ValueError("El archivo supera el límite de extracción")
        required = "apps/travelcorp-portfolio/exercises/agentstorming/facilitate.py"
        if required not in seen:
            raise ValueError("Falta el facilitador de TravelCorp en el archivo")
        # Extract only plain files/directories into our own staging directory.
        staging = Path(tempfile.mkdtemp(prefix=".lab-restore-", dir=destination.parent))
        try:
            for member in members:
                target = staging / member.name
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.extractfile(member) as source, target.open("xb") as output:
                        shutil.copyfileobj(source, output)
                    target.chmod(0o700 if member.mode & 0o111 else 0o600)
                    os.utime(target, (member.mtime, member.mtime))
            if destination.exists():
                raise ValueError("El destino apareció durante la extracción; no se reemplaza")
            staging.rename(destination)
        except BaseException:
            shutil.rmtree(staging)
            raise
    return {"destination": str(destination), "sha256": expected, "entries": len(members)}


def portfolio(environment):
    root = Path(environment).expanduser().resolve() / "apps/travelcorp-portfolio"
    if not (root / "exercises/agentstorming/facilitate.py").is_file():
        raise ValueError(f"No se encontró TravelCorp en {root}")
    return root


def run(command, **kwargs):
    return subprocess.run(command, text=True, capture_output=True,
                          stdin=subprocess.DEVNULL, timeout=90, **kwargs)


def rehearse(environment, output):
    source = portfolio(environment)
    output = fresh_destination(output)
    output.mkdir(mode=0o700)
    exercises = output / "exercises"
    exercises.mkdir()
    # Copy code only; captured boards/manifest must not satisfy this rehearsal.
    shutil.copytree(source / "exercises/agentstorming", exercises / "agentstorming",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(source / "exercises/build-atx-context.sh", exercises)
    for phase in (1, 2, 3):
        result = run([sys.executable, "-S", "-m", "agentstorming.facilitate",
                      "--phase", str(phase), "--offline", "--choices",
                      ",".join(["1"] * 30)], cwd=exercises)
        (output / f"phase-{phase}.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise ValueError(f"Falló la fase {phase}; consulta {output}/phase-{phase}.log")
    generated = ["exercises/eventstorm-output.md", "exercises/eventstorm-board.json",
                 "exercises/quadrant-output.md", "exercises/quadrant-board.json",
                 "exercises/workflow-design-output.md", "atx-config-ara.yaml",
                 "atx-config-mod.yaml", "run-manifest.json"]
    for relative in generated:
        path = output / relative
        if not path.is_file() or not path.stat().st_size:
            raise ValueError(f"Falta una salida: {relative}")
        if path.suffix == ".json":
            json.loads(path.read_text())
    manifest = json.loads((output / "run-manifest.json").read_text())
    if manifest.get("candidate") != "rebooking" or manifest.get("autonomy") != "P":
        raise ValueError("El manifiesto no coincide con el escenario capturado rebooking/P")
    for kind in ("ara", "mod"):
        result = run(["bash", str(exercises / "build-atx-context.sh"), kind])
        if result.returncode or "Rebooking" not in result.stdout or "autonomy level P" not in result.stdout:
            raise ValueError(f"Contexto {kind} ausente o sin el agente/autonomía esperados")
        (output / f"context-{kind}.txt").write_text(result.stdout + "\n")
    evidence = {"mode": "offline", "python": sys.version.split()[0],
                "candidate": manifest["candidate"], "autonomy": manifest["autonomy"],
                "cloud_analysis_executed": False,
                "generated": {name: digest(output / name) for name in generated}}
    (output / "rehearsal.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return {"output": str(output), **evidence}


def collect(environment, output, origin):
    base = portfolio(environment)
    environment = base.parent.parent
    roots = ([base / "precomputed-reports"] if origin == "precomputed" else
             [environment / "reports"] + [base / "src" / s / "services" for s in SERVICES])
    files = sorted({p for root in roots if root.exists() for p in root.rglob("*")
                    if p.is_file() and "-report" in p.name and
                    p.suffix in (".json", ".md", ".html")})
    if not files:
        raise ValueError("No hay informes de ese origen; no se sustituirán por un baseline")
    # Validate before copying; keep each source path, never merge by basename/mtime.
    records = []
    for path in files:
        if path.is_symlink() or environment not in path.resolve().parents:
            raise ValueError("Informe fuera del entorno restaurado")
        record = {"path": str(path.relative_to(environment)), "sha256": digest(path)}
        if path.suffix == ".json":
            data = json.loads(path.read_text())
            if not isinstance(data, dict):
                raise ValueError(f"El informe JSON no es un objeto: {path.name}")
            record["classification"] = data.get("classification")
        records.append(record)
    output = fresh_destination(output)
    output.mkdir(mode=0o700)
    for path, record in zip(files, records):
        target = output / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    (output / "inventory.json").write_text(json.dumps({"origin": origin,
         "fresh_analysis": False, "reports": records}, indent=2) + "\n")
    return {"output": str(output), "origin": origin, "files": len(files),
            "fresh_analysis": False}


def doctor(environment, live=False):
    base = portfolio(environment)
    checks = []
    def check(label, ok, detail=""):
        checks.append({"check": label, "ok": bool(ok), "detail": detail})
    check("Python >= 3.11", sys.version_info >= (3, 11), sys.version.split()[0])
    for command in (["bash", "git", "node", "atx", "kiro-cli", "aws", "jq"] if live else ["bash"]):
        check(command, shutil.which(command), "disponible" if shutil.which(command) else "no instalado")
    for relative in ["exercises/build-atx-context.sh", "custom-td/SKILL.md",
                     "custom-td-containerize/SKILL.md", "platform-team/deploy-pipeline.yaml",
                     "platform-team/booking-service-eks.yaml"]:
        check(relative, (base / relative).is_file())
    if live and shutil.which("node"):
        version = run(["node", "--version"])
        check("Node >= 22", version.returncode == 0 and int(version.stdout.strip().lstrip("v").split('.')[0]) >= 22)
    if live and shutil.which("git"):
        for service in SERVICES:
            repo = base / "src" / service
            branch = run(["git", "-C", str(repo), "branch", "--show-current"])
            status = run(["git", "-C", str(repo), "status", "--porcelain"])
            check(f"{service}: main limpia", branch.returncode == status.returncode == 0 and
                  branch.stdout.strip() == "main" and not status.stdout.strip(),
                  f"rama: {branch.stdout.strip() or 'desconocida'}")
    return {"mode": "live-prerequisites" if live else "offline",
            "ok": all(c["ok"] for c in checks), "checks": checks,
            "aws_identity_permissions_models_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("restore", help="Verificar y extraer una captura en un destino nuevo")
    p.add_argument("--archive", required=True)
    p.add_argument("--destination", required=True)
    p.add_argument("--sha256", default=SNAPSHOT_SHA256,
                   help="Hash de una captura autorizada diferente (predeterminado: 2026-10-15)")
    for name in ("doctor", "rehearse", "collect"):
        p = sub.add_parser(name)
        p.add_argument("--environment", required=True, help="Directorio que contiene apps/, reports/, orchestrator/")
        if name == "doctor":
            p.add_argument("--live", action="store_true", help="Revisar prerequisitos locales de AWS, sin llamar AWS")
        else:
            p.add_argument("--output", required=True, help="Directorio nuevo; nunca sobrescribe")
        if name == "collect":
            p.add_argument("--origin", required=True, choices=("captured", "precomputed"))
    args = vars(parser.parse_args())
    command = args.pop("command")
    if command == "restore":
        args["expected"] = args.pop("sha256")
    try:
        result = globals()[command](**args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok", True) else 1
    except (OSError, ValueError, tarfile.TarError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
