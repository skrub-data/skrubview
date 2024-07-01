#! /usr/bin/env python3

import time
import shutil
from pathlib import Path

import polars as pl
import pandas as pd
from skrub import datasets as skrub_data
from sklearn import datasets as sklearn_data
from skrubview import Report


doc_dir = Path(__file__).resolve().parent
build_dir = doc_dir / "_build"
if build_dir.is_dir():
    shutil.rmtree(build_dir)
build_dir.mkdir()
reports_dir = build_dir / "reports"
reports_dir.mkdir()

AMES_HOUSING_CSV = "https://www.openml.org/data/get_csv/20649135/file2ed11cebe25.arff"
datasets = [(pd.read_csv(AMES_HOUSING_CSV), "AMES Housing")]
skrub_dataset_names = [
    "employee_salaries",
    "medical_charge",
    "traffic_violations",
    "drug_directory",
]
datasets.extend(
    [(getattr(skrub_data, f"fetch_{name}")().X, name) for name in skrub_dataset_names]
)

sklearn_dataset_names = ["titanic"]
datasets.extend(
    [
        (
            sklearn_data.fetch_openml(
                name, as_frame=True, parser="auto", version=1
            ).frame,
            name,
        )
        for name in sklearn_dataset_names
    ]
)


def add_report(df, name):
    print(f"making report for {name}", end="", flush=True)
    # TODO: from_pandas failing due to bug in polars; restore when it is fixed.
    # df = pl.from_pandas(df)
    pretty_name = name.replace("_", " ").capitalize()
    start = time.time()
    html = Report(df, title=pretty_name).html
    stop = time.time()
    print(f": {stop - start:.2f}s")
    addition = f"""
    <div style="padding: 1rem; font-size: 0.9rem;">
    <p>
    Report generated in {stop - start:.2f} seconds by
    <a href="https://github.com/skrub-data/skrubview">skrubview</a>.
    </p>
    <p><a href="..">Back to homepage</a>
    </div>
    """
    html = html.replace("</body>", f"{addition}\n</body>")
    (reports_dir / f"{name}.html").write_text(html, "utf-8")
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
<body>
<h1>Skrubview example reports</h1>
<ul>
{links_text}
</ul>
See also the <a href="https://github.com/skrub-data/skrubview">GitHub repository</a>
</body>
</html>
"""

(build_dir / "index.html").write_text(index, "utf-8")
