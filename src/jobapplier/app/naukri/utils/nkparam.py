# app/utils/nkparam.py

import base64
import time

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from jobapplier.app.config import NAUKRI_PUBLIC_KEY

# Credits: Traverser25

def generate_nkparam(page_type: str = "srp") -> str:
    """
    Generate the nkparam header value required by Naukri APIs.

    The payload is constructed as:
        v0|<timestamp_ms>|121_<page_type>

    It is then RSA encrypted using Naukri's public key
    and Base64 encoded.
    """
    timestamp = int(time.time() * 1000)

    plaintext = f"v0|{timestamp}|121_{page_type}"

    public_key = RSA.import_key(NAUKRI_PUBLIC_KEY)
    cipher = PKCS1_v1_5.new(public_key)

    encrypted = cipher.encrypt(plaintext.encode("utf-8"))

    return base64.b64encode(encrypted).decode("utf-8")