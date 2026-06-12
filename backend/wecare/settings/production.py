from .base import *

DEBUG = False

# Railway (and most PaaS) terminate SSL at the load balancer and forward via HTTP internally.
# This tells Django to trust the X-Forwarded-Proto header so HTTPS is detected correctly.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
