import unittest
import contextlib
import sys
from errno import ENOENT, ENOTDIR
from io import StringIO
from src.dita.cleanup import cli
from src.dita.cleanup import NAME, VERSION

class TestDitaCleanupCli(unittest.TestCase):
    def test_invalid_option(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stderr(StringIO()) as err:
            cli.parse_args(['--invalid-option'])

        self.assertEqual(cm.exception.code, ENOENT)
        self.assertRegex(err.getvalue(), rf'^usage: {NAME}')

    def test_missing_argument(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stderr(StringIO()) as err:
            cli.parse_args([])

        self.assertEqual(cm.exception.code, ENOENT)
        self.assertRegex(err.getvalue(), rf'^usage: {NAME}')

    def test_single_argument(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(len(args.files), 1)
        self.assertEqual(args.files[0], 'test_file')

    def test_multiple_arguments(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['test_file_one', 'test_file_two'])

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(len(args.files), 2)
        self.assertEqual(args.files[0], 'test_file_one')
        self.assertEqual(args.files[1], 'test_file_two')

    def test_argument_stdin(self):
        args = cli.parse_args(['-'])
        self.assertEqual(args.files[0], sys.stdin)
        self.assertEqual(args.output, sys.stdout)

    def test_opt_help_short(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stdout(StringIO()) as out:
            cli.parse_args(['-h'])

        self.assertEqual(cm.exception.code, 0)
        self.assertRegex(out.getvalue(), rf'^usage: {NAME}')

    def test_opt_help_long(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stdout(StringIO()) as out:
            cli.parse_args(['--help'])

        self.assertEqual(cm.exception.code, 0)
        self.assertRegex(out.getvalue(), rf'^usage: {NAME}')

    def test_opt_version_short(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stdout(StringIO()) as out:
            cli.parse_args(['-v'])

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(out.getvalue().rstrip(), f'{NAME} {VERSION}')

    def test_opt_version_long(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stdout(StringIO()) as out:
            cli.parse_args(['--version'])

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(out.getvalue().rstrip(), f'{NAME} {VERSION}')

    def test_opt_output_short(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['-o', 'output_file', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(args.output, 'output_file')

    def test_opt_output_long(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['--output', 'output_file', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(args.output, 'output_file')

    def test_opt_output_missing_argument(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stderr(StringIO()) as out:
            cli.parse_args(['--output'])

        self.assertEqual(cm.exception.code, ENOENT)
        self.assertRegex(out.getvalue(), rf'^usage: {NAME}')

    def test_opt_output_stdout(self):
        args = cli.parse_args(['--output', '-', 'test_file'])
        self.assertEqual(args.output, sys.stdout)

    def test_opt_conref_short(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['-C', 'conref_target', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(args.conref_target, 'conref_target')

    def test_opt_conref_long(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['--conref-target', 'conref_target', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(args.conref_target, 'conref_target')

    def test_opt_conref_missing_argument(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stderr(StringIO()) as out:
            cli.parse_args(['--conref-target'])

        self.assertEqual(cm.exception.code, ENOENT)
        self.assertRegex(out.getvalue(), rf'^usage: {NAME}')

    def test_opt_images_short(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['-D', '.', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(args.images_dir, '.')

    def test_opt_images_long(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['--images-dir', '.', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(args.images_dir, '.')

    def test_opt_images_missing_argument(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stderr(StringIO()) as out:
            cli.parse_args(['--images-dir', 'test_file'])

        self.assertEqual(cm.exception.code, ENOENT)
        self.assertRegex(out.getvalue(), rf'^usage: {NAME}')

    def test_opt_images_invalid_argument(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stderr(StringIO()) as out:
            cli.parse_args(['--images-dir', 'file.dita', 'test_file'])

        self.assertEqual(cm.exception.code, ENOTDIR)
        self.assertRegex(out.getvalue(), rf"Not a directory: 'file.dita'")

    def test_opt_xref_short(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['-X', '.', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(args.xref_dir, '.')

    def test_opt_xref_long(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['--xref-dir', '.', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertEqual(args.xref_dir, '.')

    def test_opt_xref_missing_argument(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stderr(StringIO()) as out:
            cli.parse_args(['--xref-dir', 'test_file'])

        self.assertEqual(cm.exception.code, ENOENT)
        self.assertRegex(out.getvalue(), rf'^usage: {NAME}')

    def test_opt_xref_invalid_argument(self):
        with self.assertRaises(SystemExit) as cm,\
             contextlib.redirect_stderr(StringIO()) as out:
            cli.parse_args(['--xref-dir', 'file.dita', 'test_file'])

        self.assertEqual(cm.exception.code, ENOTDIR)
        self.assertRegex(out.getvalue(), rf"Not a directory: 'file.dita'")

    def test_opt_prune_ids_short(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['-i', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertTrue(args.prune_ids)

    def test_opt_prune_ids_long(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['--prune-ids', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertTrue(args.prune_ids)

    def test_opt_prune_includes_short(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['-I', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertTrue(args.prune_includes)

    def test_opt_prune_includes_long(self):
        with contextlib.redirect_stdout(StringIO()) as out:
            args = cli.parse_args(['--prune-includes', 'test_file'])

        self.assertEqual(out.getvalue(), '')
        self.assertTrue(args.prune_includes)
