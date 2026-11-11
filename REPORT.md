# Security and Performance Evaluation of AES-GCM and ChaCha20-Poly1305 with a Custom Experimental Cipher

Jay Patel and Sami Darouiche

Draft prepared from the project prototype. All numbers below were measured by the project code; nothing is estimated. See Section 6 for important caveats, including that the timing data came from a cloud container and should be re-collected on your own computer before submission.

## 1. Research question and background

Using a strong encryption algorithm does not by itself make a system secure. Implementation mistakes, misuse of modes, nonce reuse, weak keys and poorly designed custom algorithms can all defeat otherwise sound cryptography. This project asks:

How do AES-128-GCM, AES-256-GCM and ChaCha20-Poly1305 compare in performance and in resistance to common misuse, and what does a deliberately weak custom cipher show about why designing cryptography is hard?

AES-GCM and ChaCha20-Poly1305 are authenticated encryption with associated data (AEAD) constructions. They encrypt the message and also produce a 16-byte authentication tag that is checked before decrypted data is accepted. Both take a nonce, and the Python cryptography library documentation states: "Reuse of a nonce with a given key compromises the security of any message with that nonce and key pair" (cryptography documentation, AEAD page [6]). The standards for these constructions are NIST SP 800-38D for GCM [2] and RFC 8439 for ChaCha20-Poly1305 [3]; AES itself is specified in FIPS 197 [1] and the ECB mode in NIST SP 800-38A [4].

## 2. Environment and experimental methods

Environment (recorded automatically in environment.json):

- OS: Linux-6.18.44-fc-v378-x86_64-with-glibc2.39
- CPU: Intel(R) Xeon(R) Processor @ 2.10GHz (2 cores available)
- Python: 3.13.18
- cryptography 50.0.2, NumPy 2.5.4, pandas 3.1.1, Matplotlib 3.11.2
- cryptography backend: OpenSSL 4.0.3 29 Sep 2026

Method summary:

- All data is synthetic random bytes. No real confidential data was used.
- Sizes: 1 KiB, 10 KiB, 100 KiB, 1 MiB. Each configuration had 5 discarded warm-up operations and 30 measured repetitions.
- The full benchmark was run 3 separate times so that run-to-run variation could be reported. Throughput values in this report are the median across the 3 runs of each run's median time.
- Timing uses time.perf_counter_ns(). Key creation, data generation, nonce creation, correctness checks, file output and plotting are outside the timed region. Tag creation/verification and library-call overhead are inside it.
- Each algorithm uses a fresh random key, and benchmark nonces are unique counters per key.
- Throughput = plaintext bytes divided by median time, in MiB/s.
- Memory was measured separately with tracemalloc, one sample per size and operation.
- The fixed benchmark order (AES-128-GCM, AES-256-GCM, ChaCha20-Poly1305, Toy) means ordering and system load can affect results.

## 3. Cipher implementations and toy-cipher limitations

The three standard ciphers use the cryptography library's AESGCM and ChaCha20Poly1305 classes with a fixed public associated-data label, so both ciphertext and associated data are authenticated.

The custom cipher, Toy-XOR-16, XORs each plaintext byte with one of two repeating key bytes. It has these deliberate weaknesses:

- 16-bit keyspace: 65,536 possible keys.
- No authentication, and it ignores the nonce and associated data.
- Repeating-key structure, so identical plaintext blocks give identical ciphertext blocks.
- Known-plaintext weakness: the first two plaintext and ciphertext bytes reveal the whole key.

It is a teaching baseline, not a design to be compared on equal terms with the standard ciphers. It is also written as a pure-Python loop while the standard ciphers run compiled library code, so its speed difference mostly reflects the programming language, not cipher design.

## 4. Performance results

Encryption throughput (MiB/s, median of 3 runs):

| Algorithm | 1 KiB | 10 KiB | 100 KiB | 1 MiB |
|---|---|---|---|---|
| AES-128-GCM | 1,083 | 5,671 | 9,869 | 8,383 |
| AES-256-GCM | 1,048 | 5,228 | 8,942 | 7,740 |
| ChaCha20-Poly1305 | 474 | 1,932 | 2,823 | 2,769 |
| Toy-XOR-16 | 16.7 | 15.3 | 14.4 | 15.0 |

