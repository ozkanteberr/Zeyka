from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt

# DİKKAT: Bu bilgilerin diğer servislerle (örn: user-service) birebir aynı olması gerekir.
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

API_KEY_SCHEME = APIKeyHeader(name="Authorization", auto_error=False)

def get_current_user_id(token: str = Depends(API_KEY_SCHEME)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token or not token.startswith("Bearer "):
        raise credentials_exception

    token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception

        # Not: Gerçek bir uygulamada, bu email ile veritabanından kullanıcıyı
        # bulup onun ID'sini döndürmek daha doğrudur. Projemizin bu aşamasında,
        # test amacıyla varsayımsal bir ID döndürüyoruz.
        return 1 # Varsayımsal Kullanıcı ID'si

    except JWTError:
        raise credentials_exception