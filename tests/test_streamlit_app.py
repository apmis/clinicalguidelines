"""Tests deployment-safe URL handling for the Streamlit client."""

import unittest

from streamlit_app import normalize_api_url


class StreamlitAppTests(unittest.TestCase):
    def test_keeps_explicit_http_url(self):
        self.assertEqual(
            normalize_api_url("http://127.0.0.1:8011/"),
            "http://127.0.0.1:8011",
        )

    def test_adds_http_scheme_to_render_private_host(self):
        self.assertEqual(
            normalize_api_url("healthstack-guidelines-api:10000"),
            "http://healthstack-guidelines-api:10000",
        )

    def test_trims_blank_url(self):
        self.assertEqual(normalize_api_url("  "), "")


if __name__ == "__main__":
    unittest.main()
