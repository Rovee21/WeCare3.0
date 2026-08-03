from .base import *

DEBUG = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env.bool("SECURE_SSL_REDIRECT", default=True)
CSRF_COOKIE_SECURE = env.bool("SECURE_SSL_REDIRECT", default=True)
