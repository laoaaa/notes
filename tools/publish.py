"""Explicit, notes-only Git publication; no forced updates or stored credentials."""
from pathlib import Path
import re
import subprocess


def git_command():
    command = ['git']
    try:
        config = subprocess.check_output(['scutil', '--proxy'], text=True, timeout=5)
        def value(key):
            match = re.search(r'^\s*' + key + r'\s*:\s*(\S+)', config, re.M)
            return match.group(1) if match else ''
        host, port = value('HTTPSProxy'), value('HTTPSPort')
        if value('HTTPSEnable') == '1' and host in ('127.0.0.1', 'localhost') and port.isdigit():
            command += ['-c', f'http.proxy=http://{host}:{port}']
    except (OSError, subprocess.SubprocessError):
        pass
    return command


class Publisher:
    def __init__(self, root, command=None):
        self.root = Path(root)
        self.command = command or git_command()

    def git(self, *args):
        result = subprocess.run(self.command + list(args), cwd=self.root,
                                text=True, capture_output=True, timeout=120)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or 'Git 操作失败')
        return result.stdout.strip()

    def prepare(self):
        if self.git('branch', '--show-current') != 'main':
            raise RuntimeError('请先切换到 main 分支')
        if self.git('status', '--porcelain'):
            raise RuntimeError('项目有未提交改动，请先处理；本工具不会代为上传程序或其他文件')
        self.git('fetch', 'origin')
        ahead, behind = map(int, self.git('rev-list', '--left-right', '--count',
                                         'HEAD...origin/main').split())
        if ahead:
            raise RuntimeError('本地有尚未推送的提交，请先人工确认并推送，避免顺带上传其他改动')
        if behind:
            self.git('merge', '--ff-only', 'origin/main')

    def publish(self):
        if self.git('diff', '--cached', '--name-only'):
            raise RuntimeError('暂存区非空，停止发布')
        self.git('add', '--', 'notes')
        names = self.git('diff', '--cached', '--name-only', '-z').split('\0')
        if any(n and not n.startswith('notes/') for n in names):
            raise RuntimeError('发现笔记目录外的暂存文件，停止发布')
        if any(names):
            self.git('commit', '-m', 'Update notes')
        # Fetch again: refuse divergence caused by concurrent remote edits.
        self.git('fetch', 'origin')
        behind = int(self.git('rev-list', '--count', 'HEAD..origin/main'))
        if behind:
            raise RuntimeError('远程刚有更新，已保留本地提交；停止推送，请先合并')
        self.git('push', 'origin', 'HEAD:main')
