#!/usr/bin/env python3
"""Fetch hash-locked sources. Extract only into a NEW directory; never execute code."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def extract(archive, destination):
    if destination.exists() or destination.is_symlink():
        raise ValueError(f'destination already exists: {destination}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        with tarfile.open(archive) as tar:
            members = tar.getmembers()
            roots = {PurePosixPath(m.name).parts[0] for m in members if m.name}
            if len(roots) != 1:
                raise ValueError('archive must have one root')
            for member in members:
                path = PurePosixPath(member.name)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('unsafe archive path')
            base = Path(tmp).resolve()
            safe_root = base/next(iter(roots))
            # Extract regular files first, then safe relative symlinks. No archive
            # ownership, special files, hardlinks or writes through symlinks.
            for member in members:
                path = base/member.name
                if member.isdir():
                    path.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as src, path.open('xb') as dst:
                        shutil.copyfileobj(src, dst)
                    path.chmod(member.mode & 0o777)
                elif not member.issym():
                    raise ValueError('unsupported archive entry')
            for member in members:
                if not member.issym():
                    continue
                path = base/member.name
                link = PurePosixPath(member.linkname)
                if link.is_absolute() or not (path.parent/str(link)).resolve().is_relative_to(safe_root):
                    raise ValueError('unsafe archive symlink')
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.parent.resolve().is_relative_to(base):
                    raise ValueError('unsafe symlink parent')
                path.symlink_to(member.linkname)
        source = Path(tmp)/roots.pop()
        if not source.is_dir() or source.is_symlink():
            raise ValueError('invalid archive root')
        source.rename(destination)


def fetch(entry, cache):
    repo, revision, expected = entry['repository'], entry['revision'], entry['sha256']
    if not re.fullmatch(r'[\w-]+/[\w.-]+', repo) or not re.fullmatch('[a-f0-9]{40}', revision):
        raise ValueError('invalid source pin')
    if not re.fullmatch('[a-f0-9]{64}', expected):
        raise ValueError('invalid SHA256')
    cache.mkdir(parents=True, exist_ok=True)
    target = cache/f'{revision}.tar.gz'
    if not target.exists():
        with tempfile.NamedTemporaryFile(dir=cache, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                with urllib.request.urlopen(f'https://codeload.github.com/{repo}/tar.gz/{revision}', timeout=120) as response:
                    shutil.copyfileobj(response, stream)
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        if hashlib.file_digest(temporary.open('rb'), 'sha256').hexdigest() != expected:
            temporary.unlink()
            raise ValueError('download SHA256 mismatch')
        temporary.replace(target)
    with target.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != expected:
        raise ValueError(f'cached archive SHA256 mismatch: {target}')
    return target


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('component', choices=['kernel', 'vendor'])
    ap.add_argument('--destination', required=True, type=Path)
    ap.add_argument('--cache', type=Path, default=ROOT/'.cache/downloads')
    args = ap.parse_args()
    if args.destination.exists() or args.destination.is_symlink():
        ap.error('destination must not exist; choose a new workspace')
    lock = json.loads((ROOT/'kernel/build-lock.json').read_text())
    extract(fetch(lock[args.component], args.cache), args.destination)


if __name__ == '__main__':
    main()
