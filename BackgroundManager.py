from PyQt6.QtGui import QPixmap, QBrush, QColor, QLinearGradient
from PyQt6.QtCore import Qt, QPoint
import os
import sys

class BackgroundManager:
    """背景管理器 - 专门负责背景图片的加载和显示控制"""
    
    def __init__(self, window):
        """初始化背景管理器
        
        Args:
            window: 主窗口实例，用于设置背景
        """
        self.window = window  # 保存窗口引用
        self.background_pixmap = None  # 背景图片对象
    
    def get_resource_path(self, relative_path):
        """获取资源的绝对路径，支持开发环境和打包环境"""
        try:
            # PyInstaller创建的临时文件夹
            base_path = sys._MEIPASS
        except Exception:
            # 开发环境
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        return os.path.join(base_path, relative_path)
    
    def load_background_image(self, image_path="Miku.jpg"):
        """加载背景图片 - 增强错误处理
        
        Args:
            image_path: 背景图片路径，默认为"初音未来图片"
        """
        # 获取资源的绝对路径（支持打包环境）
        image_path = self.get_resource_path(image_path)
        
        print(f"尝试加载背景图片: {image_path}")
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            print(f"❌ 背景图片不存在: {image_path}")
            self.create_miku_style_gradient()  # 创建初音未来风格的渐变背景
            return
        
        # 从指定路径加载图片
        self.background_pixmap = QPixmap(image_path)
        
        # 检查图片是否加载成功
        if self.background_pixmap.isNull():
            print(f"❌ 背景图片加载失败: {image_path}")
            # 图片加载失败，创建备用背景
            self.create_miku_style_gradient()
        else:
            print(f"✓ 背景图片加载成功: {image_path}")
            # 图片加载成功，进行缩放处理以适应窗口
            self.background_pixmap = self.background_pixmap.scaled(
                self.window.width(),                    # 缩放至窗口宽度
                self.window.height(),                   # 缩放至窗口高度
                Qt.AspectRatioMode.KeepAspectRatio,     # 保持宽高比
                Qt.TransformationMode.SmoothTransformation  # 使用平滑变换
            )
    
    def create_miku_style_gradient(self):
        """创建初音未来风格的渐变背景"""
        print("创建初音未来风格渐变背景...")
        
        # 创建一个与窗口同尺寸的QPixmap
        self.background_pixmap = QPixmap(self.window.width(), self.window.height())
        
        # 创建渐变画刷
        gradient = QLinearGradient(QPoint(0, 0), QPoint(0, self.window.height()))
        
        # 初音未来主题色：蓝绿色渐变
        gradient.setColorAt(0.0, QColor(57, 197, 187))   # 浅蓝绿
        gradient.setColorAt(0.5, QColor(39, 174, 96))    # 绿色
        gradient.setColorAt(1.0, QColor(41, 128, 185))   # 蓝色
        
        # 填充背景
        self.background_pixmap.fill(Qt.GlobalColor.transparent)
        
        from PyQt6.QtGui import QPainter
        painter = QPainter(self.background_pixmap)
        painter.fillRect(0, 0, self.window.width(), self.window.height(), gradient)
        painter.end()
        
        print("✓ 已创建初音未来风格渐变背景")
    
    def create_fallback_background(self):
        """创建备用渐变背景（当图片加载失败时使用）"""
        print("创建备用渐变背景...")
        # 创建一个与窗口同尺寸的QPixmap
        self.background_pixmap = QPixmap(self.window.width(), self.window.height())
        
        # 创建渐变
        from PyQt6.QtGui import QLinearGradient, QPainter
        gradient = QLinearGradient(0, 0, 0, self.window.height())
        gradient.setColorAt(0.0, QColor(52, 152, 219))   # 蓝色
        gradient.setColorAt(1.0, QColor(41, 128, 185))   # 深蓝色
        
        # 填充渐变
        self.background_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self.background_pixmap)
        painter.fillRect(0, 0, self.window.width(), self.window.height(), gradient)
        painter.end()
        
        print("✓ 已创建备用渐变背景")
    
    def apply_background(self):
        """应用背景到窗口"""
        if self.background_pixmap is None:
            print("❌ 没有可用的背景图片")
            return
        
        # 获取窗口的调色板
        palette = self.window.palette()
        # 设置窗口背景为加载的图片或备用背景
        palette.setBrush(palette.ColorRole.Window, QBrush(self.background_pixmap))
        # 将调色板应用到窗口
        self.window.setPalette(palette)
        print("✓ 背景已应用到窗口")