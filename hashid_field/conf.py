from django.conf import settings

settings.HASHID_FIELD_SALT = getattr(settings, "HASHID_FIELD_SALT", "")
settings.HASHID_FIELD_MIN_LENGTH = getattr(settings, "HASHID_FIELD_MIN_LENGTH", 7)
settings.HASHID_FIELD_BIG_MIN_LENGTH = getattr(
    settings, "HASHID_FIELD_BIG_MIN_LENGTH", 13
)
settings.HASHID_FIELD_ALPHABET = getattr(
    settings,
    "HASHID_FIELD_ALPHABET",
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
)
settings.HASHID_FIELD_ALLOW_INT_LOOKUP = getattr(
    settings, "HASHID_FIELD_ALLOW_INT_LOOKUP", False
)
settings.HASHID_FIELD_LOOKUP_EXCEPTION = getattr(
    settings, "HASHID_FIELD_LOOKUP_EXCEPTION", False
)
settings.HASHID_FIELD_ENABLE_HASHID_OBJECT = getattr(
    settings, "HASHID_FIELD_ENABLE_HASHID_OBJECT", True
)
settings.HASHID_FIELD_ENABLE_DESCRIPTOR = getattr(
    settings, "HASHID_FIELD_ENABLE_DESCRIPTOR", True
)
