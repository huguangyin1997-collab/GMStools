GMStools Ubuntu/Linux 版本

📁 文件说明:
├── GMStools           - 主程序（可执行文件）
├── GMStools.desktop   - 桌面快捷方式
├── icon.png          - 程序图标
├── Miku.jpg          - 背景图片
├── install.sh        - 安装脚本
├── uninstall.sh      - 卸载脚本
└── README.txt        - 本文件

🚀 使用方法:
方式1: 运行安装脚本（推荐）
      1. chmod +x install.sh
      2. ./install.sh
      3. 选择安装方式

方式2: 使用桌面快捷方式
      1. 双击 GMStools.desktop
      2. 如果提示，选择"允许启动"
      3. 图标将显示在应用菜单中

方式3: 直接运行
      1. chmod +x GMStools
      2. ./GMStools

🔧 常见问题:
Q: 图标不显示？
A: 运行安装脚本，它会处理图标缓存

Q: 双击 .desktop 文件无法启动？
A: 右键 -> 属性 -> 权限 -> 勾选"允许作为程序执行"

Q: 安装后命令不可用？
A: 重启终端，或运行: export PATH="~/.local/bin:$PATH"

📦 分发说明:
整个 release_linux 文件夹可以直接发给其他 Linux 用户
用户只需运行 install.sh 即可安装
