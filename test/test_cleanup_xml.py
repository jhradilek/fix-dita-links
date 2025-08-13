import unittest
from io import StringIO
from lxml import etree
from src.dita.cleanup.xml import list_ids, prune_ids

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
