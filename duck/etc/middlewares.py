# List of all recommended Duck middlewares.

# ordinary middlewares
middlewares = [
    "duck.http.middlewares.security.RequestsLimitMiddleware",  # Protects against Denial of Service (DOS) attacks.
    "duck.http.middlewares.contrib.WWWRedirectMiddleware", # Redirect www urls to non-www urls
    "duck.http.middlewares.security.URLSecurityMiddleware",  # Protects against URL-based attacks.
    "duck.http.middlewares.security.SQLInjectionMiddleware",  # Protects against SQL injection attacks.
    "duck.http.middlewares.security.XSSMiddleware",  # Protects against Cross-Site Scripting (XSS) attacks.
    "duck.http.middlewares.security.CommandInjectionMiddleware",  # Protects against command injection attacks.
    "duck.http.middlewares.security.HostMiddleware",  # Validates the Host header to prevent unknown host attacks.
    "duck.http.middlewares.security.HeaderInjectionMiddleware",  # Prevents header injection attacks.
    "duck.http.middlewares.contrib.SessionMiddleware",  # Creates sessions for users ensuring secure storage of user sessions.
    "duck.http.middlewares.security.CSRFMiddleware",  # Protects against Cross-Site Request Forgery (CSRF) attacks.
]
