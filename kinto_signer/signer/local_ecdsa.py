import base64
import six

import ecdsa
from ecdsa import NIST384p, SigningKey, VerifyingKey
import hashlib

from .exceptions import BadSignatureError


class ECDSASigner(object):

    def __init__(self, private_key=None, public_key=None):
        if private_key is None and public_key is None:
            msg = ("Please, specify either a private_key or public_key "
                   "location.")
            raise ValueError(msg)
        self.private_key = private_key
        self.public_key = public_key

    @classmethod
    def generate_keypair(cls):
        sk = SigningKey.generate(curve=NIST384p)
        vk = sk.get_verifying_key()
        return sk.to_pem(), vk.to_pem()

    def load_private_key(self):
        if self.private_key is None:
            msg = 'Please, specify the private_key location.'
            raise ValueError(msg)

        with open(self.private_key, 'rb') as key_file:
            return SigningKey.from_pem(key_file.read())

    def load_public_key(self):
        # Check settings validity
        if self.private_key:
            private_key = self.load_private_key()
            return private_key.get_verifying_key()
        elif self.public_key:
            with open(self.public_key, 'rb') as key_file:
                return VerifyingKey.from_pem(key_file.read())

    def sign(self, payload):
        if isinstance(payload, six.text_type):  # pragma: nocover
            payload = payload.encode('utf-8')

        private_key = self.load_private_key()
        signature = private_key.sign(
            payload,
            hashfunc=hashlib.sha384,
            sigencode=ecdsa.util.sigencode_string)
        return base64.b64encode(signature).decode('utf-8')

    def verify(self, payload, signature):
        if isinstance(payload, six.text_type):  # pragma: nocover
            payload = payload.encode('utf-8')

        if isinstance(signature, six.text_type):  # pragma: nocover
            signature = signature.encode('utf-8')

        signature_bytes = base64.b64decode(signature)

        public_key = self.load_public_key()
        try:
            public_key.verify(
                signature_bytes,
                payload,
                hashfunc=hashlib.sha384,
                sigdecode=ecdsa.util.sigdecode_string)
        except Exception as e:
            raise BadSignatureError(e)


def load_from_settings(settings):
    private_key = settings.get('kinto_signer.ecdsa.private_key')
    public_key = settings.get('kinto_signer.ecdsa.public_key')
    try:
        return ECDSASigner(private_key=private_key, public_key=public_key)
    except ValueError:
        msg = ("Please specify either kinto_signer.ecdsa.private_key or "
               "kinto_signer.ecdsa.public_key in the settings.")
        raise ValueError(msg)