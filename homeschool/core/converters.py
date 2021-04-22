from hashid_field.conf import settings as hashid_field_settings


class HashidConverter:
    regex = (
        "["
        + hashid_field_settings.HASHID_FIELD_ALPHABET
        + "]{"
        + str(hashid_field_settings.HASHID_FIELD_MIN_LENGTH)
        + ",}"
    )

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
