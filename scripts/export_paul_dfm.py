#!/usr/bin/env python3
"""Export a new manufacturing-only DFM snapshot from a native-clean Paul trial.

This does not establish supplier, assembly or functional acceptance. Never
overwrite an earlier package; the source hash and native reports travel with it.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("trial", type=Path)
parser.add_argument(
    "name", help="New package name under the trial's evidence directory"
)
args = parser.parse_args()
trial = args.trial.resolve()
assert trial.is_relative_to(ROOT / "experiments")
assert re.fullmatch(r"[a-z0-9-]+", args.name)
pcb = trial / "hardware/collar-tracker.kicad_pcb"
sch = pcb.with_suffix(".kicad_sch")
out = trial / "evidence" / args.name
archive = out.with_suffix(".zip")
assert not out.exists() and not archive.exists(), "Preserve prior packages"
out.mkdir()
gerbers = out / "gerbers"
gerbers.mkdir()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


source_hash = sha(pcb)
inputs = {
    path.name: sha(path)
    for path in pcb.parent.iterdir()
    if path.is_file()
    and path.suffix in {".kicad_pcb", ".kicad_sch", ".kicad_pro", ".kicad_dru"}
}
env = dict(os.environ, LC_ALL="C")
with (out / "export.log").open("w") as log:

    def run(*command):
        subprocess.run(
            [str(ROOT / "scripts/kicad-cli"), *map(str, command)],
            cwd=ROOT,
            env=env,
            check=True,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

    run(
        "pcb",
        "drc",
        "--format",
        "json",
        "--severity-all",
        "--schematic-parity",
        "--all-track-errors",
        "-o",
        out / "drc.json",
        pcb,
    )
    drc = json.loads((out / "drc.json").read_text())
    assert not any(
        drc[key] for key in ["violations", "unconnected_items", "schematic_parity"]
    )
    run("sch", "erc", "--format", "json", "--severity-all", "-o", out / "erc.json", sch)
    erc = json.loads((out / "erc.json").read_text())
    assert all(not sheet["violations"] for sheet in erc["sheets"])
    run(
        "pcb",
        "export",
        "gerbers",
        "-l",
        "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts",
        "--use-drill-file-origin",
        "--subtract-soldermask",
        "-o",
        gerbers,
        pcb,
    )
    run(
        "pcb",
        "export",
        "drill",
        "--format",
        "excellon",
        "--drill-origin",
        "plot",
        "--excellon-separate-th",
        "--generate-report",
        "--report-path",
        out / "drill-report.txt",
        "-o",
        gerbers,
        pcb,
    )
assert sha(pcb) == source_hash, "Source changed during export"
assert all(sha(pcb.parent / name) == digest for name, digest in inputs.items()), (
    "Native input changed during export"
)
files = sorted(gerbers.iterdir())
required = {
    ".gtl",
    ".gbl",
    ".g1",
    ".g2",
    ".gts",
    ".gbs",
    ".gto",
    ".gbo",
    ".gtp",
    ".gbp",
    ".gm1",
}
assert required <= {path.suffix for path in files}
assert len(files) == 14 and len(list(gerbers.glob("*.drl"))) == 2
assert all(path.suffix in required | {".drl", ".gbrjob"} for path in files)
edge = (gerbers / "collar-tracker-Edge_Cuts.gm1").read_text()
assert "%MOMM*%" in edge and "%FSLAX46Y46*%" in edge
points = [
    (int(x) / 1e6, int(y) / 1e6)
    for x, y in re.findall(r"X(-?\d+)Y(-?\d+)D0[12]\*", edge)
]
dimensions = [max(p[i] for p in points) - min(p[i] for p in points) for i in (0, 1)]
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
    for path in files:
        package.write(path, path.name)
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None
    assert all(package.read(path.name) == path.read_bytes() for path in files)
report = dict(
    source=str(pcb.relative_to(ROOT)),
    source_sha256=source_hash,
    native_input_sha256=inputs,
    schematic_sha256=sha(sch),
    zip=str(archive.relative_to(ROOT)),
    zip_sha256=sha(archive),
    zip_bytes=archive.stat().st_size,
    dimensions_mm=dimensions,
    native_drc="drc.json",
    native_erc="erc.json",
    files=[
        dict(name=path.name, sha256=sha(path), bytes=path.stat().st_size)
        for path in files
    ],
    scope="Native-clean DFM input snapshot only. Supplier DFM and remaining layout reviews are not accepted by this export.",
)
(out / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
print(
    json.dumps(
        {key: value for key, value in report.items() if key != "files"}, indent=2
    )
)
