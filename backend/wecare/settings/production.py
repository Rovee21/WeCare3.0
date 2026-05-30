from .base import *

DEBUG = False

# RDS database URL comes from DATABASE_URL env var (set in AWS env / ECS task definition)

# S3 static files (optional — can use WhiteNoise instead)
# STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
