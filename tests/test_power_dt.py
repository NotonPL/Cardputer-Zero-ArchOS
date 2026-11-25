import json
from pathlib import Path
import struct
import tempfile
import unittest
from test_tools import load

power = load('inspect_power_dt')


def cell(*values):
    return struct.pack('>' + 'I' * len(values), *values)


class PowerDT(unittest.TestCase):
    def fixture(self, root):
        tree = root/'sys/firmware/devicetree/base'
        provider = tree/'soc/i2c/gpio@4f'
        node = tree/'powerfail'
        provider.mkdir(parents=True)
        node.mkdir()
        (provider/'compatible').write_bytes(b'm5stack,m5ioe1\0')
        (provider/'phandle').write_bytes(cell(42))
        (provider/'#gpio-cells').write_bytes(cell(2))
        (node/'compatible').write_bytes(b'cardputerzero,powerfail-suo\0')
        (node/'disabled-gpios').write_bytes(cell(42, 11, 1))
        (node/'debounce-ms').write_bytes(cell(500))
        return tree, provider, node

    def test_no_interfaces_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = power.inspect(Path(tmp))
            self.assertFalse(report['dt_available'])
            self.assertFalse(report['hardware_validated'])
            self.assertEqual(report['powerfail_nodes'], [])

    def test_vendor_gpio_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(Path(tmp))
            report = power.inspect(Path(tmp))
            node = report['powerfail_nodes'][0]
            self.assertEqual(node['debounce_ms_cells'], [500])
            self.assertEqual(node['disabled_gpio']['offset'], 11)
            self.assertTrue(node['disabled_gpio']['active_low'])
            self.assertFalse(node['irq_gpio']['resolved'])
            json.dumps(report)

    def test_malformed_cells(self):
        self.assertIsNone(power.cells(b'abc'))
        self.assertIsNone(power.cells(None))
        self.assertEqual(power.cells(cell(0x12345678)), [0x12345678])

    def test_unknown_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, node = self.fixture(Path(tmp))
            (node/'disabled-gpios').write_bytes(cell(99, 11, 1))
            self.assertFalse(power.inspect(Path(tmp))['powerfail_nodes'][0]['disabled_gpio']['resolved'])

    def test_unsupported_provider_cell_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, provider, _ = self.fixture(Path(tmp))
            (provider/'#gpio-cells').write_bytes(cell(3))
            self.assertFalse(power.inspect(Path(tmp))['powerfail_nodes'][0]['disabled_gpio']['resolved'])

    def test_duplicate_phandle_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree, _, _ = self.fixture(Path(tmp))
            other = tree/'other'
            other.mkdir()
            (other/'compatible').write_bytes(b'other\0')
            (other/'phandle').write_bytes(cell(42))
            self.assertFalse(power.inspect(Path(tmp))['powerfail_nodes'][0]['disabled_gpio']['resolved'])

    def test_hw_id_and_disabled_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, _, node = self.fixture(root)
            (node/'status').write_bytes(b'disabled\0')
            (root/'proc').mkdir()
            (root/'proc/cardputerzero_hw_id').write_text('0x06\n')
            report = power.inspect(root)
            self.assertEqual(report['hw_id'], '0x06')
            self.assertEqual(report['powerfail_nodes'][0]['status'], 'disabled')
            (root/'proc/cardputerzero_hw_id').write_text('unexpected private content')
            self.assertIsNone(power.inspect(root)['hw_id'])

    def test_bounded_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp)/'large'
            file.write_bytes(b'x' * (power.LIMIT + 1))
            self.assertIsNone(power.blob(file))
