from django.test import TestCase
from django.core.management import call_command
from django.conf import settings
from unittest.mock import patch, MagicMock
import os

class VendorPullTest(TestCase):
    @patch('helpers.download_to_local')
    def test_vendor_pull_command(self, mock_download_to_local):
        mock_download_to_local.return_value = True
        call_command('vendor_pull')
        self.assertEqual(mock_download_to_local.call_count, 4)
        for name, url in settings.VENDOR_STATICFILES.items():
            out_path = settings.STATICFILES_VENDOR_DIR / name
            mock_download_to_local.assert_any_call(url, out_path)


