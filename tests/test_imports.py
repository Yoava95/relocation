import unittest

class ImportTests(unittest.TestCase):
    def test_import_job_search(self):
        import job_search  # noqa: F401
        self.assertTrue(hasattr(job_search, "HEADERS"))

    def test_import_job_search_local(self):
        import job_search_local  # noqa: F401
        self.assertTrue(hasattr(job_search_local, "HEADERS"))

if __name__ == "__main__":
    unittest.main()
