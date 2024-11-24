import helpers
from typing import Any
from django.conf import settings
from django.core.management.base import BaseCommand

VENDOR_STATICFILES = {
    "flowbite.min.css" : "https://cdn.jsdelivr.net/npm/flowbite@2.5.2/dist/flowbite.min.css",
    "flowbite.min.js" : "https://cdn.jsdelivr.net/npm/flowbite@2.5.2/dist/flowbite.min.js",
    "flowbite.min.js.map" : "https://cdn.jsdelivr.net/npm/flowbite@2.5.2/dist/flowbite.min.js.map",
}

STATICFILES_VENDOR_DIR = getattr(settings, 'STATICFILES_VENDOR_DIR')

class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        self.stdout.write("Downloading vendor static files")

        completed_urls = []
        for name, url in VENDOR_STATICFILES.items():
            out_path = STATICFILES_VENDOR_DIR / name
            dl_status = helpers.download_to_local(url, out_path)
            
            if dl_status:
                completed_urls.append(url)
            else:
                self.stdout.write(self.style.ERROR(f"Failed to download {url}"))

        if set(completed_urls) == set(VENDOR_STATICFILES.values()):
            self.stdout.write(
                self.style.SUCCESS(f"Successfully updated vendor static files")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Failed to update vendor static files")
            )