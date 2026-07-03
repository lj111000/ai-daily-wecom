#!/usr/bin/env bash
# 一键推送到所有 remote（gitee + github）
# 用法：./push-all.sh "提交信息"
#
# 不带参数则只推送当前已暂存的提交：./push-all.sh

set -e
cd "$(dirname "$0")"

if [ -n "$1" ]; then
    git add -A
    git commit -m "$1"
fi

echo "→ 推送到 gitee (origin)..."
git push origin master

echo "→ 推送到 github (github)..."
git push github master

echo "✅ 全部推送完成"
