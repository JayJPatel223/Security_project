# Encryption security and performance project

Working educational prototype for Jay Patel and Sami Darouiche's proposal.

## Start here

Use Python 3.10 or newer. Open a terminal inside this folder:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux instead:
# source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python crypto_model.py
```

Quick run: `python crypto_model.py --sizes 1024 10240 --repetitions 5 --output quick_results`

The default run uses 1 KiB, 10 KiB, 100 KiB, and 1 MiB, five warm-ups per configuration and 30 measured repetitions. All data is synthetic. Results from the development environment are included in `sample_results/`; rerun on your own computer for your final report. These are measured samples, not predicted results.

## Model and modules

Synthetic data -> four cipher implementations -> performance/security experiments -> CSV/JSON/graphs.

`make_cipher`: AES-128-GCM, AES-256-GCM, ChaCha20-Poly1305, and Toy-XOR-16.
`benchmark`: encryption/decryption timings and correctness checks.
`memory_measurements`: separate Python allocation measurements.
`security_experiments`: tampering, nonce reuse, ECB leakage, exhaustive toy-key search.
`diffusion_experiments`: plaintext-bit sensitivity, separating ciphertext body and tag.
`main`: CLI, environment capture, tables, and charts.

## Experimental choices

The toy cipher XORs each plaintext byte with one of two repeating key bytes. Its 16-bit keyspace has 65,536 candidates; it has no authentication and ignores nonce/AAD. Exhaustive search uses a complete known plaintext/ciphertext pair and reports every matching key. This design is intentionally weak and has an even easier known-plaintext attack: the first two plaintext and ciphertext bytes reveal its key. Its performance is a Python teaching baseline, not a fair comparison between equally secure implementations.

Standard encryption uses the library AEAD APIs, which return ciphertext with a 16-byte tag appended. A fixed public associated-data label is authenticated but not encrypted. Key creation, data generation, nonce creation, correctness checks, CSV output, and plotting are outside timed operations. Tag creation/verification and library-call overhead are inside timing. Each algorithm uses a fresh key; benchmark nonce counters are unique per key. Decryption timing reuses the corresponding valid ciphertext. Benchmark order is fixed, so system load, CPU frequency changes and ordering can influence results. Repeat whole runs and compare distributions before making speed claims.

Memory uses tracemalloc in separate runs, with inputs and cipher setup allocated beforehand. It measures traced Python allocation peaks, not total process memory or all native cryptographic allocations. Each size has one memory sample per operation; treat it as exploratory.

## Security demonstrations

- Tampering: change ciphertext, change tag, supply wrong AAD or nonce. Standard AEAD decryption must reject each using InvalidTag. Tests also check wrong keys.
- Nonce reuse: deliberately reuse one nonce with a disposable key for two equal-length messages. Excluding tags, C1 XOR C2 equals P1 XOR P2. Knowing P1 then recovers P2. This demonstrates confidentiality loss, not tag forgery or recovery of the encryption key.
- ECB: encrypt four identical 16-byte blocks; show identical ciphertext blocks. ECB is a separate illustration, not one of the four benchmark constructions.
- Brute force: test every 16-bit toy key and verify the recovered candidate against known plaintext.
- Diffusion: run 100 fresh-key trials per algorithm. Flip one bit of a 64-byte plaintext while holding the nonce and key fixed within each isolated pair. GCM and ChaCha20 use stream-like encryption, so one ciphertext-body bit changes. Their tags are measured separately; neither tag bit counts nor ciphertext appearance prove security. Deliberate nonce reuse here is solely for the controlled comparison, using throwaway keys.

## Output files

| File | Contents |
| --- | --- |
| environment.json | OS, CPU, Python, dependencies, backend OpenSSL, run settings |
| timings.csv | Every measured encryption/decryption duration in nanoseconds |
| summary.csv | Median, 95th percentile and throughput derived from median duration |
| memory.csv | Python allocation peaks, measured separately from timing |
| security.json | Actual security demonstration outcomes and toy search duration |
| diffusion.csv | Per-trial ciphertext-body and tag bit changes |
| encrypt_throughput.png | Encryption throughput comparison |
| decrypt_throughput.png | Decryption throughput comparison |

Throughput is plaintext bytes / median time, expressed in MiB/s. The p95 values describe observed timing spread; they are not confidence intervals. Small input measurements include substantial call overhead. The random inputs/keys differ between runs; the procedure and settings are repeatable, not the exact ciphertext bytes. No secret keys from standard algorithms are saved.

## Suggested report structure

1. Research question and AEAD background.
2. Hardware/software environment and experimental methods.
3. Cipher implementations and toy-cipher limitations.
4. Performance tables and graphs, including timing variation.
5. Security experiment evidence and explanation.
6. Limitations, interpretation, and conclusions.

## Plain-language glossary

- Plaintext: original readable data.
- Ciphertext: encrypted data.
- Key: secret value controlling encryption/decryption.
- Nonce: value that must be unique for every encryption under the same AEAD key.
- AEAD: encryption that also authenticates ciphertext and optional public associated data.
- Tag: authentication value checked before accepting decrypted data.
- AAD: public information authenticated alongside the encrypted message.
- Brute force: trying all possible keys.
- Throughput: how much data an operation processes per second.
- Diffusion: how input changes spread through a construction; interpretation depends on the mode.

## Primary references

- Python cryptography AEAD API: https://cryptography.io/en/stable/hazmat/primitives/aead/
- AES standard: https://doi.org/10.6028/NIST.FIPS.197-upd1
- GCM: https://doi.org/10.6028/NIST.SP.800-38D
- ChaCha20-Poly1305: https://www.rfc-editor.org/rfc/rfc8439
- ECB and other modes: https://doi.org/10.6028/NIST.SP.800-38A

These experiments demonstrate specific properties and misuse cases. They do not establish new cryptographic security proofs. The toy cipher is for this classroom exercise only.

## Course project documents

- [Approved proposal (public text copy)](PROPOSAL.txt)
- [Draft report](REPORT.md)
- [Task 1 — Proposal coverage audit](TASK_1_PROPOSAL_AUDIT.txt)
- [Task 2 — Prototype code review](TASK_2_CODE_REVIEW.txt)

This repository contains the supplied prototype and its sample results. The draft report also discusses a separate set of full cloud benchmark runs whose files have yet to be supplied. The planned local benchmark results are pending.
