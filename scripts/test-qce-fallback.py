#!/usr/bin/env python3
"""Kernel AF_ALG known answers and Book4 QCE opt-out readiness
No module or policy changes
Run: python3 scripts/test-qce-fallback.py
Excluded: IPsec, legacy ciphers, explicit QCE driver requests, suspend power
"""
from pathlib import Path
import hashlib
import hmac
import signal
import socket
import struct

signal.alarm(20)
assert not Path('/sys/module/qcrypto').exists(), 'unload qcrypto before this check'
message = b'book4 software crypto check'
for name, key, expected in (
    ('sha1', None, hashlib.sha1(message).digest()),
    ('sha256', None, hashlib.sha256(message).digest()),
    ('hmac(sha1)', b'public-test-key', hmac.digest(b'public-test-key', message, 'sha1')),
    ('hmac(sha256)', b'public-test-key', hmac.digest(b'public-test-key', message, 'sha256')),
):
    with socket.socket(socket.AF_ALG, socket.SOCK_SEQPACKET) as algorithm:
        algorithm.bind(('hash', name))
        if key is not None:
            algorithm.setsockopt(socket.SOL_ALG, socket.ALG_SET_KEY, key)
        operation, _ = algorithm.accept()
        with operation:
            operation.sendall(message)
            assert operation.recv(len(expected)) == expected, name
    assert not Path('/sys/module/qcrypto').exists(), 'unexpected QCE autoload'
    print(name, 'passed')

with socket.socket(socket.AF_ALG, socket.SOCK_SEQPACKET) as algorithm:
    algorithm.bind(('skcipher', 'cbc(aes)'))
    algorithm.setsockopt(socket.SOL_ALG, socket.ALG_SET_KEY, bytes(16))
    operation, _ = algorithm.accept()
    with operation:
        operation.sendmsg([bytes(16)], [
            (socket.SOL_ALG, socket.ALG_SET_OP, struct.pack('I', socket.ALG_OP_ENCRYPT)),
            (socket.SOL_ALG, socket.ALG_SET_IV, struct.pack('I', 16) + bytes(16)),
        ])
        assert operation.recv(16).hex() == '66e94bd4ef8a2c3b884cfa59ca342b2e'
assert not Path('/sys/module/qcrypto').exists(), 'unexpected QCE autoload'
print('cbc(aes) passed, QCE remained absent')

providers = list(Path('/sys/bus/platform/devices').glob('*.interconnect/state_synced'))
assert providers, 'no interconnect providers found'
unsynced = [p.parent.name for p in providers if p.read_text().strip() != '1']
assert not unsynced, f'QCE opt-out blocked interconnect sync: {unsynced}'
summary = Path('/sys/kernel/debug/interconnect/interconnect_summary').read_text()
assert '2147483647' not in summary, 'interconnect initialization floor still present'
print('Interconnect synchronization complete, no INT_MAX bandwidth floor')
