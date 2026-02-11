# Copyright (C) 2025, 2026 Jaromir Hradilek

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
from pathlib import Path
from typing import Final
from .out import warn

__all__ = [
    'list_ids', 'prune_ids', 'prune_xrefs', 'replace_attributes',
    'update_image_paths', 'update_xref_targets'
]

RE_ID_ATTRIBUTE:   Final = re.compile(r'[_-]?\{([0-9A-Za-z_][0-9A-Za-z_-]*|set:.+?|counter2?:.+?)\}')
RE_TEXT_ATTRIBUTE: Final = re.compile(r'(?<!\$)\{([0-9A-Za-z_][0-9A-Za-z_-]*)\}')
RE_TEXT_COUNTER:   Final = re.compile(r'(?<!\$)\{(set:.+?|counter2?:.+?)\}')

def list_ids(xml: etree._ElementTree) -> list[str]:
    result: list[str] = []
    root   = xml.getroot()

    if root.tag not in ['concept', 'reference', 'task', 'topic']:
        return result

    if root.attrib.has_key('id'):
        result.append(str(root.attrib['id']))
    else:
        result.append('')

    for e in xml.iter():
        if e == root:
            continue
        if not e.attrib:
            continue
        if not e.attrib.has_key('id'):
            continue
        if str(e.attrib['id']).startswith('_'):
            continue

        result.append(str(e.attrib['id']))

    return result

def prune_ids(xml: etree._ElementTree) -> bool:
    updated = False

    valid_id       = re.compile(r'^[A-Za-z_:][A-Za-z0-9_:.-]+$')

    for e in xml.iter():
        if not e.attrib:
            continue
        if not e.attrib.has_key('id'):
            continue

        xml_id = str(e.attrib['id'])

        if valid_id.match(xml_id):
            continue

        e.attrib['id'] = RE_ID_ATTRIBUTE.sub('', xml_id)
        updated = True

    return updated

def prune_xrefs(xml: etree._ElementTree) -> bool:
    updated = False

    for e in xml.iter():
        if e.tag != 'xref':
            continue
        if not e.attrib:
            continue
        if not e.attrib.has_key('href'):
            continue

        xml_href = str(e.attrib['href'])

        if not RE_ID_ATTRIBUTE.search(xml_href):
            continue

        e.attrib['href'] = RE_ID_ATTRIBUTE.sub('', xml_href)
        updated = True

    return updated

def rebuild_text(text: str, conref_prefix: str) -> tuple[str, list[etree._Element]]:
    rest = text
    start = ''
    nodes: list[etree._Element] = []

    while match := RE_TEXT_ATTRIBUTE.findall(rest):
        tail, rest = rest.split('{' + match[0] + '}', 1)

        if not nodes:
            start = tail
        else:
            nodes[-1].tail = tail

        node = etree.Element('ph')
        node.set('conref', conref_prefix + match[0].lower())
        nodes.append(node)

    if nodes:
        nodes[-1].tail = rest

    return start, nodes

def replace_attributes(xml: etree._ElementTree, conref_prefix: str) -> bool:
    updated = False

    if not conref_prefix.endswith('/'):
        conref_prefix = conref_prefix + '/'

    for e in xml.iter():
        if e.text:
            text, nodes = rebuild_text(str(e.text), conref_prefix)

            if nodes:
                e.text = text

                index = 0
                for node in nodes:
                    e.insert(index, node)
                    index += 1

                updated = True

        if e.tail:
            text, nodes = rebuild_text(str(e.tail), conref_prefix)

            if nodes:
                e.tail = text

                parent = e.getparent()

                if parent is None:
                    continue

                index = parent.index(e)
                for node in nodes:
                    index += 1
                    parent.insert(index, node)

                updated = True

    return updated

def report_problems(xml:etree._ElementTree, file_path: Path) -> None:
    attribute_references = set()

    for e in xml.iter():
        if matches := RE_TEXT_ATTRIBUTE.findall(str(e.text) + str(e.tail)):
            attribute_references.update(set(matches))

        if matches := RE_TEXT_COUNTER.findall(str(e.text) + str(e.tail)):
            attribute_references.update(set(matches))

        if e.attrib.has_key('id') and (matches := RE_ID_ATTRIBUTE.findall(str(e.attrib['id']))):
            attribute_references.update(set(matches))

        if e.attrib.has_key('href') and (matches := RE_ID_ATTRIBUTE.findall(str(e.attrib['href']))):
            attribute_references.update(set(matches))

    for attribute in iter(attribute_references):
        warn(str(file_path) + ": Unresolved attribute reference: " + attribute)

def update_image_paths(xml: etree._ElementTree, images_dir: Path, file_path: Path) -> bool:
    updated = False

    for e in xml.iter():
        if e.tag != 'image':
            continue
        if not e.attrib:
            continue
        if not e.attrib.has_key('href'):
            continue

        f = file_path.resolve()
        i = images_dir.resolve()

        if i == f.parent:
            continue

        target = str(i.relative_to(f.parent, walk_up=True))
        href   = str(e.attrib['href'])

        if href.startswith(target + '/'):
            warn(str(file_path) + ": Already in target path: " + href)
            continue

        e.attrib['href'] = target + '/' + href

        updated = True

    return updated

def update_xref_targets(xml: etree._ElementTree, xml_ids: dict[str, tuple[str, Path]], file_path: Path) -> bool:
    updated = False

    for e in xml.iter():
        if e.tag not in ['xref', 'link']:
            continue
        if not e.attrib:
            continue
        if e.attrib.has_key('scope') and e.attrib['scope'] == 'external':
            continue
        if not e.attrib.has_key('href'):
            continue
        if not str(e.attrib['href']).startswith('#'):
            continue

        href  = str(e.attrib['href']).lstrip('#')
        match = [i for i in xml_ids.keys() if href == i or href.startswith(i + '_')]

        if not match:
            warn(str(file_path) + ": No matching ID: " + href)
            continue
        if len(match) > 1:
            warn(str(file_path) + ": Multiple matching IDs: " + href)
            continue

        target_id = match[0]
        topic_id, target_file = xml_ids[target_id]

        if target_file.parent == file_path.parent:
            target = str(target_file.name)
        else:
            f = file_path.resolve()
            t = target_file.resolve()
            target = str(t.parent.relative_to(f.parent, walk_up=True) / t.name)

        if topic_id == target_id:
            e.attrib['href'] = target + '#' + topic_id
        else:
            e.attrib['href'] = target + '#' + topic_id + '/' + target_id

        updated = True

    return updated
