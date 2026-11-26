from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage


def find_image(folder, key):
    if not key:
        return ""

    for ext in ["jpg", "jpeg", "webp", "png", "svg"]:
        path = f"{folder}/{key}.{ext}"
        if finders.find(path):
            return staticfiles_storage.url(path)

    return ""