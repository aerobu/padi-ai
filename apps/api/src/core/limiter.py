from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize Rate Limiter singleton
limiter = Limiter(key_func=get_remote_address)
