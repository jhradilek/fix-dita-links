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

import re
from lxml import etree

def prune_ids(xml: etree._ElementTree) -> bool:
    updated = False

    adoc_attribute = re.compile(r'[_-]?\{([0-9A-Za-z_][0-9A-Za-z_-]*|set:.+?|counter2?:.+?)\}')
    valid_id       = re.compile(r'^[A-Za-z_:][A-Za-z0-9_:.-]+$')

    for e in xml.iter():
        if not e.attrib.has_key('id'):
            continue

        xml_id = str(e.attrib['id'])

        if valid_id.match(xml_id):
            continue

        e.attrib['id'] = adoc_attribute.sub('', xml_id)
        updated = True

    return updated

def prune_includes(xml: etree._ElementTree) -> bool:
    updated = False

    for e in xml.iter():
        if e.tag != 'xref':
            continue
        if not e.attrib.has_key('href'):
            continue
        if not str(e.attrib['href']).endswith('.adoc'):
            continue

        parent = e.getparent()

        if parent is None:
            continue

        parent.remove(e)
        updated = True

        if len(parent) != 0:
            continue

        grandparent = parent.getparent()
        if grandparent is None:
            continue

        grandparent.remove(parent)

    return updated

def update_image_paths(xml: etree._ElementTree, images_dir: str) -> bool:
    if images_dir == '':
        return False

    if not images_dir.endswith('/'):
        images_dir = images_dir + '/'

    updated = False

    for e in xml.iter():
        if e.tag != 'image':
            continue
        if not e.attrib.has_key('href'):
            continue

        e.attrib['href'] = images_dir + str(e.attrib['href'])
        updated = True

    return updated
