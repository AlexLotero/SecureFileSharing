#!/usr/bin/env python3

import ecdsa

def generate_key_pair():
    signing_key = ecdsa.SigningKey.generate() # uses NIST192p
    verifying_key = signing_key.verifying_key
    return signing_key, verifying_key

def generate_signature(data, signing, verifying):
    data_bytes = bytes(data, 'utf-8')
    signature = signing.sign(data_bytes)
    assert verifying.verify(signature, data_bytes)
    return signature

def verify_signature(data, verifying, signature):
    data_bytes = bytes(data, 'utf-8')
    if verifying.verify(signature, data_bytes):
        return True
    else:
        return False