# 独立文字博客

个人文字博客：从指定的苹果备忘录文件夹生成本地预览，确认后写入笔记，再由你提交并推送到 GitHub Pages。页面和生成器独立编写，只使用 Python 标准库。部署使用 GitHub 官方 Actions。

## 日常使用

Mac 安装 Python 3 后，双击 本地同步.command，默认读取 iCloud / Blog测试。先查看生成的预览，再输入“写入”；工具写入 notes 并构建 dist。不会提交或推送，不需要 GitHub 令牌，不修改苹果备忘录。

支持文字与段落，不支持图片、附件、富文本样式及 Markdown 排版；遇附件或加密笔记停止。重复同步按稳定笔记 ID 更新文件，覆盖前备份，不自动删除已发布内容。

## 本地预览

在本目录运行：

```
python3 build.py
python3 -m http.server 4174 --bind 127.0.0.1 --directory dist
```

打开 http://127.0.0.1:4174/ 。构建后刷新即可。

site.json 修改标题与描述。notes/example.md 是虚构示例，真实笔记尚未迁入。不要将整个上一级目录上传。

## GitHub Pages

当前目录就是仓库根目录，已绑定 https://github.com/laoaaa/prprp.git ，main 分支推送后自动部署。

提交源码、notes、tools、site.json、build.py 和隐藏的 .github 目录。dist、.notes-staging、缓存和环境文件不提交。Settings → Pages → Source 选择 GitHub Actions，推送 main 后自动构建。页面没有绝对资源路径，适用于仓库子路径。

## 隐私与恢复

.notes-staging 包含本地预览、旧文件备份，必须保留在忽略列表，不强制上传。确认 notes 内容允许公开后再提交。被推送的笔记可能留存在 Git 历史中。Notes 自动化权限是应用级权限，文件夹限制由代码执行，并非系统级隔离。

本地覆盖采用原子文件替换，但批量更新不是整体事务；出现部分失败可从 .notes-staging/backup-* 恢复旧文件。


## 推送更新

在当前目录打开终端，检查笔记可以公开后执行：

```bash
git add notes
git commit -m "Update notes"
git -c http.proxy=http://127.0.0.1:15236 push
```

代理端口为本机当前配置，代理软件调整后需相应更新。目录已整理到项目根目录，不再进入任何子项目目录。页面地址：https://laoaaa.github.io/prprp/ 。当前未启用定时同步或自动推送。
