import tempfile
import requests
import time

class Inter:

    def __init__(
            self, 
            url: str = "https://cdpj.partners.bancointer.com.br",
            client_id=None,
            client_secret=None,
            grant_type="client_credentials"
        ) -> None:
        self.__url = url
        self.__oauth = dict()
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__grant_type = grant_type
        self.__cert_path = None
        self.__prv_path = None

    def load_cert(self, cert: str, prv: str, is_format=False):
        if is_format:
            cert = cert.replace("-----BEGIN CERTIFICATE-----", "")
            cert = cert.replace("-----END CERTIFICATE-----", "")
            cert = [cert[i:i+64] for i in range(0, len(cert), 64)]
            cert = "\n".join(cert)
            cert = "-----BEGIN CERTIFICATE-----\n" + cert + "\n-----END CERTIFICATE-----"

            prv = prv.replace("-----BEGIN RSA PRIVATE KEY-----", "")
            prv = prv.replace("-----END RSA PRIVATE KEY-----", "")
            prv = [prv[i:i+64] for i in range(0, len(prv), 64)]
            prv = "\n".join(prv)
            prv = "-----BEGIN RSA PRIVATE KEY-----\n" + prv + "\n-----END RSA PRIVATE KEY-----"
    
        with tempfile.NamedTemporaryFile(mode='w+t', suffix='.tmp', delete=False) as f:
            f.write(cert)
            self.__cert_path = f.name
    
        with tempfile.NamedTemporaryFile(mode='w+t', suffix='.tmp', delete=False) as f:
            f.write(prv)
            self.__prv_path = f.name
    
    def get_token(self, scopes=["pix.read", "cob.read", "cob.write"]):
        self.__oauth = requests.post(
            url=self.__url + "/oauth/v2/token", 
            data={
                "client_id": self.__client_id,
                "client_secret": self.__client_secret,
                "grant_type": self.__grant_type,
                "scope": " ".join(scopes)
            }, 
            cert=(self.__cert_path, self.__prv_path)
        ).json()
        self.__oauth["expires_in"] = time.time() + self.__oauth["expires_in"]
        return self.__oauth
    
    def call(self, method: str, path: str, data=None, params=None):
        r = requests.request(
            method=method, 
            url=self.__url + path, 
            headers={ 
                "Authorization": f"{self.__oauth['token_type']} {self.__oauth['access_token']}" 
            },
            params=params, 
            json=data, cert=(
                self.__cert_path, 
                self.__prv_path
            ))
        r.raise_for_status()
        return r.text
    
    def get_balance(self):
        return self.call("GET", "/banking/v2/saldo")

    def create_cob(self, key: str, value: float, txid: str, expiry=900):
        return self.call("PUT", f"/pix/v2/cob/{txid}", data={
            "calendario": {
                "expiracao": expiry
            },
            "valor": {
                "original": f"{value:,.2f}",
                "modalidadeAlteracao": 0
            },
            "chave": key
        })
    
    def get_cob(self, txid: str):
        return self.call("GET", f"/pix/v2/cob/{txid}")
