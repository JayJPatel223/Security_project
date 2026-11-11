"""Local educational encryption experiments; the toy cipher is deliberately insecure."""
import argparse
import json
import os
import platform
import ssl
import sys
import time
import tracemalloc
from pathlib import Path

import cryptography
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

NAMES = ('AES-128-GCM', 'AES-256-GCM', 'ChaCha20-Poly1305', 'Toy-XOR-16')
AAD = b'course-project-v1'


def xor(a, b):
    if len(a) != len(b):
        raise ValueError('XOR inputs must have equal lengths')
    return bytes(x ^ y for x, y in zip(a, b))


class ToyCipher:
    """16-bit repeated-key XOR: no nonce, authentication, or meaningful security."""
    def __init__(self, key):
        if len(key) != 2:
            raise ValueError('Toy key must contain exactly two bytes')
        self.key = key

    def encrypt(self, nonce, data, aad):
        return bytes(v ^ self.key[i % 2] for i, v in enumerate(data))

    decrypt = encrypt


def make_cipher(name):
    if name == 'AES-128-GCM':
        return AESGCM(AESGCM.generate_key(bit_length=128))
    if name == 'AES-256-GCM':
        return AESGCM(AESGCM.generate_key(bit_length=256))
    if name == 'ChaCha20-Poly1305':
        return ChaCha20Poly1305(ChaCha20Poly1305.generate_key())
    if name == 'Toy-XOR-16':
        return ToyCipher(os.urandom(2))
    raise ValueError(name)


def flip(data, index=0):
    result = bytearray(data)
    result[index] ^= 1
    return bytes(result)


def rejects(cipher, nonce, ciphertext, aad):
    try:
        cipher.decrypt(nonce, ciphertext, aad)
    except InvalidTag:
        return True
    return False


def security_experiments():
    results = {}
    p1 = b'Known classroom message number 1.'
    p2 = b'Other classroom message number 2.'
    assert len(p1) == len(p2)
    for name in NAMES[:3]:
        cipher = make_cipher(name)
        nonce = bytes(12)
        c1 = cipher.encrypt(nonce, p1, AAD)
        # Deliberate misuse, confined to this disposable demonstration key.
        c2 = cipher.encrypt(nonce, p2, AAD)
        recovered = xor(xor(c1[:-16], c2[:-16]), p1)
        results[name] = {
            'round_trip': cipher.decrypt(nonce, c1, AAD) == p1,
            'ciphertext_tampering_rejected': rejects(cipher, nonce, flip(c1), AAD),
            'tag_tampering_rejected': rejects(cipher, nonce, flip(c1, -1), AAD),
            'wrong_aad_rejected': rejects(cipher, nonce, c1, b'wrong'),
            'wrong_nonce_rejected': rejects(cipher, flip(nonce), c1, AAD),
            'nonce_reuse_known_plaintext_recovers_second_message': recovered == p2,
        }
    block = b'REPEATED-BLOCK!!'
    assert len(block) == 16
    enc = Cipher(algorithms.AES(os.urandom(16)), modes.ECB()).encryptor()
    ciphertext = enc.update(block * 4) + enc.finalize()
    results['AES-ECB'] = {'identical_ciphertext_blocks': len({ciphertext[i:i+16] for i in range(0, 64, 16)}) == 1}
    key = (45000).to_bytes(2, 'big')
    toy = ToyCipher(key)
    plaintext = b'KNOWN educational plaintext for exhaustive key search'
    ciphertext = toy.encrypt(None, plaintext, None)
    started = time.perf_counter_ns()
    candidates = []
    # Full 65,536-key search, using a known plaintext/ciphertext pair.
    for candidate in range(65536):
        candidate_bytes = candidate.to_bytes(2, 'big')
        if ToyCipher(candidate_bytes).decrypt(None, ciphertext, None) == plaintext:
            candidates.append(candidate)
    results['Toy-XOR-16'] = {
        'keyspace': 65536, 'keys_tested': 65536,
        'recovered_keys': candidates, 'actual_key': 45000,
        'unique_correct_key_recovered': candidates == [45000],
        'search_ms': (time.perf_counter_ns() - started) / 1e6,
        'tampering_accepted': toy.decrypt(None, flip(ciphertext), None) != plaintext,
    }
    return results


def diffusion_experiments(trials=100):
    """Same nonce within disposable experiment keys isolates one-bit input changes.

    GCM and ChaCha are stream-like here: plaintext flips do not cause ciphertext
    avalanche. Tags and ciphertext bodies must be measured separately.
    """
    rows = []
    for name in NAMES:
        for trial in range(trials):
            cipher = make_cipher(name)
            data = os.urandom(64)
            changed = flip(data, trial % len(data))
            a = cipher.encrypt(bytes(12), data, AAD)
            b = cipher.encrypt(bytes(12), changed, AAD)
            body_a, body_b = (a, b) if name == 'Toy-XOR-16' else (a[:-16], b[:-16])
            distance = lambda x, y: sum(v.bit_count() for v in xor(x, y))
            rows.append({'algorithm': name, 'trial': trial,
                         'body_changed_bits': distance(body_a, body_b),
                         'body_total_bits': len(body_a)*8,
                         'tag_changed_bits': None if name == 'Toy-XOR-16' else distance(a[-16:], b[-16:])})
    return pd.DataFrame(rows)


