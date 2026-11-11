import pytest
from cryptography.exceptions import InvalidTag
from crypto_model import NAMES, ToyCipher, make_cipher, benchmark, security_experiments, diffusion_experiments


@pytest.mark.parametrize('name', NAMES)
@pytest.mark.parametrize('data', [b'', b'x', bytes(range(256))*3])
def test_roundtrip(name, data):
    cipher = make_cipher(name)
    assert cipher.decrypt(bytes(12), cipher.encrypt(bytes(12), data, b'aad'), b'aad') == data


@pytest.mark.parametrize('name', NAMES[:3])
def test_wrong_key_rejected(name):
    ciphertext = make_cipher(name).encrypt(bytes(12), b'message', b'aad')
    with pytest.raises(InvalidTag):
        make_cipher(name).decrypt(bytes(12), ciphertext, b'aad')


def test_all_security_demonstrations():
    results = security_experiments()
    for name in NAMES[:3]:
        assert all(results[name].values())
    assert results['AES-ECB']['identical_ciphertext_blocks']
    assert results['Toy-XOR-16']['unique_correct_key_recovered']
    assert results['Toy-XOR-16']['tampering_accepted']


def test_mode_appropriate_diffusion():
    rows = diffusion_experiments(3)
    assert (rows.body_changed_bits == 1).all()
    assert rows.loc[rows.algorithm == 'Toy-XOR-16', 'tag_changed_bits'].isna().all()


def test_benchmark_shape():
    rows = benchmark([16, 128], 2, warmups=1)
    assert len(rows) == 16
    assert (rows.encrypt_ns > 0).all()
    assert (rows.decrypt_ns > 0).all()


def test_toy_key_validation():
    with pytest.raises(ValueError):
        ToyCipher(b'x')
