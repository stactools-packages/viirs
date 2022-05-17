import unittest

import stactools.viirs


class TestModule(unittest.TestCase):
    def test_version(self) -> None:
        self.assertIsNotNone(stactools.viirs.__version__)
