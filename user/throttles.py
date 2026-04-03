from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Throttle specifically for the login endpoint.

    Limits unauthenticated (anonymous) requests by IP address.
    Rate is controlled by the 'login' key in REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].

    Default: 5 attempts per minute per IP.
    """

    scope = "login"
