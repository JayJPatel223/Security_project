# Local benchmark handoff

The current report contains cloud measurements. Use the steps below on the computer you intend to describe in the final report. Keep the original run folders so every reported value can be traced back to its source.

## Run the benchmark on Windows

The commands below match the prototype currently on GitHub. If you have the complete project, use its matching code and README for the benchmark and extra experiments. Record which revision or archive produced the files. The prototype runs the core experiments but lacks the extra output-characteristics script and the combined analysis script referenced in the draft.

Open PowerShell in the project folder. The prototype README calls for Python 3.10 or newer.

```powershell
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }

$projectPython = ".\.venv\Scripts\python.exe"
& $projectPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

& $projectPython -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests did not pass." }

$runRoot = "local_results_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $runRoot -ErrorAction Stop | Out-Null
& $projectPython -m pip freeze | Set-Content (Join-Path $runRoot "dependencies.txt")
git rev-parse HEAD 2>$null | Set-Content (Join-Path $runRoot "revision.txt")

foreach ($run in 1..3) {
    $runPath = Join-Path $runRoot "run_$run"
    & $projectPython crypto_model.py --output $runPath
    if ($LASTEXITCODE -ne 0) { throw "Benchmark run $run failed. Keep the failed folder separate." }
}
```

The prototype defaults to 1 KiB, 10 KiB, 100 KiB, and 1 MiB with 5 warm-ups and 30 timed repetitions per configuration. Use the same settings, software environment, and power mode for all three runs. Run them sequentially and record the CPU model, available cores, OS, and any unusual activity during a run. A fresh output directory keeps a partial rerun from mixing with earlier results. If you ran from an extracted archive, record its filename if Git cannot supply a revision.

## Send back the evidence

Zip the entire local results folder. Each complete prototype run folder should have these files.

- `environment.json`
- `timings.csv` and `summary.csv`
- `memory.csv`
- `security.json` and `diffusion.csv`
- `encrypt_throughput.png` and `decrypt_throughput.png`

Also include the complete project archive if it differs from the GitHub prototype. If you ran the extra experiment, include its raw and summary files. If you generated a combined report or figure, include it with the analysis script. Keep the cloud outputs separate from the local outputs.

## How the report will be refreshed

| Report item | Local evidence |
|---|---|
| Environment and methods | Each run's environment file, dependency snapshot, and code revision |
| Encryption and decryption time, throughput, and run-to-run variation | Raw timings and per-run summaries |
| Combined throughput figure | Local timing data used for the tables, with the aggregation method stated in the caption |
| Traced Python allocation peaks | Each run's memory CSV and the aggregation method used in the report |
| Tampering, nonce reuse, ECB, and toy key search | Each run's security JSON |
| Plaintext bit-flip experiment | Each run's diffusion CSV |
| Entropy, chi-square, and repeated-block statistics | Local output-characteristics experiment files and the script that produced them |

With the local files, compare the reported cloud conclusions against the local results. Check the AES-GCM versus ChaCha20-Poly1305 ranking, the size of the gap relative to run-to-run spread, and whether the narrower differences between AES variants remain consistent. Flag missing evidence and any change in the security experiment outcomes. A local prototype run alone cannot refresh the output-characteristics table.
