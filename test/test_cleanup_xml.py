import unittest
from io import StringIO
from lxml import etree
from src.dita.cleanup.xml import list_ids

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
