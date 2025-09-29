from django.test import TestCase
from django.core.management import call_command
from django.conf import settings
from unittest.mock import patch, MagicMock
import os
from hypothesis.extra.django import TestCase as HypothesisTestCase
from hypothesis import given, strategies as st

class VendorPullTest(TestCase):
    @patch('helpers.download_to_local')
    def test_vendor_pull_command(self, mock_download_to_local):
        mock_download_to_local.return_value = True
        call_command('vendor_pull')
        self.assertEqual(mock_download_to_local.call_count, 4)
        for name, url in settings.VENDOR_STATICFILES.items():
            out_path = settings.STATICFILES_VENDOR_DIR / name
            mock_download_to_local.assert_any_call(url, out_path)

class CommandoHypothesisTest(HypothesisTestCase):
    @given(vendor_files=st.dictionaries(st.text(min_size=1), st.text(min_size=1)))
    @patch('helpers.download_to_local')
    def test_vendor_pull_command_hypothesis(self, mock_download_to_local, vendor_files):
        """
        Tests the vendor_pull command with a variety of file dictionaries.
        """
        mock_download_to_local.return_value = True
        if not vendor_files:
            return
        with self.settings(VENDOR_STATICFILES=vendor_files):
            call_command('vendor_pull')
            self.assertEqual(mock_download_to_local.call_count, len(vendor_files))
            for name, url in vendor_files.items():
                out_path = settings.STATICFILES_VENDOR_DIR / name
                mock_download_to_local.assert_any_call(url, out_path)


