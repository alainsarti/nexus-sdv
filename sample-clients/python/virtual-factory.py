from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
# ... (Deine bestehenden cryptography Imports hier beibehalten)

app = FastAPI(title="Factory CA Service")

# Datenmodell für den Request
class SignRequest(BaseModel):
    vin: str
    device: str

# Datenmodell für die Antwort
class SignResponse(BaseModel):
    certificate: str
    private_key: str
    csr: str

# --- Deine bestehenden Funktionen (leicht angepasst für Rückgabewerte) ---

def generate_private_key_logic():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return key, key_pem.decode("utf-8")

def generate_csr_logic(private_key, vin, device):
    csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"VIN:{vin} DEVICE:{device}"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Valtech Mobility GmbH"),
        x509.NameAttribute(NameOID.COUNTRY_NAME, "DE"),
    ])).sign(private_key, hashes.SHA256())
    
    return csr, csr.public_bytes(serialization.Encoding.PEM).decode("utf-8")

def sign_csr_logic(csr):
    # Hier solltest du die Pfade idealerweise über Umgebungsvariablen laden
    oem_ca_cert = x509.load_pem_x509_certificate(open(OEM_CA_CERTIFICATE_PATH, "rb").read())
    oem_ca_key = serialization.load_pem_private_key(
        open(OEM_CA_KEY_PATH, "rb").read(), 
        OEM_CA_KEY_PASSWORD.encode() if OEM_CA_KEY_PASSWORD else None
    )

    cert = x509.CertificateBuilder().subject_name(csr.subject).issuer_name(
        oem_ca_cert.subject
    ).public_key(csr.public_key()).serial_number(
        x509.random_serial_number()
    ).not_valid_before(datetime.now(timezone.utc)).not_valid_after(
        datetime.now(timezone.utc) + CERTIFICATE_VALIDITY_TIME
    ).sign(oem_ca_key, hashes.SHA256())

    return cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

# --- Der API Endpoint ---

@app.post("/sign-car", response_model=SignResponse)
async def api_sign_car(request: SignRequest):
    try:
        # 1. Key generieren
        priv_key_obj, priv_key_pem = generate_private_key_logic()
        
        # 2. CSR generieren
        csr_obj, csr_pem = generate_csr_logic(priv_key_obj, request.vin, request.device)
        
        # 3. Signieren
        cert_pem = sign_csr_logic(csr_obj)
        
        return SignResponse(
            certificate=cert_pem,
            private_key=priv_key_pem,
            csr=csr_pem
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)