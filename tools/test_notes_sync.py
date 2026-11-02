import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('sync', Path(__file__).with_name('notes-sync.py'))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        sync.ROOT = Path(self.temp.name)
        sync.STAGE = sync.ROOT / '.notes-staging'
        self.note = dict(id='sample', text='<script>test</script>', attachments=0,
                        created='2026-11-02T00:00:00Z', modified='2026-11-02T00:00:00Z')

    def test_update_and_backup(self):
        sync.preview([self.note]); sync.apply()
        self.note['text'] = 'updated'
        sync.preview([self.note]); sync.apply()
        files = list((sync.ROOT / 'notes').glob('*.md'))
        self.assertEqual(len(files), 1)
        self.assertIn('updated', files[0].read_text())
        self.assertTrue(list(sync.STAGE.glob('backup-*/*.md')))

    def test_tamper(self):
        sync.preview([self.note])
        next(sync.STAGE.glob('*.md')).write_text('tampered')
        with self.assertRaises(ValueError): sync.apply()

    def test_attachment_and_escaping(self):
        self.assertIn('&lt;script&gt;', sync.render(self.note))
        self.note['attachments'] = 1
        with self.assertRaises(ValueError): sync.preview([self.note])
        self.assertFalse(sync.STAGE.exists())

    def test_manifest_symlink(self):
        sync.STAGE.mkdir()
        outside = sync.ROOT / 'untouched'
        outside.write_text('original')
        (sync.STAGE / 'manifest.json').symlink_to(outside)
        with self.assertRaises(ValueError): sync.preview([self.note])
        self.assertEqual(outside.read_text(), 'original')

    def test_parent_symlink(self):
        outside = sync.ROOT / 'other'; outside.mkdir()
        (sync.ROOT / 'notes').symlink_to(outside)
        sync.preview([self.note])
        with self.assertRaises(ValueError): sync.apply()
        self.assertEqual(list(outside.iterdir()), [])

if __name__ == '__main__': unittest.main()
