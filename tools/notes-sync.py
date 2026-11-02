#!/usr/bin/env python3
"""Local-only Apple Notes exporter. No network, credentials, or git operations."""
import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import tempfile
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / '.notes-staging'


def capture(account, folder):
    # Arguments travel as JSON, never interpolated into executable JavaScript.
    script = '''function run(argv) {
      const args = JSON.parse(argv[0]);
      const app = Application('Notes');
      const accounts = app.accounts.whose({name: args.account})();
      if (accounts.length !== 1) throw Error('Account must match exactly once');
      const folders = accounts[0].folders.whose({name: args.folder})();
      if (folders.length !== 1) throw Error('Folder must match exactly once');
      return JSON.stringify(folders[0].notes().map(n => {
        if (n.passwordProtected()) throw Error('Password-protected note: stopped');
        return ({
        id: n.id(), text: n.plaintext(),
        created: n.creationDate().toISOString(),
        modified: n.modificationDate().toISOString(),
        attachments: n.attachments().length
      }); }));
    }'''
    result = subprocess.run(['/usr/bin/osascript', '-l', 'JavaScript', '-e', script,
        json.dumps({'account': account, 'folder': folder})],
        capture_output=True, text=True, check=True, timeout=120)
    return json.loads(result.stdout)


def render(note):
    if note['attachments']:
        raise ValueError('Attachment found: export stopped to avoid silently losing images')
    for key in ('created', 'modified'):
        dt.datetime.fromisoformat(note[key].replace('Z', '+00:00'))
    # Store escaped plain text as HTML paragraphs: no Markdown/HTML injection,
    # external image loading, or automatic link conversion.
    body = '\n'.join('<p>' + html.escape(p).replace('\n', '<br>') + '</p>'
                     for p in note['text'].split('\n\n'))
    return ('---\ncreated: ' + note['created'] + '\nmodified: ' + note['modified']
            + '\n---\n\n' + body + '\n')


def safe_path(path):
    current = path
    while current != ROOT.parent:
        if current.is_symlink():
            raise ValueError('Refusing symbolic link')
        current = current.parent
        if current == current.parent:
            raise ValueError('Path outside project')


def atomic_write(path, content):
    safe_path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.notes-tmp-')
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def preview(notes):
    safe_path(STAGE)
    safe_path(STAGE / 'manifest.json')
    prepared = {}
    for note in notes:
        name = 'notes-' + hashlib.sha256(note['id'].encode()).hexdigest() + '.md'
        if name in prepared:
            raise ValueError('Duplicate note identity')
        prepared[name] = render(note)
    STAGE.mkdir(mode=0o700, exist_ok=True)
    files = {}
    for name, content in prepared.items():
        target = STAGE / name
        if target.is_symlink():
            raise ValueError('Refusing symbolic link')
        atomic_write(target, content.encode('utf-8'))
        files[name] = hashlib.sha256(content.encode()).hexdigest()
    atomic_write(STAGE / 'manifest.json', json.dumps(files, indent=2).encode())
    print(f'Prepared {len(files)} notes in .notes-staging; review before applying.')


def apply():
    safe_path(STAGE / 'manifest.json')
    safe_path(ROOT / 'notes')
    files = json.loads((STAGE / 'manifest.json').read_text())
    target = ROOT / 'notes'
    if target.is_symlink() or STAGE.is_symlink():
        raise ValueError('Refusing symbolic link')
    prepared = []
    for name, digest in files.items():
        if not re.fullmatch(r'notes-[0-9a-f]{64}\.md', name):
            raise ValueError('Invalid filename')
        source = STAGE / name
        if source.is_symlink() or (target / name).is_symlink():
            raise ValueError('Refusing symbolic link')
        content = source.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError('Preview changed; generate preview again')
        prepared.append((name, content))
    backup = STAGE / ('backup-' + dt.datetime.now().strftime('%Y%m%d%H%M%S%f'))
    backup.mkdir(mode=0o700)
    target.mkdir(parents=True, exist_ok=True)
    for name, content in prepared:
        dest = target / name
        if dest.exists():
            atomic_write(backup / name, dest.read_bytes())
        atomic_write(dest, content)
    print(f'Applied {len(prepared)} notes locally. Nothing uploaded or deleted.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('preview')
    p.add_argument('--account', required=True)
    p.add_argument('--folder', required=True)
    sub.add_parser('apply')
    args = parser.parse_args()
    if args.command == 'preview':
        preview(capture(args.account, args.folder))
    else:
        apply()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Stopped:', type(exc).__name__, str(exc), file=sys.stderr)
        sys.exit(1)
