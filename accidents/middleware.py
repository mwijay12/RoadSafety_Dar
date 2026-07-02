"""
Security middleware — adds hardening headers without extra packages.
"""


class SecurityHeadersMiddleware:
    """Adds CSP, Permissions-Policy, and Referrer-Policy headers to every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content Security Policy — allow Google Fonts, Leaflet, Chart.js CDN
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://unpkg.com; "
            "connect-src 'self' https://*.tile.openstreetmap.org https://unpkg.com https://cdn.jsdelivr.net https://api.elevenlabs.io; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
        response["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=(), payment=()"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["X-Content-Type-Options"] = "nosniff"

        return response
