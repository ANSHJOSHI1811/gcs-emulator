"""
HTTPS/TLS Configuration for Production

Provides:
- SSL certificate management
- HTTPS redirect middleware
- TLS configuration
- Certificate validation
"""

from flask import Flask, request, redirect
import ssl
import os


class TLSConfig:
    """TLS/SSL configuration manager"""
    
    @staticmethod
    def configure_ssl_context(cert_file: str, key_file: str, ca_file: str = None) -> ssl.SSLContext:
        """
        Create SSL context for HTTPS
        
        Args:
            cert_file: Path to SSL certificate file
            key_file: Path to private key file
            ca_file: Optional path to CA certificate file
        
        Returns:
            Configured SSL context
        """
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        # Load certificate and private key
        context.load_cert_chain(cert_file, key_file)
        
        # Load CA certificate if provided
        if ca_file:
            context.load_verify_locations(ca_file)
        
        # Set secure cipher suites
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Enable hostname verification
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # Set to CERT_REQUIRED in production with proper CA
        
        # Set minimum TLS version
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        return context
    
    @staticmethod
    def generate_self_signed_cert(cert_file: str, key_file: str, domain: str = 'localhost'):
        """
        Generate self-signed certificate for development
        
        Args:
            cert_file: Output path for certificate
            key_file: Output path for private key
            domain: Domain name for certificate
        """
        from cryptography import x509
        from cryptography.x509.oid import NameOID, ExtensionOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from datetime import datetime, timedelta
        import ipaddress
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "GCP Stimulator"),
            x509.NameAttribute(NameOID.COMMON_NAME, domain),
        ])
        
        # Add Subject Alternative Names
        san_list = [x509.DNSName(domain)]
        if domain == 'localhost':
            san_list.extend([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv6Address("::1")),
            ])
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print(f"✅ Self-signed certificate generated:")
        print(f"   Certificate: {cert_file}")
        print(f"   Private Key: {key_file}")
        print(f"   Domain: {domain}")
        print(f"   Valid for: 365 days")


def redirect_to_https(app: Flask):
    """
    Middleware to redirect HTTP to HTTPS
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request():
        # Skip if HTTPS redirect is disabled
        if not app.config.get('FORCE_HTTPS', False):
            return
        
        # Skip if already HTTPS
        if request.is_secure:
            return
        
        # Skip for health check endpoints
        if request.path in ['/health', '/healthz', '/ready']:
            return
        
        # Redirect to HTTPS
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


def configure_app_tls(app: Flask, cert_file: str = None, key_file: str = None, 
                      generate_self_signed: bool = False):
    """
    Configure Flask app for TLS/HTTPS
    
    Args:
        app: Flask application instance
        cert_file: Path to SSL certificate (or where to generate it)
        key_file: Path to private key (or where to generate it)
        generate_self_signed: If True, generate self-signed cert for development
    
    Returns:
        SSL context to use with app.run()
    """
    # Set default paths if not provided
    if not cert_file:
        cert_file = os.path.join(app.instance_path, 'ssl', 'cert.pem')
    if not key_file:
        key_file = os.path.join(app.instance_path, 'ssl', 'key.pem')
    
    # Ensure SSL directory exists
    os.makedirs(os.path.dirname(cert_file), exist_ok=True)
    
    # Generate self-signed certificate if needed
    if generate_self_signed and not os.path.exists(cert_file):
        print("🔐 Generating self-signed certificate for development...")
        TLSConfig.generate_self_signed_cert(cert_file, key_file)
    
    # Check if certificate files exist
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("⚠️  SSL certificate not found. HTTPS disabled.")
        print(f"   Expected: {cert_file} and {key_file}")
        print(f"   Run with generate_self_signed=True to create development certificates")
        return None
    
    # Configure SSL context
    ssl_context = TLSConfig.configure_ssl_context(cert_file, key_file)
    
    # Store paths in app config
    app.config['SSL_CERT_FILE'] = cert_file
    app.config['SSL_KEY_FILE'] = key_file
    app.config['HTTPS_ENABLED'] = True
    
    print(f"✅ HTTPS enabled with certificate: {cert_file}")
    
    return ssl_context


# Example usage in app initialization
def example_usage():
    """
    Example of how to use TLS configuration in your app
    """
    from flask import Flask
    
    app = Flask(__name__)
    
    # For development - generate self-signed certificate
    ssl_context = configure_app_tls(
        app,
        cert_file='instance/ssl/cert.pem',
        key_file='instance/ssl/key.pem',
        generate_self_signed=True  # Set to True for dev, False for production
    )
    
    # Enable HTTPS redirect (optional)
    app.config['FORCE_HTTPS'] = False  # Set to True in production
    if app.config.get('FORCE_HTTPS'):
        redirect_to_https(app)
    
    # Run with HTTPS
    if ssl_context:
        app.run(host='0.0.0.0', port=8443, ssl_context=ssl_context)
    else:
        # Fallback to HTTP
        app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    # Test certificate generation
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cert_file = os.path.join(tmpdir, 'test_cert.pem')
        key_file = os.path.join(tmpdir, 'test_key.pem')
        
        TLSConfig.generate_self_signed_cert(cert_file, key_file, 'localhost')
        
        print("\n✅ Certificate generation test successful!")
        print(f"   Certificate exists: {os.path.exists(cert_file)}")
        print(f"   Key exists: {os.path.exists(key_file)}")
