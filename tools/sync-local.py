#!/usr/bin/env python3
"""Interactive local export, review and build. Never commits or pushes."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('notes_sync', root / 'tools/notes-sync.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

try:
    account = input('备忘录账户 [iCloud]：').strip() or 'iCloud'
    folder = input('专用文件夹 [Blog测试]：').strip() or 'Blog测试'
    sync.preview(sync.capture(account, folder))
    manifest = json.loads((sync.STAGE / 'manifest.json').read_text())
    print(f'已生成 {len(manifest)} 条笔记。预览目录：{sync.STAGE}')
    subprocess.run(['/usr/bin/open', str(sync.STAGE)], check=True)
    if input('检查预览后，输入“写入”继续；回车取消：').strip() != '写入':
        print('已取消，未改动博客。')
        sys.exit(0)
    sync.apply()
    subprocess.run([sys.executable, 'build.py'], cwd=root, check=True)
    print('本地更新完成。未提交、未推送；推送前请自行检查内容。')
except KeyboardInterrupt:
    print('\n已中断。若已执行写入，旧文件备份仍保留在预览目录。')
    sys.exit(1)
except Exception as exc:
    print('操作停止：', str(exc), file=sys.stderr)
    sys.exit(1)
