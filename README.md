# GMStools — Android 测试调试一体化工具集

**版本**: v1.2.18 | **许可证**: Apache License 2.0 | **支持平台**: Windows / Linux

GMStools 是一款面向 Android 设备测试、调试与刷机的桌面工具集，基于 PyQt6 构建，初音未来主题风格。聚合了体检报告分析、模块对比、SMR 对比、CTS Verifier 数据库管理、CV 自动化、设备解锁与镜像刷入等常用能力，减少零散脚本切换，提升测试与调试效率。

---

## 功能总览

| 模块 | 功能说明 |
|------|----------|
| **体检报告** (CheckupReport) | 分析 APTS / CTS Verifier / GTS / STS / VTS 测试报告目录，自动提取 Suite Plan、Fingerprint、Security Patch，校验版本一致性与安全补丁时效 |
| **CTS Verifier 数据库** (Ctsverifierdb) | 通过 ADB 导出/导入 CTS Verifier 的 SQLite 测试结果，支持 Excel 增量对比更新 |
| **模块对比** (Modulecomparison) | 对比新旧 XML / HTML / TXT 文件中的模块差异，可视化显示双方独有模块 |
| **SMR 对比** (SMRComparison) | Feature 级与 Package 级的 SMR 差异分析，输出 HTML 对比报告，支持严格逐行对比与智能语义对比 |
| **CV 自动化** (CVAutomation) | 设备选择 → 目录选择 → 自动执行测试流程的框架界面 |
| **解锁与镜像** (Autounlock) | 最多 4 台设备并行操作，支持 MTK 解锁、展讯 RSA 签名解锁、刷 system / vendor_boot 镜像 |
| **关于 / 更新** (Concerning) | 版本信息与在线自动更新（GitHub Releases，含 SHA256 校验） |

---

## 运行环境

| 项目 | 要求 |
|------|------|
| Python | 3.10+ |
| 操作系统 | Windows 10+ / Ubuntu 20.04+ |
| ADB 工具 | 外置于 `platform-tools/` 目录（应用会自动检测） |

---

## 安装与运行

### 1. 克隆仓库

```bash
git clone https://github.com/huguangyin1997-collab/GMStools.git
cd GMStools
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

| 库 | 版本 | 用途 |
|----|------|------|
| pyqt6 | 6.10.2 | GUI 框架 |
| openpyxl | 3.1.5 | Excel 读写（报告导出 / CTS Verifier DB） |
| beautifulsoup4 | 4.14.3 | HTML 解析（模块对比、SMR 对比） |
| Pillow | 12.1.1 | 图片处理（图标、背景图） |
| cryptography | ≥42.0.0 | RSA-SHA256 签名（展讯设备解锁） |

### 3. 确保外置工具就位

```
GMStools/
├── platform-tools/
│   ├── linux/       ← adb, fastboot, sqlite3 等
│   └── windows/     ← adb.exe, fastboot.exe, AdbWinApi.dll 等
└── unlock/
    ├── fastboot / fastboot.exe   ← 解锁专用 fastboot
    ├── rsa4096_vbmeta*.pem       ← 各型号 RSA 签名私钥
    ├── signature.bin             ← 预置签名
    └── 刷机步骤.txt
```

> `platform-tools/` 和 `unlock/` 为外置目录，不参与代码打包。ADB 查找优先级：系统 PATH → 同级 `platform-tools/` 目录。

### 4. 运行

```bash
python app_controller.py
```

首次启动会展示免责声明，须阅读并同意后方可进入主界面。

---

## 打包发布

```bash
pip install pyinstaller
python build_all_platforms.py
```

输出位于 `release_windows/` 或 `release_linux/`，解压后确保 `platform-tools/` 和 `unlock/` 与主程序同级。

---

## 项目架构

```
GMStools/
├── app_controller.py           # 应用入口（单例检查）
├── window_manager.py           # 无边框主窗口
├── PageManager.py              # 页面导航（左侧菜单 ↔ QStackedWidget）
├── left_menu.py                # 左侧菜单栏（初音主题）
├── BackgroundManager.py        # 背景图管理
├── usekey.py                   # HMAC-SHA256 免责声明签名
├── config.ini                  # 用户配置（运行时生成）
├── build_all_platforms.py      # 多平台 PyInstaller 打包
├── GMStools.spec               # PyInstaller spec
│
├── CustomTitle/                # 自定义标题栏
│   ├── customtitlebar.py
│   └── titleWindowControlButtons.py
│
├── theme/                      # 主题系统
│   └── miku_theme.py           # Miku 主题色 (#39C5BB) 与 QSS 样式
│
└── pages/                      # 功能页面（9 个模块）
    ├── Autounlock/             # 解锁与镜像刷入
    ├── CheckupReport/          # 体检报告分析
    ├── Concerning/             # 关于 / 在线更新
    ├── Ctsverifierdb/          # CTS Verifier 数据库
    ├── CVAutomation/           # CV 自动化
    ├── Disclaimer/             # 免责声明
    ├── Modulecomparison/       # 模块对比
    ├── Newfeatures/            # 新功能展示
    └── SMRComparison/          # SMR 对比（最复杂模块，约 20 个源文件）
```

### 关键设计

- **单例模式**: 通过 `QSharedMemory` 防止多开
- **无边框窗口**: 自定义标题栏实现窗口拖拽与最小化/最大化/关闭
- **统一主题**: `theme/miku_theme.py` 定义全局色彩常量，各页面通过函数获取 QSS 样式
- **免责保护**: 首次必须同意免责声明，HMAC-SHA256 签名存 `config.ini`，防篡改
- **多平台**: 自动检测 OS 选择对应 ADB 路径和路径分隔符
- **在线更新**: 通过 GitHub Releases API 检查新版本，支持 SHA256 校验、下载、解压、替换、重启

---

## 联系方式

- **GitHub**: [huguangyin1997-collab/GMStools](https://github.com/huguangyin1997-collab/GMStools)
- **问题反馈**: 请在 GitHub Issues 提交

---

## 许可证

[Apache License 2.0](LICENSE)