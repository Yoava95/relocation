import unittest

class ImportTests(unittest.TestCase):
    def test_import_job_search(self):
        import job_search  # noqa: F401
        self.assertTrue(hasattr(job_search, "HEADERS"))

if __name__ == "__main__":
    unittest.main()
