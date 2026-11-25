import json
import sys
import unittest
from test_tools import ROOT

sys.path.insert(0, str(ROOT/'tools'))
from check_kernel_contract import check
from inspect_stock_config import parse_kernel


class KernelContract(unittest.TestCase):
    def setUp(self):
        self.rules = {'builtin': ['ARM64'], 'enabled': ['PWM'], 'disabled': ['KEYBOARD_TCA8418']}

    def test_enabled_m_or_y(self):
        for value in ('m', 'y'):
            self.assertEqual(check({'CONFIG_ARM64': 'y', 'CONFIG_PWM': value}, self.rules), [])

    def test_builtin_cannot_be_module(self):
        self.assertEqual(check({'CONFIG_ARM64': 'm', 'CONFIG_PWM': 'y'}, self.rules)[0]['symbol'], 'CONFIG_ARM64')

    def test_missing_required_is_failure(self):
        self.assertTrue(check({}, self.rules))

    def test_competing_driver_rejected(self):
        config = {'CONFIG_ARM64': 'y', 'CONFIG_PWM': 'y', 'CONFIG_KEYBOARD_TCA8418': 'm'}
        self.assertEqual(check(config, self.rules)[0]['requirement'], 'disabled')

    def test_fragment_has_no_duplicate_options(self):
        config = parse_kernel((ROOT/'kernel/cardputer-v5.config').read_text())
        self.assertEqual(config['CONFIG_MODVERSIONS'], 'y')

    def test_rules_have_unique_symbols(self):
        rules = json.loads((ROOT/'kernel/contract.json').read_text())
        symbols = sum(rules.values(), [])
        self.assertEqual(len(symbols), len(set(symbols)))
