
import os
import sys
import platform
import subprocess
import shutil
import zipfile
import urllib.request
from pathlib import Path

# ==================== ADB自动下载函数 ====================
def download_adb_windows():
    """自动下载Windows ADB工具"""
    current_dir = Path(__file__).parent
    target_dir = current_dir / "platform-tools" / "windows"
    
    if target_dir.exists() and (target_dir / "adb.exe").exists():
        print("✓ ADB工具已存在")
        return True
    
    print("\n📥 正在下载ADB工具...")
    print("   从Google官方服务器下载，请稍候...")
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    adb_url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    zip_path = current_dir / "platform-tools-windows.zip"
    
    try:
        urllib.request.urlretrieve(adb_url, zip_path)
        print(f"✓ 下载完成: {zip_path.name}")
        
        print("📦 解压文件中...")
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(current_dir)
        
        extracted_dir = current_dir / "platform-tools"
        if extracted_dir.exists():
            for file in extracted_dir.iterdir():
                target_file = target_dir / file.name
                if file.is_file():
                    shutil.move(str(file), str(target_file))
            shutil.rmtree(extracted_dir)
        
        zip_path.unlink()
        
        if (target_dir / "adb.exe").exists():
            print("✓ ADB工具下载并安装成功!")
            return True
        else:
            print("❌ ADB工具安装失败")
            return False
            
    except Exception as e:
        print(f"❌ 下载ADB工具失败: {e}")
        print("   请手动下载ADB工具放置到 platform-tools/windows/ 目录")
        return False

def check_environment():
    """检查打包环境"""
    current_dir = Path(__file__).parent
    print("=" * 60)
    print("检查打包环境")
    print("=" * 60)
    
    required_files = [
        "app_controller.py",
        "Miku.jpg",
        "CustomTitle/__init__.py",
        "pages/__init__.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (current_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少以下必要文件:")
        for f in missing_files:
            print(f"   - {f}")
        return False
    
    print("✓ 所有必要文件都存在")
    
    try:
        import PyInstaller
        print(f"✓ PyInstaller 已安装: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller 未安装，请运行: pip install pyinstaller")
        return False
    
    return True

def prepare_icon(current_dir):
    """准备图标文件，返回图标路径；若失败则抛出异常"""
    icon_file = None
    
    current_os = platform.system()
    if current_os == "Windows":
        icon_candidates = ["app.ico", "miku_icon.ico", "app_icon.ico", "icon.ico", "GMStools.ico"]
    else:
        icon_candidates = ["app.png", "app.ico", "miku_icon.ico", "app_icon.ico", "icon.ico", "GMStools.png"]
    
    for icon_name in icon_candidates:
        icon_path = current_dir / icon_name
        if icon_path.exists():
            icon_file = str(icon_path)
            print(f"✓ 找到现有图标: {icon_name}")
            break
    
    if icon_file is None:
        miku_path = current_dir / "Miku.jpg"
        if miku_path.exists():
            try:
                from PIL import Image
                print("🎨 从 Miku.jpg 生成图标...")
                img = Image.open(miku_path)
                img = img.convert("RGBA")
                
                if current_os == "Windows":
                    icon_output = current_dir / "app.ico"
                    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                    img.save(icon_output, format="ICO", sizes=sizes)
                    icon_file = str(icon_output)
                    print(f"✓ 已生成 ICO 图标: app.ico")
                else:
                    icon_output = current_dir / "app.png"
                    img.save(icon_output, format="PNG")
                    icon_file = str(icon_output)
                    print(f"✓ 已生成 PNG 图标: app.png")
            except ImportError:
                print("\n" + "=" * 60)
                print("❌ 图标准备失败：Pillow 未安装")
                print("=" * 60)
                print("请运行以下命令安装 Pillow：")
                print("    pip install pillow")
                print("\n或者手动放置一个有效的图标文件：")
                print("    Windows: app.ico")
                print("    Linux:   app.png")
                raise RuntimeError("Pillow 未安装，无法生成图标")
            except Exception as e:
                print(f"⚠️ 无法生成图标: {e}")
                raise RuntimeError(f"图标生成失败: {e}")
    
    if icon_file is None:
        raise RuntimeError(
            "❌ 无法找到或生成图标文件！\n"
            "请确保 Miku.jpg 存在并安装 Pillow，或手动放置 app.ico/app.png。"
        )
    
    return icon_file

