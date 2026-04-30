# GMStools 环境配置与安装说明

## 运行环境

| 项目 | 要求 |
|------|------|
| Python | 3.10 及以上 |
| 操作系统 | Windows 10+ / Ubuntu 20.04+ / macOS |
| ADB 工具 | 外置于 `platform-tools/` 目录 |

---

## Python 依赖库

### 一键安装

```bash
pip install -r requirements.txt
```

### 详细清单

| 库 | 版本 | 用途 |
|----|------|------|
| **pyqt6** | 6.10.2 | GUI 框架，整个应用的主界面基于此构建 |
| **pyqt6-qt6** | 6.10.2 | Qt6 运行时二进制，pyqt6 的底层依赖 |
| **pyqt6-sip** | 13.11.1 | PyQt6 与 C++ Qt 库之间的 SIP 绑定层 |
| **openpyxl** | 3.1.5 | Excel 文件 (.xlsx) 的读写，用于体检报告导出、数据对比等 |
| **beautifulsoup4** | 4.14.3 | HTML 解析器，用于模块对比页面的 HTML 报告解析 |
| **Pillow** | 12.1.1 | 图片处理，用于图标生成、Miku.jpg 背景图转换 |
| **cryptography** | ≥42.0.0 | RSA-SHA256 签名，用于展讯设备解锁时的 token 签名 |

pip install pyqt6==6.10.2 pyqt6-qt6==6.10.2 pyqt6-sip==13.11.1 openpyxl==3.1.5 beautifulsoup4==4.14.3 Pillow==12.1.1 "cryptography>=42.0.0" pyinstaller 

### 可选依赖（仅打包需要）

| 库 | 用途 |
|----|------|
| **pyinstaller** | 将 Python 项目打包为独立可执行文件 (EXE/ELF) |

---

## 外置工具目录

### platform-tools/

存放 ADB 和 fastboot 工具，按平台分目录：

```
platform-tools/
├── linux/
│   ├── adb
│   ├── fastboot
│   └── ... (etc1tool, sqlite3 等)
└── windows/
    ├── adb.exe
    ├── fastboot.exe
    ├── AdbWinApi.dll
    ├── AdbWinUsbApi.dll
    └── ... (etc1tool.exe, sqlite3.exe 等)
```

应用会自动检测并使用 `platform-tools/` 下的工具，也支持系统的 adb/fastboot。

### unlock/

存放解锁和刷机相关的工具与签名文件：

```
unlock/
├── fastboot              # Linux/Mac 专用 fastboot（支持 flashing unlock_bootloader）
├── fastboot.exe          # Windows 专用 fastboot
├── rsa4096_vbmeta*.pem   # 各设备型号的 RSA 签名私钥
├── signidentifier_unlockbootloader.sh  # token 签名脚本（已由 Python 替代）
├── unlock.sh / lock.sh   # 辅助脚本
├── signature.bin         # 预置签名文件
└── 刷机步骤.txt          # 操作说明
```

---

## 目录结构

```
GMStools/
├── app_controller.py          # 应用入口
├── window_manager.py          # 主窗口管理
├── PageManager.py             # 页面导航与注册
├── left_menu.py               # 左侧菜单栏
├── BackgroundManager.py       # 背景图管理
├── usekey.py                  # 许可/免责声明签名验证
├── config.ini                 # 用户配置文件（运行时生成）
├── build_info.py              # 编译日期（打包时生成）
├── Miku.jpg                   # 默认背景图
├── requirements.txt           # Python 依赖
├── build_all_platforms.py     # 多平台打包脚本
├── GMStools.spec              # PyInstaller spec 文件
│
├── CustomTitle/               # 自定义标题栏组件
│   ├── customtitlebar.py
│   └── titleWindowControlButtons.py
│
├── theme/                     # 主题色彩与 QSS 样式
│   ├── miku_theme.py          # Miku Hatsune 主题色常量与样式函数
│   └── __init__.py
│
├── pages/                     # 功能页面
│   ├── Autounlock/            # 解锁与镜像刷入（MTK/展讯）
│   ├── CheckupReport/         # 体检报告生成
│   ├── Concerning/            # 关于/设置页
│   ├── Ctsverifierdb/         # CTS Verifier 数据库
│   ├── CVAutomation/          # CV 自动化
│   ├── Disclaimer/            # 免责声明
│   ├── Modulecomparison/      # 模块对比
│   ├── Newfeatures/           # 新功能
│   └── SMRComparison/         # SMR 对比（Feature/Package）
│       ├── SMRComparison.py   # SMR 对比页面入口
│       ├── BCompare_Feature.py
│       ├── BCompare_Package.py
│       ├── data_models.py
│       ├── html_generator.py
│       ├── Package_comparator.py
│       ├── Package_file_utils.py
│       ├── Package_html_reporter.py
│       ├── Package_models.py
│       ├── Select_directory.py
│       ├── smart_comparator.py
│       ├── strict_comparator.py
│       ├── SMR_Analyzer.py
│       ├── SMR_Comparator.py
│       ├── SMR_EventHandler.py
│       ├── SMR_FileUtils.py
│       ├── SMR_InfoExtractor.py
│       ├── SMR_PatchChecker.py
│       ├── SMR_ReportGenerator.py
│       ├── SMR_TimeUtils.py
│       ├── SMR_UI.py
│       └── usage_example.py
│
├── platform-tools/            # ADB 工具（外置，不入包）
│   ├── linux/
│   └── windows/
│
└── unlock/                    # 解锁/刷机工具（外置，不入包）
    ├── fastboot / fastboot.exe
    ├── rsa4096_vbmeta*.pem
    └── ...
```

---

## 快速开始

### 开发模式运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 确保外置工具就位
ls platform-tools/linux/   # Linux: adb 和 fastboot
ls unlock/                  # 解锁相关文件

# 3. 运行
python app_controller.py
```

### 打包为可执行文件

```bash
# 当前平台打包
python build_all_platforms.py

# 输出在 release_windows/ 或 release_linux/
```

### 发布包使用

解压后确保以下文件在同一目录：
- `GMStools` (或 `GMStools.exe`) — 主程序
- `platform-tools/` — ADB 工具
- `unlock/` — 解锁工具和 PEM 签名文件

Windows 双击 `GMStools.exe` 或运行 `启动GMStools.bat`。
Linux 运行 `./GMStools` 或执行 `./install.sh` 安装到系统。