Decryption throughput (MiB/s, median of 3 runs):

| Algorithm | 1 KiB | 10 KiB | 100 KiB | 1 MiB |
|---|---|---|---|---|
| AES-128-GCM | 1,165 | 5,837 | 10,028 | 8,596 |
| AES-256-GCM | 1,075 | 5,181 | 9,055 | 7,907 |
| ChaCha20-Poly1305 | 491 | 1,976 | 2,930 | 2,843 |
| Toy-XOR-16 | 16.7 | 15.5 | 14.5 | 14.9 |

Figure: full_results/combined/combined_throughput.png (median of 3 runs, shaded band showing min to max across runs).

Observations (measured on this machine only):

- At 1 MiB, AES-128-GCM encrypted at about 8,383 MiB/s and ChaCha20-Poly1305 at about 2,769 MiB/s, a ratio of about 3.0 to 1. At 1 KiB the ratio was about 2.3 to 1.
- AES-256-GCM ran at about 92% of AES-128-GCM's encryption throughput at 1 MiB.
- Throughput rises with size from 1 KiB to 100 KiB because fixed per-call overhead is spread over more bytes, which matches the README's warning that small-input results include substantial call overhead.
- The toy cipher ran at roughly 15 MiB/s regardless of size, about 560 times slower than AES-128-GCM at 1 MiB, for the reason given in Section 3.

Run-to-run variation. The largest ratio between the fastest and slowest of the 3 runs for any single configuration was 1.31x, and the median ratio across all configurations was 1.07x. Largest max/min ratio per configuration (encryption and decryption combined):

| Algorithm | 1 KiB | 10 KiB | 100 KiB | 1 MiB |
|---|---|---|---|---|
| AES-128-GCM | 1.08x | 1.06x | 1.03x | 1.07x |
| AES-256-GCM | 1.12x | 1.06x | 1.23x | 1.12x |
| ChaCha20-Poly1305 | 1.18x | 1.31x | 1.09x | 1.04x |
| Toy-XOR-16 | 1.18x | 1.08x | 1.29x | 1.04x |

Because differences of this size occur between identical runs, gaps smaller than roughly this variation (for example AES-128-GCM versus AES-256-GCM at some sizes) should not be presented as firm findings. The AES-GCM versus ChaCha20-Poly1305 gap is much larger than the run-to-run spread. The AES result likely depends on hardware AES instructions on the test CPU (the CPU reports the aes, pclmulqdq and vaes flags in /proc/cpuinfo). The ranking may differ on other hardware, as the proposal anticipated.

Memory (Python allocation peaks via tracemalloc; one sample each, exploratory; native library allocations are not captured):

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

For the three standard ciphers the traced Python peak was about the input size plus a small constant (49 bytes at 1 KiB and at 1 MiB for encryption), consistent with the output buffer. The toy cipher's peak was higher at 1 MiB (about 1.2 times the input size); its pure-Python loop likely creates intermediate objects, though the cause was not investigated. These figures do not describe total process memory.

## 5. Security experiment evidence

All results below held in all 3 runs.

Tampering. For AES-128-GCM, AES-256-GCM and ChaCha20-Poly1305, decryption raised InvalidTag when a ciphertext bit was flipped, when a tag bit was flipped, when the associated data was wrong, and when the nonce was wrong. The unit tests additionally check that a wrong key is rejected. The toy cipher accepted a flipped ciphertext bit without any error and returned altered plaintext.

Nonce reuse. Using a disposable key, one nonce was deliberately reused for two equal-length messages. For all three standard ciphers, XORing the two ciphertext bodies (tags excluded) gave the XOR of the two plaintexts, and knowing the first plaintext recovered the second. This demonstrates loss of confidentiality. It does not show tag forgery or recovery of the encryption key.

ECB leakage. Four identical 16-byte blocks encrypted with AES in ECB mode produced one distinct ciphertext block out of four, in every run. ECB is a separate illustration and not one of the benchmarked constructions.

Brute force. The complete 65,536-key search against the toy cipher, using a known plaintext/ciphertext pair, found exactly one matching key, the correct one, in all 3 runs. Search time was 265 to 338 ms in a pure-Python loop.

