#!/bin/bash

# GMStools 安装脚本
echo "=== GMStools 安装脚本 ==="
echo ""

# 检查是否在正确的目录中
if [ ! -f "GMStools" ]; then
    echo "❌ 请确保在 release_linux 目录中运行此脚本"
    echo "   当前目录: $(pwd)"
    exit 1
fi

# 显示安装选项
echo "选择安装方式:"
echo "1) 系统安装 (需要 sudo 权限，所有用户可用)"
echo "2) 用户安装 (仅当前用户可用，推荐)"
echo "3) 便携模式 (不安装，直接使用)"
read -p "请输入选择 [1-3]: " choice

case $choice in
    1)
        # 系统安装
        echo "进行系统安装..."
        
        # 复制可执行文件到 /usr/local/bin
        sudo cp GMStools /usr/local/bin/
        sudo chmod 755 /usr/local/bin/GMStools
        
        # 复制图标
        if [ -f "icon.png" ]; then
            sudo cp icon.png /usr/share/icons/hicolor/256x256/apps/gmstools.png
            sudo gtk-update-icon-cache /usr/share/icons/hicolor/ -f
        fi
        
        # 安装 .desktop 文件
        if [ -f "GMStools.desktop" ]; then
            sed 's|Icon=.*|Icon=gmstools|' GMStools.desktop | sudo tee /usr/share/applications/GMStools.desktop > /dev/null
        fi
        
        echo "✓ 系统安装完成！"
        echo "   现在可以在终端中输入 'GMStools' 运行"
        echo "   或在应用菜单中搜索 'GMStools'"
        ;;
    2)
        # 用户安装
        echo "进行用户安装..."
        
        # 创建必要的目录
        mkdir -p ~/.local/bin
        mkdir -p ~/.local/share/icons/hicolor/256x256/apps
        mkdir -p ~/.local/share/applications
        
        # 复制可执行文件
        cp GMStools ~/.local/bin/
        chmod 755 ~/.local/bin/GMStools
        
        # 复制图标
        if [ -f "icon.png" ]; then
            cp icon.png ~/.local/share/icons/hicolor/256x256/apps/gmstools.png
            gtk-update-icon-cache ~/.local/share/icons/hicolor/ -f 2>/dev/null || true
        fi
        
        # 安装 .desktop 文件
        if [ -f "GMStools.desktop" ]; then
            sed -e "s|Exec=.*|Exec=$HOME/.local/bin/GMStools|"                 -e "s|Icon=.*|Icon=gmstools|"                 GMStools.desktop > ~/.local/share/applications/GMStools.desktop
        fi
        
        # 更新桌面数据库
        update-desktop-database ~/.local/share/applications 2>/dev/null || true
        
        echo "✓ 用户安装完成！"
        echo "   现在可以在终端中输入 'GMStools' 运行"
        echo "   或在应用菜单中搜索 'GMStools'"
        echo ""
        echo "注意: 如果 'GMStools' 命令不可用，请重启终端或运行:"
        echo "      export PATH="$HOME/.local/bin:$PATH""
        ;;
    3)
        # 便携模式
        echo "便携模式 - 无需安装"
        echo ""
        echo "使用方法:"
        echo "1. 确保当前目录有 GMStools 文件"
        echo "2. 给予执行权限: chmod +x GMStools"
        echo "3. 运行: ./GMStools"
        echo ""
        echo "或双击 GMStools.desktop 文件"
        echo "(可能需要右键 -> 属性 -> 权限 -> 允许作为程序执行)"
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "=== 安装完成 ==="
