#!/usr/bin/env python3

# Copyright (C) 2025 Jaromir Hradilek

# MIT License
#
# Permission  is hereby granted,  free of charge,  to any person  obtaining
# a copy of  this software  and associated documentation files  (the 'Soft-
# ware'),  to deal in the Software  without restriction,  including without
# limitation the rights to use,  copy, modify, merge,  publish, distribute,
# sublicense, and/or sell copies of the Software,  and to permit persons to
# whom the Software is furnished to do so,  subject to the following condi-
# tions:
#
# The above copyright notice  and this permission notice  shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS',  WITHOUT WARRANTY OF ANY KIND,  EXPRESS
# OR IMPLIED,  INCLUDING BUT NOT LIMITED TO  THE WARRANTIES OF MERCHANTABI-
# LITY,  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT
# SHALL THE AUTHORS OR COPYRIGHT HOLDERS  BE LIABLE FOR ANY CLAIM,  DAMAGES
# OR OTHER LIABILITY,  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM,  OUT OF OR IN CONNECTION WITH  THE SOFTWARE  OR  THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import sys
from lxml import etree
from pathlib import Path

# Print a message to standard error output:
def warn(error_message):
    # Print the supplied message to standard error output:
    print(f'fix-dita-links: {error_message}', file=sys.stderr)

# Return a list of all paths to DITA files in the selected directory and
# all of its subdirectories:
def list_files(path='.'):
    # Create an empty list to collect the list of files in:
    result = []

    # Find all files recursively, do not follow symbolic links:
    for root, dirs, files in Path(path).walk(top_down=True, on_error=print):
        for name in files:
            # Record files with a supported extension:
            if name.endswith('.dita') or name.endswith('.xml'):
                result.append(Path(root, name))

    # Return the result:
    return result

# Return a list of all IDs defined in the supplied XML file with the topic
# ID being the first item:
def parse_file(path):
    # Create an empty list to collect the list of IDs in:
    result = []

    # Parse the XML file:
    try:
        xml = etree.parse(path)
    except etree.XMLSyntaxError as message:
        warn(str(message))

    # Get the root element:
    root = xml.getroot()

    # Issue a warning if the XML file is not a DITA topic:
    if root.tag not in ['concept', 'reference', 'task', 'topic']:
        warn(f'Not a DITA topic: {str(path)}')

    # Ensure that the first id on the list is the topic ID:
    if root.attrib.has_key('id'):
        result.append(root.attrib['id'])
    else:
        result.append('')
        warn(f'Topic ID not found: {str(path)}')

    # Compose the list of defined IDs:
    for e in xml.iter():
        # Skip the root element:
        if e == root:
            continue

        # Skip elements without the ID attribute:
        if not e.attrib.has_key('id'):
            continue

        # Skip automatically generated IDs:
        if not (id_value := e.attrib['id']).startswith('_'):
            result.append(id_value)

    # Return the result:
    return result

# Return a dictionary with all IDs defined in the supplied XML files:
def get_all_ids(path_list):
    # Create an empty dictionary to collect the IDs in:
    result = {}

    # Parse each file:
    for path in path_list:
        # Get the list of IDs from the file, as well as the topic ID:
        id_list  = parse_file(path)
        topic_id = id_list[0]

        # Add this information to the dictionary:
        for id in id_list:
            if id in result:
                warn(f'{str(path)}: Duplicate id: {id}')
            else:
                result[id] = {
                    'topic_id': topic_id,
                    'filepath': path
                }

    # Return the result:
    return result

# Return a list of IDs that partially match the supplied identifier:
def find_matches(identifier, id_list, suffix=''):
    # Create an empty list to collect the IDs in:
    result = []

    # Process each ID:
    for i in id_list:
        # Check if the ID matches the identifier:
        if identifier == i or identifier.startswith(i + suffix):
            result.append(i)

    # Return the result:
    return result

# Find all cross references that use and ID as the target and update them:
def update_xrefs(path_list, all_ids):
    # Process each file:
    for path in path_list:
        # Mark the file as not having any updates by default:
        updated = False

        # Parse the XML file:
        try:
            xml = etree.parse(path)
        except etree.XMLSyntaxError as message:
            warn(str(message))

        # Process each XML element:
        for e in xml.iter():
            # Ignore elements other than links and cross references:
            if e.tag not in ['xref', 'link']:
                continue

            # Ignore external links:
            if e.attrib.has_key('scope') and e.attrib['scope'] == 'external':
                continue

            # Ignore references other than to an ID:
            if not e.attrib['href'].startswith('#'):
                continue

            # Remove the hash sign from the beginning of the target ID:
            href = e.attrib['href'].lstrip('#')

            # Check if any matching IDs have been found:
            if not (matches := find_matches(href, all_ids, '_')):
                warn(f'ID not found: {href}')
                continue

            # Check if only one matching ID has been found:
            if len(matches) > 1:
                warn(f'Multiple matching IDs for {href}: {ids}')
                continue

            # Extract the information from the matching ID record:
            target_id = matches[0]
            entry = all_ids[target_id]
            topic_id  = entry['topic_id']
            filepath  = str(entry['filepath'])

            # Check if the target ID is a topic ID:
            if topic_id == target_id:
                target = f'{filepath}#{topic_id}'
            else:
                target = f'{filepath}#{topic_id}/{target_id}'

            # Update the target ID:
            e.attrib['href'] = target

            # Mark the file as updated:
            updated = True

        # Do not overwrite the file if no updates have been made:
        if not updated:
            continue

        # Save the updates to the file:
        try:
            xml.write(path)
        except Exception as message:
            warn(str(message))

if __name__ == '__main__':
    try:
        # Get a list of available DITA files:
        files = list_files('.')

        # Get a catalog of the defined IDs:
        ids   = get_all_ids(files)

        # Update cross references based on known IDs:
        update_xrefs(files, ids)
    except KeyboardInterrupt:
        sys.exit(130)
