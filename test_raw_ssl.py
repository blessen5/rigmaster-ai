import socket, ssl, sys

host = 'ac-afd629f-shard-00-00.99f5zmr.mongodb.net'
port = 27017

print(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
print(f"Testing raw TLS socket to {host}:{port}...\n")

for version_name, min_ver, max_ver in [
    ("TLS 1.2 only", ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_2),
    ("TLS 1.3 only", ssl.TLSVersion.TLSv1_3, ssl.TLSVersion.TLSv1_3),
    ("TLS 1.2+",     ssl.TLSVersion.TLSv1_2, None),
]:
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.minimum_version = min_ver
        if max_ver:
            ctx.maximum_version = max_ver

        s = socket.create_connection((host, port), timeout=10)
        ss = ctx.wrap_socket(s, server_hostname=host)
        print(f"✅ SUCCESS [{version_name}]: {ss.version()} / {ss.cipher()[0]}")
        ss.close()
    except ssl.SSLError as e:
        print(f"❌ SSL FAILED [{version_name}]: {e}")
    except Exception as e:
        print(f"❌ FAILED [{version_name}]: {e}")
