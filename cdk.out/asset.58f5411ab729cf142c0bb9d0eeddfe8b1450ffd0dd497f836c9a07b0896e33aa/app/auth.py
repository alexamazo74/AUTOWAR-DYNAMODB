import os
from fastapi import Header, HTTPException, status

API_KEY = os.getenv('AUTOWAR_API_KEY')

def require_api_key(x_api_key: str = Header(...)):
    """Dependency to require a static API key provided in the `x-api-key` header.

    The server must set the `AUTOWAR_API_KEY` environment variable. If it's not set,
    the dependency will raise a 500 to force configuration.
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail='Server misconfigured: AUTOWAR_API_KEY not set')
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid API Key')
    return True
