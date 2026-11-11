# Security and Performance Evaluation of AES-GCM and ChaCha20-Poly1305 with a Custom Experimental Cipher

Jay Patel and Sami Darouiche

Working draft. The performance values are from the existing cloud benchmark draft. The repository includes prototype sample results, but the full cloud run files and the results from the planned local rerun are pending. Values carried over from the cloud draft are identified below.

## 1. Research question and background

How do AES-128-GCM, AES-256-GCM, and ChaCha20-Poly1305 compare on the same benchmark workload? What do controlled tests of tampering, nonce reuse, and repeated input reveal about these constructions and a deliberately weak toy cipher?

AES is a block cipher. The suffix in AES-128 and AES-256 denotes the key length. Galois/Counter Mode (GCM) combines counter-mode encryption with authentication. ChaCha20-Poly1305 combines the ChaCha20 stream cipher with the Poly1305 authenticator. Both constructions provide authenticated encryption with associated data (AEAD). The associated data is authenticated and can remain public. The library APIs used here append a 16-byte tag and raise `InvalidTag` when authentication fails. Both constructions require a unique nonce for each encryption under a given key. [1–3, 6]

## 2. Environment and methods

The cloud benchmark draft records the following environment. The full-run metadata still needs to be checked against the original `environment.json` files.

- OS — Linux-6.18.44-fc-v378-x86_64-with-glibc2.39
- CPU — Intel(R) Xeon(R) Processor @ 2.10GHz (2 cores available)
- Python — 3.13.18
- Libraries — cryptography 50.0.2, NumPy 2.5.4, pandas 3.1.1, Matplotlib 3.11.2
- Cryptography backend — OpenSSL 4.0.3 29 Sep 2026

The benchmarks used synthetic random bytes. The security experiments also used synthetic inputs, including fixed messages and repeated blocks. The benchmark sizes were 1 KiB, 10 KiB, 100 KiB, and 1 MiB. Each configuration used 5 discarded warm-up operations and 30 timed repetitions. The draft reports 3 separate benchmark runs.

The prototype times each library or toy-cipher call with `time.perf_counter_ns()`. The timed region includes the call and, for AEAD, tag creation or verification. Key creation, input generation, nonce creation, correctness checks, file output, and plotting are outside the timed region. The prototype uses a fresh key for each algorithm, counter-based nonces for benchmark encryption, and a fixed algorithm order. Decryption immediately follows encryption on the resulting ciphertext. This measures a paired, in-process workload. [10]

Throughput expresses plaintext bytes processed per unit of time in MiB/s. The draft describes the cloud summaries as throughput derived from the median of the per-run median times. The exact aggregation should be checked when the analysis script and raw runs are available. Memory was measured separately with `tracemalloc`, with one sample per algorithm, input size, and operation. [9]

## 3. Implementations and toy-cipher limits

The prototype calls the Python `cryptography` library's `AESGCM` and `ChaCha20Poly1305` classes with a fixed public associated-data label. The tag covers the ciphertext and associated data. [2, 3, 6]

The project's Toy-XOR-16 implementation XORs each plaintext byte with one of two alternating key bytes. Its 16-bit keyspace contains 65,536 possible keys. The implementation ignores the nonce and associated data and has no authentication. Identical blocks at the same key alignment produce identical ciphertext blocks. The first two corresponding plaintext and ciphertext bytes determine the two key bytes under this implementation. These properties follow directly from the [ToyCipher source](crypto_model.py).

The toy is an educational baseline. It runs a pure-Python byte loop, while the standard configurations call compiled library code and perform authentication. The timings combine those differences, so they cannot isolate cipher design, implementation language, or authentication overhead.

## 4. Performance results

The tables retain the values from the cloud draft. The checked-in sample plots and CSVs are from the supplied prototype archive and should be cited as sample outputs. The cloud draft's combined figure, `full_results/combined/combined_throughput.png`, is pending verification. The draft describes it as a median across 3 runs with a band showing the minimum and maximum.

### Encryption throughput (MiB/s, median of 3 runs)

| Algorithm | 1 KiB | 10 KiB | 100 KiB | 1 MiB |
|---|---|---|---|---|
| AES-128-GCM | 1,083 | 5,671 | 9,869 | 8,383 |
| AES-256-GCM | 1,048 | 5,228 | 8,942 | 7,740 |
| ChaCha20-Poly1305 | 474 | 1,932 | 2,823 | 2,769 |
| Toy-XOR-16 | 16.7 | 15.3 | 14.4 | 15.0 |

### Decryption throughput (MiB/s, median of 3 runs)

| Algorithm | 1 KiB | 10 KiB | 100 KiB | 1 MiB |
|---|---|---|---|---|
| AES-128-GCM | 1,165 | 5,837 | 10,028 | 8,596 |
| AES-256-GCM | 1,075 | 5,181 | 9,055 | 7,907 |
| ChaCha20-Poly1305 | 491 | 1,976 | 2,930 | 2,843 |
| Toy-XOR-16 | 16.7 | 15.5 | 14.5 | 14.9 |