def benchmark(sizes, repetitions, warmups=5):
    rows = []
    for name in NAMES:
        cipher = make_cipher(name)
        counter = 0
        for size in sizes:
            data = os.urandom(size)
            for repeat in range(-warmups, repetitions):
                # Unique counter nonces per key, outside timed encryption.
                nonce = counter.to_bytes(12, 'big')
                counter += 1
                start = time.perf_counter_ns()
                ciphertext = cipher.encrypt(nonce, data, AAD)
                encrypt_ns = time.perf_counter_ns() - start
                start = time.perf_counter_ns()
                recovered = cipher.decrypt(nonce, ciphertext, AAD)
                decrypt_ns = time.perf_counter_ns() - start
                if recovered != data:
                    raise RuntimeError('Round trip failed')
                if repeat >= 0:
                    rows.append(dict(algorithm=name, size_bytes=size, repetition=repeat,
                                     encrypt_ns=encrypt_ns, decrypt_ns=decrypt_ns))
    return pd.DataFrame(rows)


def memory_measurements(sizes):
    rows = []
    for name in NAMES:
        cipher = make_cipher(name)
        for counter, size in enumerate(sizes):
            data = os.urandom(size)
            nonce = counter.to_bytes(12, 'big')
            # Separate from timing. tracemalloc cannot capture all native allocations.
            tracemalloc.start()
            ciphertext = cipher.encrypt(nonce, data, AAD)
            _, enc_peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            tracemalloc.start()
            recovered = cipher.decrypt(nonce, ciphertext, AAD)
            _, dec_peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            assert recovered == data
            rows.append(dict(algorithm=name, size_bytes=size,
                             python_encrypt_peak_bytes=enc_peak,
                             python_decrypt_peak_bytes=dec_peak))
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sizes', nargs='+', type=int, default=[1024, 10240, 102400, 1048576])
    parser.add_argument('--repetitions', type=int, default=30)
    parser.add_argument('--output', type=Path, default=Path('results'))
    args = parser.parse_args()
    if args.repetitions < 1 or any(size < 1 for size in args.sizes):
        parser.error('Sizes and repetitions must be positive')
    args.output.mkdir(parents=True, exist_ok=True)
    metadata = dict(timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    os=platform.platform(), cpu=platform.processor(), machine=platform.machine(),
                    python=sys.version, cryptography=cryptography.__version__,
                    numpy=np.__version__, pandas=pd.__version__, matplotlib=matplotlib.__version__,
                    python_ssl_openssl=ssl.OPENSSL_VERSION,
                    sizes=args.sizes, repetitions=args.repetitions, warmups=5,
                    note='Python SSL OpenSSL can differ from cryptography backend; see backend_openssl')
    from cryptography.hazmat.backends.openssl.backend import backend
    metadata['backend_openssl'] = backend.openssl_version_text()
    if Path('/proc/cpuinfo').exists():
        metadata['cpu_model'] = next((line.split(':', 1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), 'unknown')
    (args.output/'environment.json').write_text(json.dumps(metadata, indent=2))
    security = security_experiments()
    (args.output/'security.json').write_text(json.dumps(security, indent=2))
    diffusion_experiments().to_csv(args.output/'diffusion.csv', index=False)
    raw = benchmark(args.sizes, args.repetitions)
    raw.to_csv(args.output/'timings.csv', index=False)
    summary = raw.groupby(['algorithm', 'size_bytes']).agg(
        encrypt_median_ns=('encrypt_ns', 'median'), decrypt_median_ns=('decrypt_ns', 'median'),
        encrypt_p95_ns=('encrypt_ns', lambda s: np.percentile(s, 95)),
        decrypt_p95_ns=('decrypt_ns', lambda s: np.percentile(s, 95))).reset_index()
    for operation in ('encrypt', 'decrypt'):
        summary[f'{operation}_MiB_s'] = summary.size_bytes / (1024**2) / (summary[f'{operation}_median_ns']/1e9)
        fig, ax = plt.subplots(figsize=(9, 5))
        for name, group in summary.groupby('algorithm'):
            ax.plot(group.size_bytes, group[f'{operation}_MiB_s'], marker='o', label=name)
        ax.set(xscale='log', xlabel='Plaintext size (bytes)', ylabel='Throughput (MiB/s)',
               title=f'{operation.capitalize()} throughput: median of {args.repetitions} runs')
        ax.legend(); ax.grid(alpha=.25); fig.tight_layout()
        fig.savefig(args.output/f'{operation}_throughput.png', dpi=160)
        plt.close(fig)
    summary.to_csv(args.output/'summary.csv', index=False)
    memory_measurements(args.sizes).to_csv(args.output/'memory.csv', index=False)
    print(f'Completed. Results: {args.output.resolve()}')


if __name__ == '__main__':
    main()
