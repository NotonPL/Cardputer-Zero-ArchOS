import hashlib
import json
import unittest
from test_tools import load, ROOT

stock = load('inspect_stock_config')


class StockConfiguration(unittest.TestCase):
    def test_disabled_and_missing_are_distinct(self):
        result = stock.report(b'CONFIG_ARM64=y\n# CONFIG_MODULE_SIG is not set\n', b'')
        self.assertEqual(result['symbols']['CONFIG_MODULE_SIG'], 'n')
        self.assertIsNone(result['symbols']['CONFIG_MODVERSIONS'])

    def test_values_preserved(self):
        self.assertEqual(stock.parse_kernel('CONFIG_ZRAM_DEF_COMP="zstd"')['CONFIG_ZRAM_DEF_COMP'], '"zstd"')

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            stock.parse_kernel('CONFIG_ARM64=y\n# CONFIG_ARM64 is not set')

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            stock.parse_kernel('# comments only')

    def test_filters_and_duplicates_preserved(self):
        records = stock.parse_boot('gpu_mem=128\n[cm5]\ndtoverlay=dwc2,dr_mode=host\n[all]\ndtoverlay=dwc2\ndtoverlay=dwc2\n')
        self.assertEqual([r['section'] for r in records], ['unfiltered', 'cm5', 'all', 'all'])
        self.assertEqual(len(records), 4)

    def test_include_not_executed(self):
        record = stock.parse_boot('include secrets.txt')[0]
        self.assertEqual(record['key'], 'include secrets.txt')
        self.assertIsNone(record['value'])

    def test_reference_is_reproducible(self):
        root = ROOT/'hardware/reference/stock-cm0-v5'
        report = stock.report((root/'kernel.config').read_bytes(), (root/'config.txt').read_bytes())
        self.assertEqual(report, json.loads((root/'analysis.json').read_text()))
        self.assertEqual(report['symbols']['CONFIG_ARM64'], 'y')
        self.assertEqual(report['symbols']['CONFIG_MODVERSIONS'], 'y')
        self.assertEqual(report['symbols']['CONFIG_BATTERY_BQ27XXX'], 'n')
        self.assertEqual(report['symbols']['CONFIG_SND_SOC_ES8389'], 'n')
        self.assertEqual(report['symbols']['CONFIG_RTC_DRV_DS1307'], 'm')
