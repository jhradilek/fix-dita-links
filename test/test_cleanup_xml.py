import unittest
import contextlib
from io import StringIO
from lxml import etree
from pathlib import Path
from src.dita.cleanup import NAME
from src.dita.cleanup.xml import list_ids, prune_ids, prune_includes, \
    replace_attributes, update_image_paths, update_xref_targets

class TestDitaCleanupXML(unittest.TestCase):
    def test_list_ids(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <note id="note-id">A note</note>
                <section id="section-id">
                    <title>Section title</title>
                    <p><ph id="phrase-id">A phrase</ph></p>
                </section>
            </conbody>
        </concept>
        '''))

        ids = list_ids(xml)

        self.assertEqual(len(ids), 4)
        self.assertEqual(ids[0], 'topic-id')
        self.assertTrue('note-id' in ids)
        self.assertTrue('section-id' in ids)
        self.assertTrue('phrase-id' in ids)

    def test_list_ids_no_topic_id(self):
        xml = etree.parse(StringIO('''\
        <concept>
            <title>Concept title</title>
            <conbody>
                <note id="note-id">A note</note>
                <section id="section-id">
                    <title>Section title</title>
                    <p><ph id="phrase-id">A phrase</ph></p>
                </section>
            </conbody>
        </concept>
        '''))

        ids = list_ids(xml)

        self.assertEqual(len(ids), 4)
        self.assertEqual(ids[0], '')
        self.assertTrue('note-id' in ids)
        self.assertTrue('section-id' in ids)
        self.assertTrue('phrase-id' in ids)

    def test_list_ids_generated_id(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <note id="note-id">A note</note>
                <section id="_section-id">
                    <title>Section title</title>
                    <p><ph id="phrase-id">A phrase</ph></p>
                </section>
            </conbody>
        </concept>
        '''))

        ids = list_ids(xml)

        self.assertEqual(len(ids), 3)
        self.assertEqual(ids[0], 'topic-id')
        self.assertTrue('note-id' in ids)
        self.assertTrue('phrase-id' in ids)
        self.assertFalse('_section-id' in ids)

    def test_list_ids_unsupported_topic(self):
        xml = etree.parse(StringIO('''\
        <map id="map-id">
            <title>Map title</title>
            <topicref href="topic.dita" type="topic" />
        </map>
        '''))

        ids = list_ids(xml)

        self.assertEqual(len(ids), 0)

    def test_prune_ids(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id_{context}">
            <title>Concept title</title>
            <conbody>
                <section id="section-id_{context}">
                    <title>Section title</title>
                    <p><ph id="phrase-id-{counter:seq1:1}">A phrase</ph></p>
                </section>
            </conbody>
        </concept>
        '''))

        updated = prune_ids(xml)

        self.assertTrue(updated)
        self.assertTrue(xml.xpath('boolean(/concept[@id="topic-id"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/section[@id="section-id"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/section/p/ph[@id="phrase-id"])'))

    def test_prune_ids_no_attributes(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <section id="section-id">
                    <title>Section title</title>
                    <p><ph id="phrase-id">A phrase</ph></p>
                </section>
            </conbody>
        </concept>
        '''))

        updated = prune_ids(xml)

        self.assertFalse(updated)

    def test_prune_includes(self):
        xml = etree.parse(StringIO('''\
        <concept id="assembly-id">
            <title>Assembly title</title>
            <conbody>
                <p>
                    <xref href="https://example.com" scope="external">An external link</xref>
                    <xref href="a-topic.dita">A topic</xref>
                </p>
                <p>
                    <xref href="a-module.adoc" scope="external">a-module.adoc</xref>
                    <xref href="another-module.adoc" scope="external">another-module.adoc</xref>
                </p>
            </conbody>
        </concept>
        '''))

        updated = prune_includes(xml)

        self.assertTrue(updated)
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1]/xref[1][@href="https://example.com"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1]/xref[2][@href="a-topic.dita"])'))
        self.assertFalse(xml.xpath('boolean(/concept/conbody/p[2])'))
        self.assertFalse(xml.xpath('boolean(//xref[@href="a-module.adoc"])'))
        self.assertFalse(xml.xpath('boolean(//xref[@href="another-module.adoc"])'))

    def test_prune_includes_no_includes(self):
        xml = etree.parse(StringIO('''\
        <concept id="assembly-id">
            <title>Assembly title</title>
            <conbody>
                <p>
                    <xref href="https://example.com" scope="external">Example link</xref>
                    <xref href="a-topic.dita">A topic</xref>
                </p>
            </conbody>
        </concept>
        '''))

        updated = prune_includes(xml)

        self.assertFalse(updated)

    def test_replace_attributes(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p>first part {first-attribute} second part {second-attribute} third part <i>inline tag</i> fourth part {third-attribute} fifth part</p>
                <p><i>first inline tag</i> first part {first-attribute} second part {second-attribute} third part <i>second inline tag</i> fourth part {third-attribute} fifth part</p>
            </conbody>
        </concept>
        '''))

        updated = replace_attributes(xml, 'topic.dita#topic-id')

        self.assertTrue(updated)
        self.assertEqual(str(xml.xpath('/concept/conbody/p[1]/text()[1]')[0]).strip(), 'first part')
        self.assertEqual(str(xml.xpath('/concept/conbody/p[1]/text()[2]')[0]).strip(), 'second part')
        self.assertEqual(str(xml.xpath('/concept/conbody/p[1]/text()[3]')[0]).strip(), 'third part')
        self.assertEqual(str(xml.xpath('/concept/conbody/p[1]/text()[4]')[0]).strip(), 'fourth part')
        self.assertEqual(str(xml.xpath('/concept/conbody/p[1]/text()[5]')[0]).strip(), 'fifth part')
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1]/i[text()="inline tag"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1]/ph[1][@conref="topic.dita#topic-id/first-attribute"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1]/ph[2][@conref="topic.dita#topic-id/second-attribute"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1]/ph[3][@conref="topic.dita#topic-id/third-attribute"])'))
        self.assertEqual(str(xml.xpath('/concept/conbody/p[2]/text()[1]')[0]).strip(), 'first part')
        self.assertEqual(str(xml.xpath('/concept/conbody/p[2]/text()[2]')[0]).strip(), 'second part')
        self.assertEqual(str(xml.xpath('/concept/conbody/p[2]/text()[3]')[0]).strip(), 'third part')
        self.assertEqual(str(xml.xpath('/concept/conbody/p[2]/text()[4]')[0]).strip(), 'fourth part')
        self.assertEqual(str(xml.xpath('/concept/conbody/p[2]/text()[5]')[0]).strip(), 'fifth part')
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[2]/i[1][text()="first inline tag"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[2]/i[2][text()="second inline tag"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[2]/ph[1][@conref="topic.dita#topic-id/first-attribute"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[2]/ph[2][@conref="topic.dita#topic-id/second-attribute"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[2]/ph[3][@conref="topic.dita#topic-id/third-attribute"])'))

    def test_replace_attributes_with_slash(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p>first part {first-attribute} second part</p>
            </conbody>
        </concept>
        '''))

        updated = replace_attributes(xml, 'topic.dita#topic-id/')

        self.assertTrue(updated)
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p/ph[@conref="topic.dita#topic-id/first-attribute"])'))

    def test_replace_attributes_no_attributes(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p>first part second part</p>
            </conbody>
        </concept>
        '''))

        updated = replace_attributes(xml, 'topic.dita#topic-id')

        self.assertFalse(updated)
        self.assertFalse(xml.xpath('boolean(/concept/conbody/p/ph)'))

    def test_update_image_paths(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p>A paragraph with an <image href="inline-image.png" placement="inline"><alt>inline image</alt></image>.</p>
                <fig>
                    <title>Figure title</title>
                    <image href="separate-image.png" placement="break">
                        <alt>A separate image</alt>
                    </image>
                </fig>
            </conbody>
        </concept>
        '''))

        updated = update_image_paths(xml, Path('images'), Path('topic.dita'))

        self.assertTrue(updated)
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p/image[@href="images/inline-image.png"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/fig/image[@href="images/separate-image.png"])'))

    def test_update_image_paths_with_slash(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p>A paragraph with an <image href="inline-image.png" placement="inline"><alt>inline image</alt></image>.</p>
                <fig>
                    <title>Figure title</title>
                    <image href="separate-image.png" placement="break">
                        <alt>A separate image</alt>
                    </image>
                </fig>
            </conbody>
        </concept>
        '''))

        updated = update_image_paths(xml, Path('images/'), Path('topic.dita'))

        self.assertTrue(updated)
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p/image[@href="images/inline-image.png"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/fig/image[@href="images/separate-image.png"])'))

    def test_update_image_paths_no_images(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p>A paragraph without an inline image.</p>
            </conbody>
        </concept>
        '''))

        updated = update_image_paths(xml, Path('images'), Path('topic.dita'))

        self.assertFalse(updated)

    def test_update_image_paths_relative_paths(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p>A paragraph with an <image href="inline-image.png" placement="inline"><alt>inline image</alt></image>.</p>
                <fig>
                    <title>Figure title</title>
                    <image href="separate-image.png" placement="break">
                        <alt>A separate image</alt>
                    </image>
                </fig>
            </conbody>
        </concept>
        '''))

        updated = update_image_paths(xml, Path('first/images'), Path('first/second/topic.dita'))

        self.assertTrue(updated)
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p/image[@href="../images/inline-image.png"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/fig/image[@href="../images/separate-image.png"])'))

    def test_update_image_paths_same_paths(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p>A paragraph with an <image href="inline-image.png" placement="inline"><alt>inline image</alt></image>.</p>
                <fig>
                    <title>Figure title</title>
                    <image href="separate-image.png" placement="break">
                        <alt>A separate image</alt>
                    </image>
                </fig>
            </conbody>
        </concept>
        '''))

        updated = update_image_paths(xml, Path('first'), Path('first/topic.dita'))

        self.assertFalse(updated)
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p/image[@href="inline-image.png"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/fig/image[@href="separate-image.png"])'))

    def test_update_xref_targets(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p><xref href="#first-id">First reference</xref></p>
                <p><xref href="#second-id_assembly-context">Second reference</xref></p>
                <p><xref href="#third-id_assembly-context">Third reference</xref></p>
            </conbody>
        </concept>
        '''))

        ids = {
            'first-id': ('first-topic-id', Path('first-topic.dita')),
            'second-id': ('second-topic-id', Path('second-topic.dita')),
            'third-id': ('third-id', Path('third-topic.dita'))
        }

        with contextlib.redirect_stderr(StringIO()) as err:
            updated = update_xref_targets(xml, ids, Path('topic.dita'))

        self.assertTrue(updated)
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1]/xref[@href="first-topic.dita#first-topic-id/first-id"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[2]/xref[@href="second-topic.dita#second-topic-id/second-id"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[3]/xref[@href="third-topic.dita#third-id"])'))
        self.assertEqual(err.getvalue(), '')

    def test_update_xref_targets_no_matches(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p><xref href="#first-id">First reference</xref></p>
                <p><xref href="#second-id_assembly-context">Second reference</xref></p>
            </conbody>
        </concept>
        '''))

        ids = {
            'first-id': ('first-topic-id', Path('first-topic.dita')),
        }

        with contextlib.redirect_stderr(StringIO()) as err:
            updated = update_xref_targets(xml, ids, Path('topic.dita'))

        self.assertTrue(updated)
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1]/xref[@href="first-topic.dita#first-topic-id/first-id"])'))
        self.assertRegex(err.getvalue(), rf'^{NAME}: topic.dita: No matching ID: ')

    def test_update_xref_targets_multiple_matches(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p><xref href="#first-id">First reference</xref></p>
                <p><xref href="#second-id_assembly-context">Second reference</xref></p>
            </conbody>
        </concept>
        '''))

        ids = {
            'first-id': ('first-topic-id', Path('first-topic.dita')),
            'second-id': ('second-topic-id', Path('second-topic.dita')),
            'second-id_assembly-context': ('second-id_assembly_context', Path('second-topic.dita')),
        }

        with contextlib.redirect_stderr(StringIO()) as err:
            updated = update_xref_targets(xml, ids, Path('topic.dita'))

        self.assertTrue(updated)
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1]/xref[@href="first-topic.dita#first-topic-id/first-id"])'))
        self.assertRegex(err.getvalue(), rf'^{NAME}: topic.dita: Multiple matching IDs: ')

    def test_update_xref_targets_no_xrefs(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p>A paragraph without a cross reference.</p>
            </conbody>
        </concept>
        '''))

        ids = {}

        with contextlib.redirect_stderr(StringIO()) as err:
            updated = update_xref_targets(xml, ids, Path('topic.dita'))

        self.assertFalse(updated)
        self.assertEqual(err.getvalue(), '')

    def test_update_xref_targets_relative_paths(self):
        xml = etree.parse(StringIO('''\
        <concept id="topic-id">
            <title>Concept title</title>
            <conbody>
                <p><xref href="#first-id">First reference</xref></p>
                <p><xref href="#second-id">Second reference</xref></p>
                <p><xref href="#third-id">Third reference</xref></p>
                <p><xref href="#fourth-id">Fourth reference</xref></p>
            </conbody>
        </concept>
        '''))

        ids = {
            'first-id': ('first-topic-id', Path('one/first-topic.dita')),
            'second-id': ('second-topic-id', Path('two/second-topic.dita')),
            'third-id': ('third-id', Path('one/three/third-topic.dita')),
            'fourth-id': ('fourth-id', Path('fourth-topic.dita'))
        }

        with contextlib.redirect_stderr(StringIO()) as err:
            updated = update_xref_targets(xml, ids, Path('one/topic.dita'))

        self.assertTrue(updated)
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[1]/xref[@href="first-topic.dita#first-topic-id/first-id"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[2]/xref[@href="../two/second-topic.dita#second-topic-id/second-id"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[3]/xref[@href="three/third-topic.dita#third-id"])'))
        self.assertTrue(xml.xpath('boolean(/concept/conbody/p[4]/xref[@href="../fourth-topic.dita#fourth-id"])'))
        self.assertEqual(err.getvalue(), '')
