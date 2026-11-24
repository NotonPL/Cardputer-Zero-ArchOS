import json
from pathlib import Path
import tempfile
import unittest
from test_tools import load, ROOT

keymap = load('inspect_keymap')
audit = load('audit_sources')


def fixture(values='0x00000001 0x00010002'):
    return ('#address-cells = <1>; keypad,num-rows = <1>; keypad,num-columns = <2>;\n'
            + '\n'.join(f'{name} = <{values}>;' for name in
                        ('linux,keymap', 'linux,keymap1', 'linux,keymap2')))


class Keymaps(unittest.TestCase):
    def test_numeric_layers_and_dt_hash_property(self):
        result = keymap.inspect(fixture())
        self.assertEqual(result['mapped_positions'], 2)
        self.assertFalse(result['hardware_validated'])

    def test_comments_not_cells(self):
        self.assertEqual(keymap.inspect(fixture('0x00000001 /* 0xFFFFFFFF */'))['mapped_positions'], 1)

    def test_duplicate_position(self):
        with self.assertRaises(ValueError):
            keymap.inspect(fixture('0x00000001 0x00000002'))

    def test_outside_matrix(self):
        with self.assertRaises(ValueError):
            keymap.inspect(fixture('0x01000001'))

    def test_overflow(self):
        with self.assertRaises(ValueError):
            keymap.inspect(fixture('0x100000001'))

    def test_macros_rejected(self):
        with self.assertRaises(ValueError):
            keymap.inspect(fixture('KEY_ESC'))

    def test_conditionals_rejected(self):
        with self.assertRaises(ValueError):
            keymap.inspect('#if FOO\n' + fixture() + '\n#endif')

    def test_different_positions_rejected(self):
        with self.assertRaises(ValueError):
            keymap.inspect(fixture().replace('linux,keymap2 = <0x00000001 0x00010002>',
                                             'linux,keymap2 = <0x00000001>'))

    def test_committed_report_provenance(self):
        report = json.loads((ROOT/'hardware/keymap-v5.json').read_text())
        evidence = json.loads((ROOT/'hardware/vendor-evidence.json').read_text())
        source = next(p for p in evidence['probes'] if p['path'].endswith('/cardputerzero-v5-overlay.dts'))
        self.assertEqual(source['sha256'], report['source_sha256'])
        self.assertEqual(report['mapped_positions'], 46)
        for entries in report['maps'].values():
            self.assertEqual(len(entries), 46)


class Cache(unittest.TestCase):
    def test_explicit_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit.cache_source(root, 'modules/source.c', b'never executed')
            self.assertEqual((root/'modules/source.c').read_bytes(), b'never executed')

    def test_escaping_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            (root/'modules').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                audit.cache_source(root, 'modules/source.c', b'data')
            self.assertFalse((Path(outside)/'source.c').exists())

    def test_query_in_path_rejected(self):
        import tomllib
        config = tomllib.loads((ROOT/'hardware/vendor-sources.toml').read_text())
        config['probe'][0]['path'] = 'file?ref=main'
        with self.assertRaises(ValueError):
            audit.validate(config)
