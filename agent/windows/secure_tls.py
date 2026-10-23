"""Private keys are encrypted at rest; their passphrase is protected by DPAPI."""
import datetime
import ipaddress
import os
import secrets
import ssl
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def create_identity(directory, host, protector, now=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cert_path, key_path, pass_path = [directory / name for name in ('server.crt', 'server.key', 'tls.dpapi')]
    if any(p.exists() for p in (cert_path, key_path, pass_path)):
        raise FileExistsError('TLS identity already exists; never rotate implicitly')
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Lone Smart Room Agent')])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=5))
            .not_valid_after(now + datetime.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(host))]), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .sign(key, hashes.SHA256()))
    password = secrets.token_bytes(32)
    pass_path.write_bytes(protector.seal(password))
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.BestAvailableEncryption(password)))
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def fingerprint(directory):
    cert = x509.load_pem_x509_certificate((Path(directory) / 'server.crt').read_bytes())
    return cert.fingerprint(hashes.SHA256()).hex()


def server_context(directory, protector):
    directory = Path(directory)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(directory / 'server.crt', directory / 'server.key',
                            password=lambda: protector.open((directory / 'tls.dpapi').read_bytes()))
    return context
