"""Summarize the matched-run frontend benchmark."""
import json
import os
import sys
from pathlib import Path

results = [json.loads(Path(path).read_text()) for path in sys.argv[1:]]
lines = [
    "# Frontend migration benchmark",
    "",
    "Same Ubuntu runner, fresh browser contexts, all optional features disabled.",
    "Nine navigation samples per build; medians shown. Builds exclude dependency installation.",
    "",
    "| Variant | Build (s) | JS raw (KiB) | JS gzip (KiB) | JS Brotli (KiB) | CSS gzip (KiB) | Initial JS (KiB) | FCP (ms) | Note visible (ms) |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for result in results:
    js, css, med = result["assets"]["js"], result["assets"]["css"], result["median"]
    lines.append(
        f'| {result["label"]} | {result["buildMs"] / 1000:.2f} | '
        f'{js["raw"] / 1024:.1f} | {js["gzip"] / 1024:.1f} | {js["brotli"] / 1024:.1f} | '
        f'{css["gzip"] / 1024:.1f} | {med["initialJsBytes"] / 1024:.1f} | '
        f'{med["fcpMs"]:.1f} | {med["readyMs"]:.1f} |'
    )
lines += [
    "",
    "Raw per-navigation samples, revision SHAs and tool versions are in the JSON artifacts.",
    "Compressed sizes are offline per-file estimates, not network transfer measurements.",
    "Historical dependency ranges resolve at run time; this compares template revisions under today's resolution, not exact historical lockfiles.",
    "The standalone migration also changed forms and settings UI, so its delta is not exclusively attributable to SvelteKit removal.",
]
report = "\n".join(lines) + "\n"
print(report)
Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a").write(report)
Path("benchmark-results/report.md").write_text(report)
