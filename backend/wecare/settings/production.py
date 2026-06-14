from .base import *

DEBUG = False

# AWS Elastic Beanstalk (and ALB) terminate SSL at the load balancer.
# Trust the forwarded proto header so Django detects HTTPS correctly.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
