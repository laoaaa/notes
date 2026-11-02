#!/usr/bin/env python3
"""Independent plain-text static blog generator; Python standard library only."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from datetime import datetime
from zoneinfo import ZoneInfo
import json

ROOT = Path(__file__).resolve().parent

class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'br'): self.parts.append('\n')
    def handle_data(self, text): self.parts.append(text)
    def handle_endtag(self, tag):
        if tag == 'p': self.parts.append('\n')

def read_note(path):
    raw = path.read_text(encoding='utf-8')
    if not raw.startswith('---\n'): raise ValueError('Missing metadata: ' + path.name)
    head, body = raw[4:].split('\n---\n', 1)
    meta = dict(line.split(': ', 1) for line in head.splitlines())
    date = datetime.fromisoformat(meta['created'].replace('Z', '+00:00'))
    if date.tzinfo is None: raise ValueError('Date requires timezone')
    parser = Text(); parser.feed(body)
    return date, ''.join(parser.parts).strip(), path.stem

def build():
    settings = json.loads((ROOT / 'site.json').read_text())
    notes = sorted((read_note(p) for p in (ROOT / 'notes').glob('*.md')), reverse=True)
    cards = []
    for date, text, slug in notes:
        cards.append(f'<article id="{escape(slug, quote=True)}"><time datetime="{date.isoformat()}">{date.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y年%m月%d日 · %H:%M")}</time><div class="text">{escape(text)}</div></article>')
    title = escape(settings['title'])
    page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title><meta name="description" content="{escape(settings['description'], quote=True)}"><style>
:root{{color-scheme:light;--ink:#26352f;--muted:#718078;--line:#dce3dc;--paper:#f7f8f3}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.85 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}main{{max-width:760px;margin:auto;padding:72px 28px 40px}}header{{padding-bottom:42px;border-bottom:1px solid var(--line)}}.eyebrow{{font-size:12px;letter-spacing:.22em;color:var(--muted)}}h1{{font-size:38px;letter-spacing:.08em;font-weight:500;margin:12px 0}}.description{{color:var(--muted);margin:0}}.count{{font-size:12px;color:var(--muted);margin-top:22px}}article{{padding:32px 0;border-bottom:1px solid var(--line)}}time{{font-size:12px;letter-spacing:.04em;color:var(--muted)}}.text{{white-space:pre-wrap;overflow-wrap:anywhere;margin-top:12px}}footer{{padding-top:32px;color:var(--muted);font-size:12px}}@media(max-width:500px){{main{{padding:40px 22px}}h1{{font-size:30px}}}}
</style></head><body><main><header><div class="eyebrow">NOTES / 文字存档</div><h1>{title}</h1><p class="description">{escape(settings['description'])}</p><div class="count">共 {len(notes)} 条记录</div></header>{''.join(cards) if cards else '<p>这里还没有记录。</p>'}<footer>文字留在这里，慢慢积累。</footer></main></body></html>'''
    output = ROOT / 'dist'
    if output.is_symlink(): raise ValueError('Refusing symlink output')
    output.mkdir(exist_ok=True)
    (output / 'index.html').write_text(page, encoding='utf-8')
    (output / '.nojekyll').touch()
    print(f'Built {len(notes)} notes → dist/index.html')

if __name__ == '__main__': build()