In the cloud draft, AES-128-GCM encrypted about 3.0 times as fast as ChaCha20-Poly1305 at 1 MiB and about 2.3 times as fast at 1 KiB. AES-256-GCM reached about 92% of AES-128-GCM's encryption throughput at 1 MiB. Throughput increased from 1 KiB to 100 KiB for the standard configurations. The timing includes fixed per-call work, which may contribute to that pattern. Toy-XOR-16 ran at roughly 15 MiB/s and was about 560 times slower than AES-128-GCM at 1 MiB in this implementation.

### Run-to-run variation

For each algorithm and size, the table reports the larger of the encryption and decryption max/min ratios. The largest reported ratio was 1.31x, and the median across configurations was 1.07x. The AES-GCM versus ChaCha20-Poly1305 throughput gap in these cloud results exceeded the reported run-to-run spread. The smaller AES-128-GCM versus AES-256-GCM differences at some sizes deserve a more cautious reading. The draft lists the CPU flags `aes`, `pclmulqdq`, and `vaes`. Backend instruction use and its effect on throughput were unverified.

| Algorithm | 1 KiB | 10 KiB | 100 KiB | 1 MiB |
|---|---|---|---|---|
| AES-128-GCM | 1.08x | 1.06x | 1.03x | 1.07x |
| AES-256-GCM | 1.12x | 1.06x | 1.23x | 1.12x |
| ChaCha20-Poly1305 | 1.18x | 1.31x | 1.09x | 1.04x |
| Toy-XOR-16 | 1.18x | 1.08x | 1.29x | 1.04x |

### Traced Python allocation peaks (bytes)

| Algorithm | Size | Encrypt peak (bytes) | Decrypt peak (bytes) |
|---|---|---|---|
| AES-128-GCM | 1 KiB | 1,073 | 1,057 |
| AES-128-GCM | 1 MiB | 1,048,625 | 1,048,609 |
| AES-256-GCM | 1 KiB | 1,073 | 1,057 |
| AES-256-GCM | 1 MiB | 1,048,625 | 1,048,609 |
| ChaCha20-Poly1305 | 1 KiB | 1,073 | 1,057 |
| ChaCha20-Poly1305 | 1 MiB | 1,048,625 | 1,048,609 |
| Toy-XOR-16 | 1 KiB | 1,896 | 1,896 |
| Toy-XOR-16 | 1 MiB | 1,271,387 | 1,271,387 |

For the standard configurations, the reported encryption peaks were 49 bytes above the input size at both listed sizes. The toy's reported peak at 1 MiB was about 1.2 times its input size. Inputs and cipher setup were allocated before tracing began. These single-sample measurements describe traced Python allocations during the call. Total process memory and native library allocations were outside the measurement scope. [9]

## 5. Security evidence

The observations below come from the cloud draft. The [prototype code](crypto_model.py) contains the tampering, nonce-reuse, ECB, toy key-search, and bit-flip demonstrations. The full-run aggregates and extra output-characteristics experiment still need the matching result files.

**Tampering.** The draft reports that each AEAD configuration raised `InvalidTag` when a ciphertext bit or tag bit changed, or when the supplied associated data or nonce differed. The prototype [unit tests](tests/test_model.py) also cover the wrong-key case. The toy cipher returned altered plaintext after a ciphertext bit flip. The reported AEAD behavior is consistent with the API's authentication checks. [6]

**Nonce reuse.** The draft reports that deliberate reuse of a nonce under a disposable key exposed the XOR of the two plaintexts through the ciphertext bodies in all three AEAD configurations. With one plaintext known, the experiment recovered the other. This is a confidentiality demonstration. Authentication forgery and encryption-key recovery were outside its scope. The same-key, same-nonce confidentiality risk is documented for GCM and ChaCha20-Poly1305. [2, 3]

**ECB leakage.** Encrypting four identical 16-byte plaintext blocks produced one distinct ciphertext block out of four in the reported runs. ECB independently applies the block cipher to each block, so equal plaintext blocks map to equal ciphertext blocks under the same key. The ECB experiment is separate from the performance benchmark. [4]

**Toy key search.** The reported exhaustive search checked 65,536 keys against a known plaintext/ciphertext pair. It found one matching key in all 3 runs and took 265 to 338 ms. The time describes this particular Python loop. Section 3 explains the simpler recovery available from the toy's implementation.

**Plaintext bit flips.** The draft reports 100 trials per algorithm per run, or 300 trials per algorithm across the 3 runs. Each pair used a 64-byte plaintext and held the key and nonce fixed. The prototype changes the lowest bit of the selected byte and rotates the byte position. The ciphertext body changed by exactly one bit in every reported trial. That behavior follows from the way GCM's counter-mode encryption and ChaCha20 XOR a fixed keystream with plaintext in this controlled comparison. The toy also uses XOR. The authentication tags changed by an average of 63.9 bits for AES-128-GCM, 63.7 bits for AES-256-GCM, and 64.0 bits for ChaCha20-Poly1305, out of 128 bits. The reported range was 48 to 82 bits. [2, 3, 6]

