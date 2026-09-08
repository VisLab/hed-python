"""Source order of get_library_data: GitHub first, then the cached copy, then the packaged copy.

The registry URL is pointed at a real local file (a file:// URL, which urllib serves like any other) so these
tests never reach the network, and each test uses its own cache folder. The module constant is set directly
in each test and restored in tearDown; no mock objects are involved.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from hed.schema import hed_cache
from hed.schema.hed_cache import get_library_data

PACKAGED_REGISTRY = os.path.join(hed_cache.INSTALLED_CACHE_LOCATION, "library_data", "library_data.json")

URL_REGISTRY = {
    "": {
        "id_range": [10000, 39999],
        "retired_ids": {"HED_0011644": {"label": "uV", "section": "units", "removed_in": "8.5.0"}},
    },
    "score": {"id_range": [40000, 59999]},
}

CACHED_REGISTRY = {
    "": {"id_range": [10000, 39999]},
    "score": {"id_range": [40000, 59999]},
    "onlycached": {"id_range": [1, 2]},
}


class TestGetLibraryData(unittest.TestCase):
    def setUp(self):
        get_library_data.cache_clear()
        self._saved_url = hed_cache.LIBRARY_DATA_URL
        self.tmp_dir = tempfile.mkdtemp()
        self.cache_folder = os.path.join(self.tmp_dir, "hed_cache")
        self.cache_registry = os.path.join(self.cache_folder, "library_data", "library_data.json")
        self.url_registry = os.path.join(self.tmp_dir, "remote", "library_data.json")
        self.url = Path(self.url_registry).as_uri()
        self.unreachable_url = Path(os.path.join(self.tmp_dir, "missing", "library_data.json")).as_uri()

    def tearDown(self):
        hed_cache.LIBRARY_DATA_URL = self._saved_url
        get_library_data.cache_clear()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    @staticmethod
    def _write_json(filename, data):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file)

    def _read_json(self, filename):
        with open(filename, encoding="utf-8") as file:
            return json.load(file)

    def test_url_is_authoritative(self):
        self._write_json(self.url_registry, URL_REGISTRY)
        self._write_json(self.cache_registry, CACHED_REGISTRY)
        hed_cache.LIBRARY_DATA_URL = self.url
        standard = get_library_data("", self.cache_folder)
        only_cached = get_library_data("onlycached", self.cache_folder)
        self.assertEqual(standard, URL_REGISTRY[""])
        self.assertIn("HED_0011644", standard["retired_ids"])
        # The stale cached copy was not consulted and has been replaced by the fetched registry.
        self.assertEqual(only_cached, {})
        self.assertEqual(self._read_json(self.cache_registry), URL_REGISTRY)
        # The conditional-request bookkeeping was recorded next to the version listings.
        url_cache = self._read_json(os.path.join(self.cache_folder, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME))
        self.assertEqual(url_cache[self.url]["body"], URL_REGISTRY)

    def test_falls_back_to_cached_copy(self):
        self._write_json(self.cache_registry, CACHED_REGISTRY)
        hed_cache.LIBRARY_DATA_URL = self.unreachable_url
        standard = get_library_data("", self.cache_folder)
        only_cached = get_library_data("onlycached", self.cache_folder)
        self.assertEqual(standard, CACHED_REGISTRY[""])
        self.assertEqual(only_cached, CACHED_REGISTRY["onlycached"])
        # The failed attempt is remembered, and the cached copy is left as it was.
        url_cache = self._read_json(os.path.join(self.cache_folder, hed_cache.AVAILABLE_VERSIONS_CACHE_FILENAME))
        self.assertIsNone(url_cache[self.unreachable_url]["body"])
        self.assertEqual(self._read_json(self.cache_registry), CACHED_REGISTRY)

    def test_falls_back_to_packaged_copy(self):
        hed_cache.LIBRARY_DATA_URL = self.unreachable_url
        standard = get_library_data("", self.cache_folder)
        packaged = self._read_json(PACKAGED_REGISTRY)
        self.assertEqual(standard, packaged[""])
        self.assertEqual(standard["id_range"], [10000, 39999])
        self.assertIn("HED_0011644", standard["retired_ids"])
        # The packaged copy was installed into the cache for next time.
        self.assertEqual(self._read_json(self.cache_registry), packaged)

    def test_url_body_must_be_an_object(self):
        self._write_json(self.url_registry, ["not", "a", "registry"])
        self._write_json(self.cache_registry, CACHED_REGISTRY)
        hed_cache.LIBRARY_DATA_URL = self.url
        standard = get_library_data("", self.cache_folder)
        self.assertEqual(standard, CACHED_REGISTRY[""])
        self.assertEqual(self._read_json(self.cache_registry), CACHED_REGISTRY)

    def test_unknown_library_is_empty(self):
        self._write_json(self.url_registry, URL_REGISTRY)
        hed_cache.LIBRARY_DATA_URL = self.url
        self.assertEqual(get_library_data("nosuchlib", self.cache_folder), {})

    def test_packaged_registry_lists_retired_ids(self):
        packaged = self._read_json(PACKAGED_REGISTRY)
        retired = packaged[""]["retired_ids"]
        self.assertEqual(retired["HED_0011644"]["label"], "uV")
        self.assertEqual(retired["HED_0011644"]["removed_in"], "8.5.0")
        self.assertIn("HED_0010308", retired)


if __name__ == "__main__":
    unittest.main()
