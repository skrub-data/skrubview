#! /usr/bin/env python3

import shutil
from pathlib import Path

from skrub import datasets
from skrubview import Report


doc_dir = Path(__file__).resolve().parent
build_dir = doc_dir / "_build"
if build_dir.is_dir():
    shutil.rmtree(build_dir)
build_dir.mkdir()
reports_dir = build_dir / "reports"
reports_dir.mkdir()

dataset_names = [
    "employee_salaries",
    "medical_charge",
]
datasets = [(getattr(datasets, f"fetch_{name}")().X, name) for name in dataset_names]


def add_report(df, name):
    pretty_name = name.replace("_", " ").capitalize()
    report = Report(df, title=pretty_name)
    (reports_dir / f"{name}.html").write_text(report.html, "utf-8")
    return f"<li><a href='reports/{name}.html'>{pretty_name}</a></li>"


links = [add_report(df, name) for df, name in datasets]

links_text = "\n".join(links)

index = f"""
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>skrubview</title>
</head>
<h1>Skrubview example reports</h1>
<ul>
{links_text}
</ul>
<body>
</body>
</html>
"""

(build_dir / "index.html").write_text(index, "utf-8")
