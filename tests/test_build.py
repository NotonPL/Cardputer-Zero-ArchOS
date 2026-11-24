import io
import json
from pathlib import Path
import struct
import tarfile
import tempfile
import unittest
from test_tools import load, ROOT

fetcher = load('fetch_build_sources')
builder = load('build_vendor_modules')


class Archives(unittest.TestCase):
    def archive(self, directory, name='repo/file.c', link=None):
        archive = directory/'source.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            item = tarfile.TarInfo(name)
            if link is None:
                item.size = 3
                tar.addfile(item, io.BytesIO(b'abc'))
            else:
                item.type = tarfile.SYMTYPE
                item.linkname = link
                tar.addfile(item)
        return archive

    def test_extract_regular_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fetcher.extract(self.archive(root), root/'new')
            self.assertEqual((root/'new/file.c').read_bytes(), b'abc')

    def test_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                fetcher.extract(self.archive(root, 'repo/../../escape'), root/'new')
            self.assertFalse((root/'new').exists())

    def test_escape_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                fetcher.extract(self.archive(root, 'repo/link', '../../escape'), root/'new')

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'new').mkdir()
            with self.assertRaises(ValueError):
                fetcher.extract(self.archive(root), root/'new')

    def test_existing_bad_archive_rejected_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = dict(repository='test/test', revision='a'*40, sha256='0'*64)
            (root/('a'*40+'.tar.gz')).write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
                fetcher.fetch(entry, root)


class Kbuild(unittest.TestCase):
    def prepare(self, root):
        (root/'.config').write_text('CONFIG_ARM64=y\nCONFIG_MODULES=y\nCONFIG_MODVERSIONS=y\n')
        for name in ('include/generated/autoconf.h', 'include/config/auto.conf'):
            path = root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('test fixture')

    def test_full_modules_require_symvers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare(root)
            builder.preflight(root, 'objects')
            with self.assertRaisesRegex(ValueError, 'Module.symvers'):
                builder.preflight(root, 'modules')

    def test_non_arm64_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'.config').write_text('CONFIG_X86_64=y\nCONFIG_MODULES=y\n')
            with self.assertRaisesRegex(ValueError, 'ARM64'):
                builder.preflight(root, 'objects')

    def test_staging_uses_own_kbuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for group, targets in builder.GROUPS.items():
                path = root/'vendor/modules'/group
                path.mkdir(parents=True, exist_ok=True)
                (path/'Makefile').write_text('install: destructive-command')
                for target in targets:
                    (path/(target+'.c')).write_text('/* fixture */')
            hashes = builder.stage_sources(root/'vendor', root/'stage')
            self.assertEqual(len(hashes), len(builder.TARGETS))
            self.assertFalse((root/'stage/Makefile').exists())
            self.assertNotIn('install', (root/'stage/Kbuild').read_text().split('\n', 1)[1])

    def test_commands_have_no_install_or_bypass(self):
        cmd = builder.command(Path('/kernel'), Path('/out'), 'aarch64-linux-gnu-', 2, 'objects')
        self.assertIn('ARCH=arm64', cmd)
        self.assertNotIn('modules', cmd)
        self.assertTrue(cmd[-1].endswith('.o'))
        full = builder.command(Path('/kernel'), Path('/out'), '', 2, 'modules')
        self.assertEqual(full[-1], 'modules')
        self.assertNotIn('KBUILD_MODPOST_WARN=1', full)

    def test_elf_machine_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'test.o'
            header = bytearray(20)
            header[:6] = b'\x7fELF\x02\x01'
            struct.pack_into('<H', header, 18, 183)
            path.write_bytes(header)
            self.assertTrue(builder.arm64_elf(path))
            struct.pack_into('<H', header, 18, 62)
            path.write_bytes(header)
            self.assertFalse(builder.arm64_elf(path))

    def test_source_lock_matches_audit(self):
        lock = json.loads((ROOT/'kernel/build-lock.json').read_text())
        evidence = json.loads((ROOT/'hardware/vendor-evidence.json').read_text())
        self.assertEqual(lock['vendor']['revision'], evidence['revision'])