Diffusion (100 trials per algorithm per run, 300 total, flipping one bit of a 64-byte plaintext with key and nonce fixed within each pair). The ciphertext body changed by exactly one bit for all four constructions, including the three AEADs, because they are stream-like. A one-bit change in the plaintext therefore does not spread through the body. Authentication tags changed on average by 63.9 bits (AES-128-GCM), 63.7 bits (AES-256-GCM) and 64.0 bits (ChaCha20-Poly1305) out of 128, with an observed range of 48 to 82 bits. Diffusion alone is therefore not a good measure of security for these modes.

Output characteristics (new experiment in extra_experiments.py). A 64 KiB plaintext made of one repeated 16-byte block, which has an entropy of 3.58 bits per byte, was encrypted 30 times per construction:

| Construction | Mean entropy (bits/byte) | Mean chi-square (255 d.f.) | Distinct 16-byte blocks (of 4,096) |
|---|---|---|---|
| AES-128-GCM | 7.997 | 248 | 4096 |
| AES-256-GCM | 7.997 | 259 | 4096 |
| ChaCha20-Poly1305 | 7.997 | 258 | 4096 |
| AES-128-ECB | 3.913 | 1,074,790 | 1 |
| Toy-XOR-16 | 3.857 | 1,135,957 | 1 |

The AEADs produced near-uniform bytes (a 64 KiB sample cannot reach exactly 8.0 bits, so about 7.997 is the expected ceiling) and no repeated blocks. ECB and the toy cipher kept the plaintext's repeated structure. The chi-square acceptance range of about 197 to 313 is a normal approximation, and the fraction of ChaCha20-Poly1305 samples inside it was 97% (about 1% of samples are expected outside by chance). These statistics only describe appearance. Even where a statistic looks acceptable, it is not evidence of security: the toy cipher falls to a trivial key search whatever its byte statistics look like.

## 6. Limitations, interpretation and conclusions

Limitations:

- The timing data came from a 2-core cloud container and not from your own hardware. Rerun the full benchmark on the machine you will describe in the report and replace the tables.
- Only 3 whole runs were used. Differences smaller than the run-to-run spread above should not be claimed.
- The benchmark order is fixed, and the toy cipher is pure Python, so its speed is not a fair cipher comparison.
- Memory results are single-sample Python allocation peaks only.
- The experiments demonstrate specific properties and misuse cases. They are not security proofs and do not test side channels, key management or protocol design.

Conclusions, each supported by the results above:

1. Under correct use, all three standard AEAD ciphers detected every tampering attempt tested, and produced ciphertext with near-uniform byte statistics even for highly repetitive plaintext.
2. On this hardware, AES-GCM was substantially faster than ChaCha20-Poly1305, with the size of the gap larger than the run-to-run variation. Hardware dependence means this should be re-measured on the final test machine.
3. Nonce reuse broke confidentiality for all three standard ciphers, even though everything else was done correctly. Correct use matters as much as algorithm choice.
4. ECB leaked structure and the toy cipher was broken by an exhaustive search of 65,536 keys, accepted tampering silently, and also leaked structure. Ciphertext that looks irregular is not the same as a secure design.

## References

[1] National Institute of Standards and Technology. Advanced Encryption Standard (AES), FIPS PUB 197-upd1, 2023. https://doi.org/10.6028/NIST.FIPS.197-upd1
[2] Dworkin, M. Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC, NIST SP 800-38D, 2007. https://doi.org/10.6028/NIST.SP.800-38D
[3] Nir, Y., and Langley, A. ChaCha20 and Poly1305 for IETF Protocols, RFC 8439, 2018. https://www.rfc-editor.org/rfc/rfc8439
[4] Dworkin, M. Recommendation for Block Cipher Modes of Operation: Methods and Techniques, NIST SP 800-38A, 2001. https://doi.org/10.6028/NIST.SP.800-38A
[5] Webster, A. F., and Tavares, S. E. On the Design of S-Boxes, Advances in Cryptology, CRYPTO '85, 1985. (Cited in the proposal; add a specific point from it if you discuss the toy cipher's design.)
[6] Python cryptography documentation, AEAD primitives (AESGCM and ChaCha20Poly1305; page consulted for version 46.0.4, while this project ran version 50.0.2). https://cryptography.io/en/stable/hazmat/primitives/aead/
