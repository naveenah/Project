import logging
from django.test import TestCase
from django.core.management import call_command
from django.conf import settings
from unittest.mock import patch, MagicMock
import os
from hypothesis.extra.django import TestCase as HypothesisTestCase
from hypothesis import given, strategies as st

logger = logging.getLogger(__name__)
logger.info("commando tests loaded")

class VendorPullTest(TestCase):
    @patch('commando.management.commands.vendor_pull.helpers.download_to_local')
    def test_vendor_pull_command(self, mock_download_to_local):
        mock_download_to_local.return_value = True
        vendor_files = {
            "saas-theme.min.css" : "https://raw.githubusercontent.com/codingforentrepreneurs/SaaS-Foundations/260663e36ab9595361e6e31964ac879d116ae599/src/staticfiles/theme/saas-theme.min.css",
            "flowbite.min.css" : "https://cdn.jsdelivr.net/npm/flowbite@2.5.2/dist/flowbite.min.css",
            "flowbite.min.js" : "https://cdn.jsdelivr.net/npm/flowbite@2.5.2/dist/flowbite.min.js",
            "flowbite.min.js.map" : "https://cdn.jsdelivr.net/npm/flowbite@2.5.2/dist/flowbite.min.js.map",
        }
        with self.settings(VENDOR_STATICFILES=vendor_files):
            call_command('vendor_pull')
            self.assertEqual(mock_download_to_local.call_count, 4)
            for name, url in vendor_files.items():
                out_path = settings.STATICFILES_VENDOR_DIR / name
                mock_download_to_local.assert_any_call(url, out_path)

class CommandoHypothesisTest(HypothesisTestCase):
    @given(vendor_files=st.dictionaries(st.text(min_size=1), st.text(min_size=1)))
    @patch('commando.management.commands.vendor_pull.helpers.download_to_local')
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


