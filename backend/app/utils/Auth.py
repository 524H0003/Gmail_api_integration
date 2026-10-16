from passlib.context import CryptContext
from app.core.config import settings
import jwt


class Auth:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    jwt_secret_key: str = ""

    def __init__(self):
        self.jwt_secret_key = settings.jwt_secret_key

    def hash_password(self, password: str) -> str:
        return Auth.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return Auth.pwd_context.verify(plain_password, hashed_password)

    def jwt_encode(self, input: object):
        return jwt.encode(input, self.jwt_secret_key, algorithm="HS256")

    def jwt_decode(self, token: str):
        try:
            return jwt.decode(token, self.jwt_secret_key, algorithms=["HS256"]).get(
                "sub"
            )
        except:
            return ""


auth = Auth()
