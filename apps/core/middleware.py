from django.conf import settings


class DefaultToEnglishMiddleware:
    """
    Django's LocaleMiddleware picks a language in this order: language
    cookie -> Accept-Language header -> LANGUAGE_CODE. Without this, a
    first-time visitor with a Greek browser locale would see Greek before
    ever touching the language switcher - the site should default to
    English for everyone and only switch on an explicit toggle (which
    sets the cookie). Blanking Accept-Language when no language cookie is
    present yet neutralizes just that one step; the cookie-based override
    from the switcher is untouched.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.LANGUAGE_COOKIE_NAME not in request.COOKIES:
            request.META["HTTP_ACCEPT_LANGUAGE"] = ""
        return self.get_response(request)
