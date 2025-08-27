# Copyright (C) 2025 Jaromir Hradilek

# MIT License
#
# Permission  is hereby granted,  free of charge,  to any person  obtaining
# a copy of  this software  and associated documentation files  (the "Soft-
# ware"),  to deal in the Software  without restriction,  including without
# limitation the rights to use,  copy, modify, merge,  publish, distribute,
# sublicense, and/or sell copies of the Software,  and to permit persons to
# whom the Software is furnished to do so,  subject to the following condi-
# tions:
#
# The above copyright notice  and this permission notice  shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS",  WITHOUT WARRANTY OF ANY KIND,  EXPRESS
# OR IMPLIED,  INCLUDING BUT NOT LIMITED TO  THE WARRANTIES OF MERCHANTABI-
# LITY,  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT
# SHALL THE AUTHORS OR COPYRIGHT HOLDERS  BE LIABLE FOR ANY CLAIM,  DAMAGES
# OR OTHER LIABILITY,  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM,  OUT OF OR IN CONNECTION WITH  THE SOFTWARE  OR  THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import argparse
import sys

from errno import EPERM, ENOTDIR
from lxml import etree
from pathlib import Path
from . import NAME, VERSION, DESCRIPTION
from .out import exit_with_error, warn
from .xml import replace_attributes, update_image_paths, prune_ids, \
                 prune_includes, list_ids, update_xref_targets

__all__ = [
    'run'
]

def list_files(directory: str) -> list[Path]:
    result: list[Path] = []
    for root, dirs, files in Path(directory).walk(top_down=True, on_error=print):
        for name in files:
            if name.endswith('.dita') or name.endswith('.xml'):
                result.append(Path(root, name))
    return result

def catalog_ids(directory: str) -> dict[str, tuple[str, Path]]:
    result: dict[str, tuple[str, Path]] = {}

    file_list = list_files(directory)

    for file_path in file_list:
        try:
            xml = etree.parse(file_path)
        except (etree.XMLSyntaxError, OSError) as message:
            warn(str(message))
            continue

        id_list  = list_ids(xml)
        topic_id = id_list[0]

        for xml_id in id_list:
            if xml_id in result:
                warn(str(file_path) + ": Duplicate ID: " + xml_id)
                continue

            result[xml_id] = (topic_id, file_path)

    return result

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=NAME,
        description=DESCRIPTION,
        add_help=False)

    parser._optionals.title = 'Options'
    parser._positionals.title = 'Arguments'

    parser.add_argument('-C', '--conref-target',
        default=False,
        metavar='TARGET',
        help='replace attribute references with reusable content references')
    parser.add_argument('-D', '--images-dir',
        default=False,
        metavar='DIRECTORY',
        help='add a directory path to all image targets')
    parser.add_argument('-X', '--xref-dir',
        default=False,
        metavar='DIRECTORY',
        help='update all cross references based on the supplied files')
    parser.add_argument('-i', '--prune-ids',
        default=False,
        action='store_true',
        help='remove invalid content from element IDs')
    parser.add_argument('-I', '--prune-includes',
        default=False,
        action='store_true',
        help='remove unresolved include statements')

    out = parser.add_mutually_exclusive_group()
    out.add_argument('-o', '--output',
        default=False,
        metavar='FILE',
        help='write output to the selected file instead of overwriting the file')

    info = parser.add_mutually_exclusive_group()
    info.add_argument('-h', '--help',
        action='help',
        help='display this help and exit')
    info.add_argument('-v', '--version',
        action='version',
        version=f'{NAME} {VERSION}',
        help='display version information and exit')

    parser.add_argument('files', metavar='FILE',
        default='-',
        nargs='+',
        help='specify the DITA files to clean up')

    args = parser.parse_args(argv)

    if args.files[0] == '-':
        args.files = [sys.stdin]
        args.output = sys.stdout
    if args.output == '-':
        args.output = sys.stdout

    if args.xref_dir and not Path(args.xref_dir).is_dir():
        exit_with_error(f"Not a directory: '{args.xref_dir}'", ENOTDIR)
    if args.images_dir and not Path(args.images_dir).is_dir():
        exit_with_error(f"Not a directory: '{args.images_dir}'", ENOTDIR)

    return args

def process_files(args: argparse.Namespace) -> int:
    exit_code = 0

    for file_path in args.files:
        try:
            xml = etree.parse(file_path)
        except (etree.XMLSyntaxError, OSError) as message:
            warn(str(message))
            exit_code = EPERM
            continue

        updated = False

        if args.conref_target and replace_attributes(xml, args.conref_target.strip()):
            updated = True

        if args.images_dir and update_image_paths(xml, Path(args.images_dir), Path(file_path)):
            updated = True

        if args.prune_ids and prune_ids(xml):
            updated = True

        if args.prune_includes and prune_includes(xml):
            updated = True

        if args.output == sys.stdout:
            if not args.xref_dir:
                sys.stdout.write(etree.tostring(xml, encoding='unicode'))
            continue

        if args.output:
            file_path = args.output
        elif not updated:
            continue

        try:
            xml.write(file_path)
        except OSError as message:
            warn(str(message))
            exit_code = EPERM
            continue

    if not args.xref_dir:
        return exit_code

    xml_ids = catalog_ids(args.xref_dir)

    for file_path in args.files:
        try:
            xml = etree.parse(file_path)
        except (etree.XMLSyntaxError, OSError) as message:
            warn(str(message))
            exit_code = EPERM
            continue

        updated = update_xref_targets(xml, xml_ids, Path(file_path))

        if args.output == sys.stdout:
            sys.stdout.write(etree.tostring(xml, encoding='unicode'))
            continue

        if args.output:
            file_path = args.output
        elif not updated:
            continue

        try:
            xml.write(file_path)
        except OSError as message:
            warn(str(message))
            exit_code = EPERM
            continue

    return exit_code

def run(argv: list[str] | None = None) -> None:
    try:
        args = parse_args(argv)
        exit_code = process_files(args)
    except KeyboardInterrupt:
        sys.exit(130)

    sys.exit(exit_code)
