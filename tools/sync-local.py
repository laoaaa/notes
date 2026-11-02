#!/usr/bin/env python3
"""Local preview, with optional explicit notes-only publication."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from publish import Publisher

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('notes_sync', root / 'tools/notes-sync.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

try:
    publishing = '--publish' in sys.argv
    publisher = Publisher(root) if publishing else None
    if publisher:
        print('正在检查 GitHub 连接和远程更新……', flush=True)
        publisher.prepare()
        print('检查通过。', flush=True)
    account = input('备忘录账户 [iCloud]：').strip() or 'iCloud'
    folder = input('专用文件夹（默认：blog）：').strip() or 'blog'
    print('正在读取指定备忘录文件夹……', flush=True)
    sync.preview(sync.capture(account, folder))
    manifest = json.loads((sync.STAGE / 'manifest.json').read_text())
    print(f'已生成 {len(manifest)} 条笔记。不会自动打开文件夹。')
    print(f'需要查看预览时，可手动打开：{sync.STAGE}')
    action = '发布' if publishing else '写入'
    if input(f'确认后，输入“{action}”继续；回车取消：').strip() != action:
        print('已取消，未改动博客。')
        sys.exit(0)
    sync.apply()
    subprocess.run([sys.executable, 'build.py'], cwd=root, check=True)
    if publisher:
        print('正在提交笔记并推送，请等待……', flush=True)
        publisher.publish()
        print('已推送，GitHub 正在构建网站：https://laoaaa.github.io/prprp/')
    else:
        print('本地更新完成。未提交、未推送。')
except KeyboardInterrupt:
    print('\n已中断。若已执行写入，旧文件备份仍保留在预览目录。')
    sys.exit(1)
except Exception as exc:
    print('操作停止：', str(exc), file=sys.stderr)
    sys.exit(1)
