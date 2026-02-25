#!/bin/bash

# GMStools 卸载脚本
echo "=== GMStools 卸载脚本 ==="
echo ""

echo "选择卸载方式:"
echo "1) 卸载系统安装"
echo "2) 卸载用户安装"
read -p "请输入选择 [1-2]: " choice

case $choice in
    1)
        # 系统卸载
        echo "卸载系统安装..."
        
        if [ -f "/usr/local/bin/GMStools" ]; then
            sudo rm -f /usr/local/bin/GMStools
            echo "✓ 已移除: /usr/local/bin/GMStools"
        fi
        
        if [ -f "/usr/share/icons/hicolor/256x256/apps/gmstools.png" ]; then
            sudo rm -f /usr/share/icons/hicolor/256x256/apps/gmstools.png
            sudo gtk-update-icon-cache /usr/share/icons/hicolor/ -f
            echo "✓ 已移除图标"
        fi
        
        if [ -f "/usr/share/applications/GMStools.desktop" ]; then
            sudo rm -f /usr/share/applications/GMStools.desktop
            echo "✓ 已移除桌面入口"
        fi
        
        echo "✓ 系统卸载完成"
        ;;
    2)
        # 用户卸载
        echo "卸载用户安装..."
        
        if [ -f "$HOME/.local/bin/GMStools" ]; then
            rm -f "$HOME/.local/bin/GMStools"
            echo "✓ 已移除: ~/.local/bin/GMStools"
        fi
        
        if [ -f "$HOME/.local/share/icons/hicolor/256x256/apps/gmstools.png" ]; then
            rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/gmstools.png"
            gtk-update-icon-cache "$HOME/.local/share/icons/hicolor/" -f 2>/dev/null || true
            echo "✓ 已移除图标"
        fi
        
        if [ -f "$HOME/.local/share/applications/GMStools.desktop" ]; then
            rm -f "$HOME/.local/share/applications/GMStools.desktop"
            echo "✓ 已移除桌面入口"
        fi
        
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
        
        echo "✓ 用户卸载完成"
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "=== 卸载完成 ==="
