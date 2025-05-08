#!/bin/bash
# 构建和上传sync2llmtxt到PyPI的脚本

# 安装必要的构建工具（如果没有）
pip install --upgrade pip build twine

# 构建发行版
echo "正在构建发行版..."
python -m build

# 检查发行版
echo "检查构建文件..."
ls -la dist/

# 上传到PyPI（可选，取消注释此行）
echo "准备上传到PyPI..."
echo "如果你想上传到PyPI，请确保你已经登录twine:"
echo "twine upload dist/*"
# echo ""
# echo "如果你想上传到TestPyPI进行测试:"
# echo "twine upload --repository testpypi dist/*"
echo ""
echo "测试发布后，可以这样安装:"
echo "pip install --index-url https://test.pypi.org/simple/ sync2llmtxt"
echo ""
echo "说明："
echo "1. 首次上传需要在PyPI注册账号: https://pypi.org/account/register/"
echo "2. 构建成功后，运行: twine upload dist/*"
echo "3. 上传后，用户可以用pip install sync2llmtxt安装"

# 取消下面的注释可以直接上传（谨慎使用）
# read -p "是否上传到PyPI? (y/n) " -n 1 -r
# echo
# if [[ $REPLY =~ ^[Yy]$ ]]
# then
#     twine upload dist/*
# fi 