def verify_exe_content(exe_path):
    """验证EXE文件中是否包含ADB工具和图标文件"""
    import zipfile
    
    print("\n🔍 验证EXE内容...")
    
    try:
        with zipfile.ZipFile(exe_path, 'r') as zf:
            files = zf.namelist()
            
            adb_files = []
            for f in files:
                if 'adb.exe' in f.lower() or 'adbwin' in f.lower():
                    adb_files.append(f)
            
            if adb_files:
                print(f"  ✓ EXE中包含ADB工具: {len(adb_files)} 个文件")
                for f in sorted(adb_files)[:3]:
                    print(f"    - {f}")
            else:
                print("  ❌ EXE中未找到ADB工具!")
            
            if any('miku.jpg' in f.lower() for f in files):
                print("  ✓ EXE中包含Miku.jpg")
            else:
                print("  ❌ EXE中未找到Miku.jpg!")
            
            if any('app.ico' in f.lower() for f in files):
                print("  ✓ EXE中包含app.ico（运行时图标）")
            else:
                print("  ❌ EXE中未找到app.ico！运行时图标将无法显示！")
                
    except Exception as e:
        print(f"  ⚠️ 无法验证EXE内容: {e}")

# ==================== Windows 打包 ====================
def build_windows_version():
    """构建 Windows 版本 - 单文件模式，所有资源打包进EXE"""
    current_dir = Path(__file__).parent
    print("\n" + "=" * 60)
    print("构建 Windows 版本（单文件模式）")
    print("=" * 60)
    
    if not download_adb_windows():
        print("❌ ADB工具准备失败，无法继续打包")
        return False, None
    
    for dir_name in ["build", "dist"]:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    # 准备图标（如果失败会抛出异常，终止打包）
    icon_file = prepare_icon(current_dir)
    
    platform_tools_dir = current_dir / "platform-tools" / "windows"
    if not platform_tools_dir.exists():
        print("❌ 错误: Windows 平台工具目录不存在")
        return False, None
    else:
        adb_exe = platform_tools_dir / "adb.exe"
        if adb_exe.exists():
            print(f"✓ 找到 ADB 工具: {adb_exe}")
            try:
                result = subprocess.run([str(adb_exe), "version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version_line = result.stdout.splitlines()[0] if result.stdout else "未知版本"
                    print(f"  ADB 版本: {version_line[:100]}")
            except:
                pass
        else:
            print("❌ 未找到 adb.exe")
            return False, None
    
    # 构建 PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "app_controller.py",
        "--name", "GMStools",
        "--add-data", "Miku.jpg;.",
        "--add-data", "app.ico;.",          # 关键：将图标作为数据文件打包进EXE
        "--add-data", "CustomTitle;CustomTitle",
        "--add-data", "pages;pages",
    ]
    
    # 打包ADB工具
    if platform_tools_dir.exists():
        cmd.extend(["--add-data", f"{platform_tools_dir};platform-tools/windows"])
        print(f"✓ 已打包ADB工具到EXE: platform-tools/windows")
        
        adb_exe = platform_tools_dir / "adb.exe"
        if adb_exe.exists():
            cmd.extend(["--add-data", f"{adb_exe};."])
            print(f"✓ 已打包adb.exe到EXE根目录")
        
        for dll in ["AdbWinApi.dll", "AdbWinUsbApi.dll"]:
            dll_file = platform_tools_dir / dll
            if dll_file.exists():
                cmd.extend(["--add-data", f"{dll_file};."])
                print(f"✓ 已打包{dll}到EXE根目录")
    
    # 隐藏导入
    hidden_imports = [
        "app_controller", "BackgroundManager", "left_menu", "PageManager",
        "window_manager", "usekey", "pages.CheckupReport", "pages.Concerning",
        "pages.Ctsverifierdb", "pages.CVAutomation", "pages.Disclaimer",
        "pages.Modulecomparison", "pages.SMRComparison",
        "CustomTitle.customtitlebar", "CustomTitle.titleWindowControlButtons",
        "pages.Ctsverifierdb.device_manager", "pages.Ctsverifierdb.main_window",
        "pages.Ctsverifierdb.device_monitor", "pages.Ctsverifierdb.test_manager",
        "pages.Ctsverifierdb.result_parser", "pages.Ctsverifierdb.report_generator"
    ]
    for mod in hidden_imports:
        cmd.extend(["--hidden-import", mod])
    
    cmd.extend([
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
    ])
    
    if "--debug" in sys.argv:
        cmd.remove("--windowed")
        cmd.append("--console")
        print("🔧 调试模式：启用控制台")
    
    # 添加图标参数（静态EXE图标）
    if icon_file:
        cmd.extend(["--icon", icon_file])
        print(f"📦 将使用静态图标: {Path(icon_file).name}")
    else:
        print("⚠️ 未找到图标文件，将使用默认图标")
    
    print("\n执行命令:", " ".join(cmd[:8]) + " ...")
    
    try:
        result = subprocess.run(cmd, check=True, cwd=current_dir, 
                              capture_output=True, text=True, encoding='utf-8')
        print("✓ Windows 版本打包成功!")
        
        exe_path = current_dir / "dist" / "GMStools.exe"
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024*1024)
            print(f"Windows 可执行文件: {exe_path}")
            print(f"文件大小: {file_size:.2f} MB")
            verify_exe_content(exe_path)
            print("\n✓ 使用单文件打包模式，所有资源已嵌入EXE")
            return True, exe_path
        else:
            print("❌ Windows 可执行文件未生成")
            return False, None
            
    except subprocess.CalledProcessError as e:
        print("❌ Windows 版本打包失败!")
        print(f"错误输出: {e.stderr}")
        print("\n🔧 常见问题排查:")
        print("1. 检查是否有杀毒软件拦截")
        print("2. 尝试以管理员权限运行")
        print("3. 检查 Python 环境: python --version")
        print("4. 检查 PyInstaller 版本: pip show pyinstaller")
        return False, None
    except Exception as e:
        print(f"❌ Windows 版本打包过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False, None

# ==================== Linux 打包（保持不变，但可添加图标数据文件）====================
def build_linux_version():
    """构建 Linux 版本"""
    current_dir = Path(__file__).parent
    print("\n" + "=" * 60)
    print("构建 Linux 版本")
    print("=" * 60)
    
    for dir_name in ["build", "dist"]:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    # 准备图标（Linux 下通常使用 PNG）
    icon_file = prepare_icon(current_dir)
    
    platform_tools_dir = current_dir / "platform-tools" / "linux"
    if not platform_tools_dir.exists():
        print("⚠️  注意: Linux 平台工具目录不存在")
        print("   请确保 platform-tools/linux 目录包含 ADB 工具")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "app_controller.py",
        "--name", "GMStools",
        "--add-data", "Miku.jpg:.",
        "--add-data", "CustomTitle:CustomTitle",
        "--add-data", "pages:pages",
    ]
    
    # 如果需要 Linux 运行时图标，取消下一行注释并将 app.ico 替换为 app.png
    # cmd.extend(["--add-data", "app.png:."])
    
    if platform_tools_dir.exists():
        cmd.extend(["--add-data", f"{platform_tools_dir}:platform-tools/linux"])
    
    hidden_imports = [
        "app_controller", "BackgroundManager", "left_menu", "PageManager",
        "window_manager", "usekey","pages.CheckupReport", "pages.Concerning",
        "pages.Ctsverifierdb", "pages.CVAutomation", "pages.Disclaimer",
        "pages.Modulecomparison", "pages.SMRComparison",
        "CustomTitle.customtitlebar", "CustomTitle.titleWindowControlButtons",
        "pages.Ctsverifierdb.device_manager", "pages.Ctsverifierdb.main_window",
        "pages.Ctsverifierdb.device_monitor", "pages.Ctsverifierdb.test_manager",
        "pages.Ctsverifierdb.result_parser", "pages.Ctsverifierdb.report_generator"
    ]
    for mod in hidden_imports:
        cmd.extend(["--hidden-import", mod])
    
    cmd.extend([
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
    ])
    
    if icon_file:
        cmd.extend(["--icon", icon_file])
        print(f"📦 将使用图标: {Path(icon_file).name}")
    else:
        print("⚠️ 未找到图标文件，将使用默认图标")
    
    print("\n执行命令:", " ".join(cmd[:8]) + " ...")
    
    try:
        result = subprocess.run(cmd, check=True, cwd=current_dir, 
                              capture_output=True, text=True)
        print("✓ Linux 版本打包成功!")
        
        exe_path = current_dir / "dist" / "GMStools"
        if exe_path.exists():
            os.chmod(exe_path, 0o755)
            file_size = exe_path.stat().st_size / (1024*1024)
            print(f"Linux 可执行文件: {exe_path}")
            print(f"文件大小: {file_size:.2f} MB")
            print("\n✓ 使用单文件打包模式，所有资源已嵌入")
            return True, exe_path
        else:
            print("❌ Linux 可执行文件未生成")
            return False, None
            
    except subprocess.CalledProcessError as e:
        print("❌ Linux 版本打包失败!")
        print(f"错误输出: {e.stderr}")
        return False, None
    except Exception as e:
        print(f"❌ Linux 版本打包过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False, None

# ==================== Windows 发布目录创建 ====================
def create_windows_release_directory(exe_path):
    """创建 Windows 发布目录"""
    current_dir = Path(__file__).parent
    
    release_dir = current_dir / "release_windows"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    print(f"✓ 已创建 Windows 发布目录: {release_dir}")
    
    if exe_path and exe_path.exists():
        target_exe = release_dir / "GMStools.exe"
        shutil.copy2(exe_path, target_exe)
        print("✓ 已复制可执行文件: release_windows/GMStools.exe")
    else:
        print("⚠️ 未找到可执行文件")
        return release_dir
    
    miku_src = current_dir / "Miku.jpg"
    if miku_src.exists():
        shutil.copy2(miku_src, release_dir / "Miku.jpg")
        print("✓ 已复制 Miku.jpg")
    
    platform_tools_src = current_dir / "platform-tools" / "windows"
    if platform_tools_src.exists():
        platform_tools_dst = release_dir / "platform-tools"
        if platform_tools_dst.exists():
            shutil.rmtree(platform_tools_dst)
        shutil.copytree(platform_tools_src, platform_tools_dst)
        print("✓ 已复制 Windows 平台工具")
    
    bat_content = """@echo off
chcp 65001 >nul
echo.
echo ========================================
echo         GMStools - Windows 版本
echo ========================================
echo.
echo 正在启动 GMStools...
echo.

set PATH=%CD%\\platform-tools;%PATH%
start "" "GMStools.exe"

echo.
echo 程序已启动！
pause
"""
    with open(release_dir / "启动GMStools.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)
    print("✓ 已创建启动脚本: 启动GMStools.bat")
    
    # 卸载脚本...
    uninstall_bat = release_dir / "卸载GMStools.bat"
    uninstall_content = """@echo off
chcp 65001 >nul
echo.
echo ========================================
echo         GMStools 卸载工具
echo ========================================
echo.
echo 这将删除 GMStools 及其相关文件。
echo.
set /p confirm="确定要卸载吗？(输入 Y 确认): "
if /i "%confirm%" neq "Y" (
    echo 取消卸载。
    pause
    exit /b
)
echo.
echo 正在卸载 GMStools...
echo.

if exist "GMStools.exe" (
    del "GMStools.exe"
    echo 已删除: GMStools.exe
)
for %%f in (Miku.jpg, GMStools.spec, *.log) do (
    if exist "%%f" (
        del "%%f"
        echo 已删除: %%f
    )
)
if exist "platform-tools" (
    rmdir /s /q "platform-tools"
    echo 已删除: platform-tools 目录
)
echo.
echo ✓ GMStools 已成功卸载！
echo.
pause
"""
    with open(uninstall_bat, "w", encoding="utf-8") as f:
        f.write(uninstall_content)
    print("✓ 已创建卸载脚本: 卸载GMStools.bat")
    
    readme_content = """GMStools Windows 版本

📁 文件说明:
├── GMStools.exe          - 主程序（双击运行）- 已包含ADB工具
├── 启动GMStools.bat      - 启动脚本（推荐使用）
├── 卸载GMStools.bat      - 卸载脚本
├── Miku.jpg             - 背景图片（备用）
├── platform-tools/      - ADB工具和驱动（备用）
└── README.txt           - 本文件

🚀 使用方法:
直接双击 GMStools.exe 即可运行，无需额外安装ADB！

📦 特性:
- ✅ ADB工具已打包进EXE文件，无需外部依赖
- ✅ 单文件设计，便携易用
- ✅ 自动识别设备，开箱即用

⚠️  注意事项:
1. 首次运行时，Windows Defender 可能会提示
   选择"更多信息" -> "仍要运行"
2. 某些功能可能需要管理员权限
   可以右键点击 -> "以管理员身份运行"
"""
    with open(release_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("✓ 已创建 README.txt")
    
    print("\n" + "=" * 60)
    print("创建 Windows 发布压缩包")
    print("=" * 60)
    
    try:
        zip_name = "GMStools-windows.zip"
        zip_path = current_dir / zip_name
        
        print(f"📦 创建 ZIP 包: {zip_name}")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in release_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(release_dir.parent)
                    zipf.write(file_path, arcname)
        
        zip_size = zip_path.stat().st_size / (1024*1024)
        print(f"✓ ZIP 创建成功: {zip_name}")
        print(f"✓ ZIP 大小: {zip_size:.2f} MB")
    except Exception as e:
        print(f"❌ 创建 ZIP 时出错: {e}")
        print("请手动压缩 release_windows 文件夹为 ZIP")
    
    return release_dir

# ==================== Linux 发布目录创建 ====================
def create_linux_release_directory(exe_path):
    """创建 Linux 发布目录"""
    current_dir = Path(__file__).parent
    
    # 创建发布目录
    release_dir = current_dir / "release_linux"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    print(f"✓ 已创建 Linux 发布目录: {release_dir}")
    
    # 1. 复制 Linux 可执行文件
    if exe_path and exe_path.exists():
        target_exe = release_dir / "GMStools"
        shutil.copy2(exe_path, target_exe)
        os.chmod(target_exe, 0o755)
        print("✓ 已复制可执行文件: release_linux/GMStools")
    else:
        print("⚠️ 未找到可执行文件")
        return release_dir
    
    # 2. 复制 Miku.jpg（如果存在）
    miku_src = current_dir / "Miku.jpg"
    if miku_src.exists():
        shutil.copy2(miku_src, release_dir / "Miku.jpg")
        print("✓ 已复制 Miku.jpg")
    
    # 3. 处理图标文件
    icon_file = None
    
    # 首先检查已有的 PNG 图标
    png_icons = ["app.png", "icon.png", "GMStools.png", "logo.png"]
    for png_name in png_icons:
        png_path = current_dir / png_name
        if png_path.exists():
            shutil.copy2(png_path, release_dir / "icon.png")
            icon_file = release_dir / "icon.png"
            print(f"✓ 已复制 PNG 图标: {png_name}")
            break
    
    # 如果没有 PNG，尝试转换 ICO 为 PNG
    if not icon_file:
        ico_files = ["app.ico", "miku_icon.ico", "icon.ico", "GMStools.ico"]
        for ico_name in ico_files:
            ico_path = current_dir / ico_name
            if ico_path.exists():
                try:
                    from PIL import Image
                    print(f"🎨 将 {ico_name} 转换为 PNG 格式...")
                    
                    img = Image.open(ico_path)
                    best_img = None
                    max_size = 0
                    
                    try:
                        for i in range(img.n_frames):
                            img.seek(i)
                            current_size = img.size[0] * img.size[1]
                            if current_size > max_size:
                                max_size = current_size
                                best_img = img.copy()
                    except:
                        best_img = img.copy()
                    
                    if best_img.mode != 'RGBA':
                        best_img = best_img.convert('RGBA')
                    
                    icon_file = release_dir / "icon.png"
                    best_img.save(icon_file, format="PNG")
                    print(f"✓ ICO 转换为 PNG 成功: {icon_file.name}")
                    break
                    
                except ImportError:
                    print("⚠️ PIL 未安装，无法转换 ICO 文件")
                    break
                except Exception as e:
                    print(f"⚠️ 转换 {ico_name} 失败: {e}")
                    continue
    
    # 4. 如果还没有图标，从 Miku.jpg 生成
    if not icon_file:
        miku_path = current_dir / "Miku.jpg"
        if miku_path.exists():
            try:
                from PIL import Image
                print("🎨 从 Miku.jpg 生成图标...")
                
                img = Image.open(miku_path)
                max_size = max(img.size)
                square_img = Image.new('RGBA', (max_size, max_size), (255, 255, 255, 0))
                paste_x = (max_size - img.size[0]) // 2
                paste_y = (max_size - img.size[1]) // 2
                square_img.paste(img, (paste_x, paste_y))
                
                icon_file = release_dir / "icon.png"
                square_img.save(icon_file, format="PNG")
                
                print(f"✓ 从 Miku.jpg 生成图标: {icon_file.name}")
            except ImportError:
                print("⚠️ PIL 未安装，无法从 Miku.jpg 生成图标")
            except Exception as e:
                print(f"⚠️ 无法从 Miku.jpg 生成图标: {e}")
    
    # 5. 创建 .desktop 文件
    desktop_path = release_dir / "GMStools.desktop"
    
    icon_path = "icon.png" if icon_file and icon_file.exists() else ""
    
    desktop_content = f"""[Desktop Entry]
Type=Application
Name=GMStools
GenericName=Android ADB Tools
Comment=Complete ADB tools with Miku theme
Exec=./GMStools
Icon={icon_path}
Terminal=false
Categories=Utility;Development;
Keywords=adb;android;tools;miku;
StartupNotify=true
X-AppImage-Version=1.0
"""
    
    with open(desktop_path, "w", encoding="utf-8") as f:
        f.write(desktop_content)
    os.chmod(desktop_path, 0o755)
    print("✓ 已创建 .desktop 文件")
    print("  注意: 在文件管理器中右键此文件 -> 允许启动")
    
    # 6. 创建安装脚本
    install_script = release_dir / "install.sh"
    install_content = """#!/bin/bash

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
            sed -e "s|Exec=.*|Exec=$HOME/.local/bin/GMStools|" \
                -e "s|Icon=.*|Icon=gmstools|" \
                GMStools.desktop > ~/.local/share/applications/GMStools.desktop
        fi
        
        # 更新桌面数据库
        update-desktop-database ~/.local/share/applications 2>/dev/null || true
        
        echo "✓ 用户安装完成！"
        echo "   现在可以在终端中输入 'GMStools' 运行"
        echo "   或在应用菜单中搜索 'GMStools'"
        echo ""
        echo "注意: 如果 'GMStools' 命令不可用，请重启终端或运行:"
        echo "      export PATH=\"$HOME/.local/bin:$PATH\""
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
"""
    
    with open(install_script, "w", encoding="utf-8") as f:
        f.write(install_content)
    os.chmod(install_script, 0o755)
    print("✓ 已创建安装脚本: install.sh")
    
    # 7. 创建卸载脚本
    uninstall_script = release_dir / "uninstall.sh"
    uninstall_content = """#!/bin/bash

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
"""
    
    with open(uninstall_script, "w", encoding="utf-8") as f:
        f.write(uninstall_content)
    os.chmod(uninstall_script, 0o755)
    print("✓ 已创建卸载脚本: uninstall.sh")
    
    # 8. 创建 README 文件
    readme_content = """GMStools Ubuntu/Linux 版本

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
"""
    
    with open(release_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("✓ 已创建 README.txt")
    
    # 9. 创建 ZIP 压缩包
    print("\n" + "=" * 60)
    print("创建 Linux 发布压缩包")
    print("=" * 60)

    try:
        zip_name = "GMStools-linux.zip"
        zip_path = current_dir / zip_name

        print(f"📦 创建 ZIP 包: {zip_name}")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in release_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(release_dir.parent)
                    zipf.write(file_path, arcname)

        zip_size = zip_path.stat().st_size / (1024*1024)
        print(f"✓ ZIP 创建成功: {zip_name}")
        print(f"✓ ZIP 大小: {zip_size:.2f} MB")

    except Exception as e:
        print(f"❌ 创建 ZIP 时出错: {e}")
        print("请手动压缩 release_linux 文件夹为 ZIP")
    
    # 10. 总结信息
    print("\n" + "=" * 60)
    print("✓ Linux 发布目录和压缩包创建完成！")
    print("=" * 60)
    
    print(f"\n📂 发布目录: {release_dir}")
    
    # 列出生成的文件
    print("\n📋 发布目录内容:")
    release_items = list(release_dir.iterdir())
    for item in sorted(release_items, key=lambda x: x.name):
        if item.is_file():
            size = item.stat().st_size / 1024
            print(f"  - {item.name:25} ({size:6.1f} KB)")
    
    # 列出压缩包
    print("\n📦 生成的压缩包:")
    zip_file = current_dir / "GMStools-linux.zip"
    if zip_file.exists():
        size_mb = zip_file.stat().st_size / (1024*1024)
        print(f"  - {zip_file.name} ({size_mb:.2f} MB)")
    
    print("\n🎯 分发和使用:")
    print("1. 将 GMStools-linux.zip 分发给其他 Linux 用户")
    print("2. 用户解压: unzip GMStools-linux.zip")
    print("3. 进入目录: cd release_linux/")
    print("4. 运行安装: chmod +x install.sh && ./install.sh")
    
    return release_dir

# ==================== 主函数 ====================
def main():
    print("=" * 60)
    print("GMStools 多平台打包脚本")
    print("支持 Windows 和 Linux 平台")
    print("=" * 60)
    
    current_os = platform.system()
    print(f"\n当前操作系统: {current_os}")
    
    if not check_environment():
        print("\n❌ 环境检查失败")
        sys.exit(1)
    
    if current_os == "Windows":
        print("\n" + "=" * 60)
        print("构建 Windows 版本（单文件模式，ADB内嵌，图标已打包）...")
        print("=" * 60)
        
        success, exe_path = build_windows_version()
        
        if success:
            print("\n" + "=" * 60)
            print("创建 Windows 发布目录...")
            print("=" * 60)
            release_dir = create_windows_release_directory(exe_path)
            
            if release_dir:
                print("\n" + "=" * 60)
                print("✓ Windows 打包完成!")
                print("=" * 60)
                
                zip_file = Path(__file__).parent / "GMStools-windows.zip"
                if zip_file.exists():
                    size_mb = zip_file.stat().st_size / (1024*1024)
                    print(f"\n📦 发布包: {zip_file.name}")
                    print(f"📏 大小: {size_mb:.2f} MB")
                    print(f"📂 包含: {release_dir.name} 目录")
                    print("\n🎯 下一步:")
                    print("1. 分发文件: GMStools-windows.zip")
                    print("2. Windows 用户解压后直接双击 GMStools.exe")
                    print("3. ADB工具已内嵌，图标已内置，无需额外配置")
                else:
                    print(f"\n📂 发布文件位于: {release_dir}")
                    print("   请手动压缩此目录为 ZIP 文件")
            else:
                print("❌ 创建发布目录失败")
                sys.exit(1)
        else:
            print("\n❌ Windows 版本打包失败")
            sys.exit(1)
            
    elif current_os == "Linux":
        print("\n" + "=" * 60)
        print("构建 Linux 版本...")
        print("=" * 60)
        
        success, exe_path = build_linux_version()
        
        if success:
            print("\n" + "=" * 60)
            print("创建 Linux 发布目录...")
            print("=" * 60)
            release_dir = create_linux_release_directory(exe_path)
            
            if release_dir:
                print("\n" + "=" * 60)
                print("✓ Linux 打包完成!")
                print("=" * 60)
                
                zip_file = Path(__file__).parent / "GMStools-linux.zip"
                if zip_file.exists():
                    size_mb = zip_file.stat().st_size / (1024*1024)
                    print(f"\n📦 发布包: {zip_file.name}")
                    print(f"📏 大小: {size_mb:.2f} MB")
                    print(f"📂 包含: {release_dir.name} 目录")
                    print("\n🎯 下一步:")
                    print("1. 分发文件: GMStools-linux.zip")
                    print("2. Linux 用户解压后运行 install.sh")
                    print("3. 在应用菜单中搜索 'GMStools'")
                else:
                    print(f"\n📂 发布文件位于: {release_dir}")
                    print("   请手动压缩此目录为 ZIP 文件")
            else:
                print("❌ 创建发布目录失败")
                sys.exit(1)
        else:
            print("\n❌ Linux 版本打包失败")
            sys.exit(1)
    else:
        print(f"❌ 不支持的操作系统: {current_os}")
        print("仅支持 Windows 和 Linux 系统")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n打包已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)