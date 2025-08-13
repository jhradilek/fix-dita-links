import unittest
import contextlib
import sys
from errno import EINVAL, EPERM
from io import StringIO
from src.dita.cleanup import out
from src.dita.cleanup import NAME

class TestDitaCleanupOut(unittest.TestCase):
    def test_warn(self):
        with contextlib.redirect_stderr(StringIO()) as err:
            out.warn('test message')

        self.assertEqual(err.getvalue().strip(), f'{NAME}: test message')

    def test_exit_with_error(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stderr(StringIO()) as err:
            out.exit_with_error('test message')

        self.assertEqual(cm.exception.code, EPERM)
        self.assertEqual(err.getvalue().strip(), f'{NAME}: test message')

    def test_exit_with_error_custom_code(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stderr(StringIO()) as err:
            out.exit_with_error('test message', EINVAL)

        self.assertEqual(cm.exception.code, EINVAL)
        self.assertEqual(err.getvalue().strip(), f'{NAME}: test message')
