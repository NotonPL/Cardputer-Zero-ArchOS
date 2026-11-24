import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_tools import ROOT


class KernelStaging(unittest.TestCase):
    def test_shell_scripts_parse(self):
        for script in (ROOT/'scripts').glob('*.sh'):
            with self.subTest(script=script.name):
                subprocess.run(['bash', '-n', str(script)], check=True)

    def test_objects_report_cannot_be_staged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'kernel').mkdir()
            (root/'vendor').mkdir()
            (root/'dt').mkdir()
            (root/'vendor/report.json').write_text(json.dumps({'mode': 'objects', 'success': True}))
            proc = subprocess.run(['bash', str(ROOT/'scripts/stage-kernel-test.sh'),
                                   str(root/'kernel'), str(root/'vendor'), str(root/'dt'),
                                   str(root/'output')], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('Successful modules-mode report required', proc.stderr)
            self.assertFalse((root/'output').exists())

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sentinel = root/'keep'
            sentinel.write_text('unchanged')
            proc = subprocess.run(['bash', str(ROOT/'scripts/stage-kernel-test.sh'),
                                   str(root), str(root), str(root), str(root)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(sentinel.read_text(), 'unchanged')
