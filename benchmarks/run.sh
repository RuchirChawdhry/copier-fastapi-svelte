#!/usr/bin/env bash
set -euo pipefail
task tools:setup
mkdir -p benchmark-results
export GITHUB_WORKSPACE="${GITHUB_WORKSPACE:-$PWD}"
export RUNNER_TEMP="${RUNNER_TEMP:-$(mktemp -d)}"
export GITHUB_SHA="${GITHUB_SHA:-$(git rev-parse HEAD)}"
for entry in 'SvelteKit + Superforms|366e3a8b6107c7338207ec1209c2e9618c39dcbd|before' 'Standalone + TanStack Form|829e4345d9623c9bf7e77adfa4d48e7e28702395|migration' "Standalone + Form + Query|${GITHUB_SHA}|current"; do
  IFS='|' read -r label revision name <<< "$entry"
  dest="$RUNNER_TEMP/benchmark-$name"
  uvx --from copier==9.14.1 copier copy --defaults --vcs-ref="$revision" . "$dest"
  (
    cd "$dest"
    CI=false task install
    cd frontend
    pnpm exec playwright install chromium
    cp "$GITHUB_WORKSPACE/benchmarks/measure.mjs" ./measure.mjs
    node measure.mjs "$label" "$revision" "$GITHUB_WORKSPACE/benchmark-results/$name.json"
    cp pnpm-lock.yaml "$GITHUB_WORKSPACE/benchmark-results/$name-pnpm-lock.yaml"
    cp ../uv.lock "$GITHUB_WORKSPACE/benchmark-results/$name-uv.lock"
  )
done