Webster and Tavares define the strict avalanche criterion per output bit. For each input-bit position, every output bit should flip with probability one-half over the input pairs. Our tag summary is an average count of changed bits. It does not establish those individual probabilities or assess the AES S-box. [5]

**Ciphertext output characteristics.** The cloud draft describes encrypting a 64 KiB plaintext made from a repeated 16-byte block 30 times per construction. It reports 3.58 bits per byte for the plaintext. The table records the draft's ciphertext summaries.

| Construction | Mean entropy (bits/byte) | Mean chi-square (255 d.f.) | Distinct 16-byte blocks (of 4,096) |
|---|---|---|---|
| AES-128-GCM | 7.997 | 248 | 4096 |
| AES-256-GCM | 7.997 | 259 | 4096 |
| ChaCha20-Poly1305 | 7.997 | 258 | 4096 |
| AES-128-ECB | 3.913 | 1,074,790 | 1 |
| Toy-XOR-16 | 3.857 | 1,135,957 | 1 |

The AEAD samples had byte frequencies closer to uniform than the ECB and toy samples, and the draft reports no repeated blocks in the AEAD samples. The empirical entropy maximum is 8.0 bits per byte when all byte values occur equally often. The reported 7.997 is an observation, not a ceiling. The draft also reports that 97% of ChaCha20-Poly1305 samples were inside an approximate chi-square interval of 197 to 313. The raw values and analysis script are needed to verify that fraction and the interval's calibration. The chi-square values are descriptive here. Byte frequencies and repeated-block counts describe the samples, and a security claim would require other evidence. [7, 8, 11]

## 6. Limitations and conclusions

The 3 cloud runs cover one reported hardware and software environment. The fixed benchmark order, paired encryption and decryption, and single-sample allocation measurements limit the scope of the performance comparison. Independent verification of the combined tables and figure requires the full benchmark runs and analysis script. The planned local rerun will supply the final performance tables and figure, including elapsed encryption and decryption times from the timing files.

The cloud draft reports that AES-GCM had higher throughput than ChaCha20-Poly1305 on that workload. The ranking applies to those measurements. The security experiments illustrate rejection of the tested modifications, confidentiality loss in the tested nonce-reuse cases, and the persistence of repeated structure under ECB and the toy cipher. The toy also accepted a ciphertext change and yielded to the exhaustive search. The experiments do not establish general security or evaluate side channels, key management, or protocol design. [2–4, 6, 11]

## References

[1] NIST. Advanced Encryption Standard (AES), FIPS 197-upd1, 2023. https://doi.org/10.6028/NIST.FIPS.197-upd1

[2] M. Dworkin. Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC, NIST SP 800-38D, 2007, Sections 6.5, 7–8 and Appendix A. https://doi.org/10.6028/NIST.SP.800-38D

[3] Y. Nir and A. Langley. ChaCha20 and Poly1305 for IETF Protocols, RFC 8439, 2018, Sections 2.4, 2.8 and 4. https://www.rfc-editor.org/rfc/rfc8439

[4] M. Dworkin. Recommendation for Block Cipher Modes of Operation: Methods and Techniques, NIST SP 800-38A, 2001, Section 6.1. https://doi.org/10.6028/NIST.SP.800-38A

[5] A. F. Webster and S. E. Tavares. On the Design of S-Boxes. In H. C. Williams (ed.), Advances in Cryptology — CRYPTO '85 Proceedings, LNCS 218, pp. 523–534. Presented at CRYPTO '85, proceedings published in 1986. https://doi.org/10.1007/3-540-39799-X_41

[6] Python Cryptographic Authority. Authenticated encryption, `cryptography` documentation, AESGCM and ChaCha20Poly1305. https://cryptography.io/en/stable/hazmat/primitives/aead/

[7] C. E. Shannon. A Mathematical Theory of Communication. Bell System Technical Journal 27, pp. 379–423, 1948, Section 6. https://doi.org/10.1002/j.1538-7305.1948.tb01338.x

[8] NIST/SEMATECH. e-Handbook of Statistical Methods, Chi-Square Goodness-of-Fit Test, Section 1.3.5.15. https://www.itl.nist.gov/div898/handbook/eda/section3/eda35f.htm

[9] Python Software Foundation. `tracemalloc` documentation, `get_traced_memory()`. https://docs.python.org/3/library/tracemalloc.html

[10] Python Software Foundation. `time` documentation, `perf_counter_ns()`. https://docs.python.org/3/library/time.html

[11] NIST. A Statistical Test Suite for Random and Pseudorandom Number Generators for Cryptographic Applications, SP 800-22 Rev. 1a, 2010. https://doi.org/10.6028/NIST.SP.800-22r1a
