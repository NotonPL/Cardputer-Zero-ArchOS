import copy
import importlib.util
from pathlib import Path
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/f'tools/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = load('audit_sources')
diag = load('diagnose')


class Sources(unittest.TestCase):
    def setUp(self):
        self.config = tomllib.loads((ROOT/'hardware/sources.toml').read_text())

    def test_manifest(self):
        audit.validate(self.config)

    def test_mutable_revision_rejected(self):
        self.config['revision'] = 'main'
        with self.assertRaises(ValueError):
            audit.validate(self.config)

    def test_traversal_rejected(self):
        self.config['probe'][0]['path'] = '../etc/shadow'
        with self.assertRaises(ValueError):
            audit.validate(self.config)

    def test_duplicate_rejected(self):
        self.config['probe'].append(copy.deepcopy(self.config['probe'][0]))
        with self.assertRaises(ValueError):
            audit.validate(self.config)

    def test_identifier_case_insensitive(self):
        row = audit.inspect(dict(id='test', path='p', needle='bmm150'), b'BMM150')
        self.assertEqual(row['result'], 'found')
        self.assertEqual(len(row['sha256']), 64)

    def test_no_identifier_not_certified(self):
        self.assertEqual(audit.inspect(dict(id='test', path='p', needle='rx8130'),
                                       b'rx8581')['result'], 'identifier-not-found')


class Diagnostics(unittest.TestCase):
    def test_missing_interfaces_are_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = diag.inventory(Path(tmp))
        self.assertIsNone(result['model'])
        self.assertEqual(result['power'], {})
        self.assertEqual(result['devices']['i2c'], [])

    def test_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {'sys/firmware/devicetree/base/model': 'Raspberry Pi CM0\x00',
                     'sys/firmware/devicetree/base/compatible': 'raspberrypi,cm0\x00brcm,bcm2837\x00',
                     'sys/bus/i2c/devices/1-0034/name': 'tca8418',
                     'sys/class/drm/card0-HDMI-A-1/status': 'connected\n',
                     'proc/meminfo': 'MemTotal: 450000 kB\nMemAvailable: 350000 kB\n'}
            for path, data in files.items():
                p = root/path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(data)
            result = diag.inventory(root)
            self.assertEqual(result['model'], 'Raspberry Pi CM0')
            self.assertEqual(len(result['compatible']), 2)
            self.assertEqual(result['devices']['i2c'][0]['name'], 'tca8418')
            self.assertEqual(result['drm']['card0-HDMI-A-1'], 'connected')

    def test_cpu_delta(self):
        self.assertEqual(diag.busy_percent((100, 80), (200, 170)), 10)

    def test_cpu_unavailable(self):
        self.assertIsNone(diag.busy_percent(None, None))
        self.assertIsNone(diag.busy_percent((100, 80), (100, 80)))

    def test_guest_not_double_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'proc').mkdir()
            (root/'proc/stat').write_text('cpu  10 0 10 80 0 0 0 0 5 0\n')
            self.assertEqual(diag.cpu_ticks(root), (100, 80))


if __name__ == '__main__':
    unittest.main()
