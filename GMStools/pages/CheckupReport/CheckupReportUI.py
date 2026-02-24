from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
                            QPushButton, QLineEdit, QTextEdit, QProgressBar,
                            QFrame, QMenu)
from PyQt6.QtGui import QFont, QAction, QTextCursor
from PyQt6.QtCore import Qt
from .CustomComboBox import CustomComboBox
import os
import base64
import re

class CheckupReportUI(QWidget):
    """检查报告页面UI - 修复按钮选中状态显示问题"""
    
    def __init__(self):
        super().__init__()
        # 错误状态存储：{错误块标识: "pending"/"passed"/"failed"}
        self.error_status = {}
        # 存储图片的Base64编码
        self.image_base64 = {}
        # 分隔符
        self.delimiter = "=" * 100
        # 存储原始错误文本
        self.original_error_text = ""
        # 存储错误块标识符映射
        self.error_block_identifiers = {}
        # 跟踪分析状态
        self.is_analyzing = False
        self.setup_ui()
        self.setup_connections()
        # 加载图片
        self.load_images()
    
    def load_images(self):
        """加载图片并转换为Base64编码"""
        image_files = {
            "pending": "Pending.png",
            "passed": "CheckPASS.png", 
            "failed": "CheckFAIL.png"
        }
        
        for status, filename in image_files.items():
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            if os.path.exists(image_path):
                try:
                    with open(image_path, 'rb') as img_file:
                        img_data = img_file.read()
                        base64_data = base64.b64encode(img_data).decode('utf-8')
                        
                    # 根据图片类型设置MIME类型
                    if filename.lower().endswith('.png'):
                        mime_type = 'image/png'
                    else:
                        mime_type = 'image/png'  # 默认
                    
                    self.image_base64[status] = f"data:{mime_type};base64,{base64_data}"
                except Exception as e:
                    print(f"加载图片失败 {filename}: {e}")
                    self.image_base64[status] = None
            else:
                print(f"图片文件不存在: {image_path}")
                self.image_base64[status] = None
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # 创建目录选择区域
        directory_layout = self.create_directory_selection_area()
        layout.addLayout(directory_layout)
        
        # 创建进度条
        self.progress_bar = self.create_progress_bar()
        layout.addWidget(self.progress_bar)
        
        # 创建固定比例的内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分析结果区域（占3/5）
        result_frame = self.create_text_area_frame("分析结果 (完整信息):", True)
        self.result_text = result_frame.text_edit
        content_layout.addWidget(result_frame, 3)
        
        # 创建错误信息区域（占2/5）
        error_frame = self.create_text_area_frame("错误信息 (仅错误):", False)
        self.error_text = error_frame.text_edit
        content_layout.addWidget(error_frame, 2)
        
        layout.addLayout(content_layout, 1)
    
    def setup_connections(self):
        """设置信号连接"""
        # Android版本选择变化时更新检查状态
        self.android_version_combo.currentTextChanged.connect(self.update_apts_check_status)
        
        # 为错误文本区域设置右键菜单
        self.error_text.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.error_text.customContextMenuRequested.connect(self.show_error_context_menu)
        
        # 添加开始分析按钮的连接
        self.analyze_btn.clicked.connect(self.on_analyze_clicked)
        
        # 添加清空按钮的连接
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        
        # 监听目录路径变化
        self.directory_path.textChanged.connect(self.on_directory_path_changed)
    
    def on_analyze_clicked(self):
        """处理开始分析按钮点击 - 修复选中状态显示问题"""
        
        # 切换分析状态
        self.is_analyzing = not self.is_analyzing
        
        # 根据分析状态更新按钮
        if self.is_analyzing:
            # 开始分析 - 设置为选中状态（绿色背景）
            self.analyze_btn.setChecked(True)
            self.analyze_btn.setText("人工核对中...")
        else:
            # 停止分析 - 保持选中状态但改变文本
            self.analyze_btn.setChecked(True)  # 保持选中状态
            self.analyze_btn.setText("分析完成")

        
        # 强制更新样式
        self.force_button_style_update()
    
    def force_button_style_update(self):
        """强制更新按钮样式"""
        self.analyze_btn.style().unpolish(self.analyze_btn)
        self.analyze_btn.style().polish(self.analyze_btn)
        self.analyze_btn.update()
    
    def on_clear_clicked(self):
        """处理清空记录按钮点击 - 重置分析按钮状态"""
        self.clear_results()
        # 清空后重置分析按钮为未选中状态
        self.analyze_btn.setChecked(False)
        self.analyze_btn.setText("开始分析")
        self.is_analyzing = False
        # 强制更新样式
        self.force_button_style_update()
    
    def on_directory_path_changed(self, text):
        """处理目录路径变化 - 更新边框颜色"""
        has_directory = bool(text.strip())
        self.directory_path.setStyleSheet(self.get_line_edit_style(has_directory))
    
    def create_directory_selection_area(self):
        """创建目录选择区域"""
        directory_layout = QHBoxLayout()
        directory_layout.setSpacing(8)
        
        # 目录路径显示
        self.directory_path = QLineEdit()
        self.directory_path.setPlaceholderText("请选择报告目录...")
        self.directory_path.setReadOnly(True)
        self.directory_path.setFixedHeight(36)
        self.directory_path.setStyleSheet(self.get_line_edit_style(False))  # 初始为蓝色边框
        directory_layout.addWidget(self.directory_path, 1)
        
        # 选择目录按钮
        self.select_directory_btn = self.create_button("选择报告目录", 140)
        directory_layout.addWidget(self.select_directory_btn)
        
        # Android版本选择器
        android_versions = ["GO 版本", "FULL 版本"]
        self.android_version_combo = CustomComboBox(android_versions)
        self.android_version_combo.setFixedSize(140, 36)
        directory_layout.addWidget(self.android_version_combo)
        
        # 分析按钮 - 特别注意这里
        self.analyze_btn = QPushButton("开始分析")
        self.analyze_btn.setFixedSize(140, 36)
        self.analyze_btn.setCheckable(True)  # 确保设置为可选中
        self.analyze_btn.setStyleSheet(self.get_button_style())
        self.analyze_btn.setEnabled(False)
        directory_layout.addWidget(self.analyze_btn)
        
        # 清空记录按钮
        self.clear_btn = self.create_button("清空记录", 140)
        directory_layout.addWidget(self.clear_btn)
        
        return directory_layout
    
    def create_button(self, text, width):
        """创建统一风格的按钮"""
        button = QPushButton(text)
        button.setFixedSize(width, 36)
        button.setCheckable(True)
        button.setStyleSheet(self.get_button_style())
        return button
    
    def create_text_area_frame(self, title, is_result):
        """创建文本区域框架"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        
        # 创建标签
        label = QLabel(title)
        label.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold;")
        label.setContentsMargins(0, 0 if is_result else 0, 0, 3)
        layout.addWidget(label)
        
        # 创建文本框
        text_edit = self.create_text_edit(is_result)
        layout.addWidget(text_edit)
        
        # 将文本框保存为属性以便访问
        frame.text_edit = text_edit
        return frame
    
    def create_text_edit(self, is_result=True):
        """创建文本框 - 修复占位文本显示不完整问题"""
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # 专门针对占位文本的优化样式
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.8);
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
                color: #2c3e50;
                font-family: "Microsoft YaHei", "SimHei", monospace;
            }
            QTextEdit:focus {
                border: 2px solid #27ae60;
            }
            /* 专门针对占位文本的样式 */
            QTextEdit::placeholder {
                color: #7f8c8d;
                font-size: 11px;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
        """)
        
        # 设置合适的字体
        font = QFont("Microsoft YaHei", 10)  # 使用中文字体
        text_edit.setFont(font)
        text_edit.setTabStopDistance(100)
        
        # 设置占位文本
        if is_result:
            text_edit.setPlaceholderText("分析结果将显示在这里...")
        else:
            text_edit.setPlaceholderText("错误信息将显示在这里...")
            
        # 设置合适的高度
        text_edit.setMinimumHeight(200)
        
        return text_edit
    
    def create_progress_bar(self):
        """创建进度条"""
        progress_bar = QProgressBar()
        progress_bar.setVisible(False)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                color: #2c3e50;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        return progress_bar
    
    def get_button_style(self):
        """获取按钮样式 - 修复选中状态显示问题"""
        return """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
                color: white;
            }
            QPushButton:hover:checked {
                background-color: #219955;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2473a6;
                color: white;
            }
            QPushButton:pressed:checked {
                background-color: #1e8449;
                color: white;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QPushButton:disabled:checked {
                background-color: #27ae60;
                color: white;
            }
        """
    
    def get_line_edit_style(self, has_directory=False):
        """获取文本框样式"""
        if has_directory:
            return """
                QLineEdit {
                    background-color: white;
                    color: #2c3e50;
                    border: 2px solid #27ae60;
                    border-radius: 5px;
                    padding: 6px 12px;
                    font-size: 14px;
                }
            """
        else:
            return """
                QLineEdit {
                    background-color: white;
                    color: #2c3e50;
                    border: 2px solid #3498db;
                    border-radius: 5px;
                    padding: 6px 12px;
                    font-size: 14px;
                }
            """
    
    def get_status_text_style(self, has_output=False):
        """获取状态文本框样式"""
        if has_output:
            return """
                QTextEdit {
                    background-color: rgba(255, 255, 255, 0.8);
                    border: 2px solid #27ae60;
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 12px;
                    color: #2c3e50;
                    font-family: "Consolas", "Monaco", "Courier New", monospace;
                }
            """
        else:
            return """
                QTextEdit {
                    background-color: rgba(255, 255, 255, 0.8);
                    border: 2px solid #3498db;
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 12px;
                    color: #2c3e50;
                    font-family: "Consolas", "Monaco", "Courier New", monospace;
                }
            """
    
    def update_apts_check_status(self, version_text):
        """根据选择的Android版本更新APTS检查状态"""
        if version_text == "GO 版本":
            status_text = "当前模式：GO版本 - 将检查APTS报告"
            status_color = "#27ae60"  # 绿色
        elif version_text == "FULL 版本":
            status_text = "当前模式：FULL版本 - 不检查APTS报告"
            status_color = "#e74c3c"  # 红色
        else:
            status_text = "当前模式：默认 - 检查所有报告（包括APTS）"
            status_color = "#3498db"  # 蓝色
        
        # 在目录路径文本框下方显示状态提示
        self.directory_path.setPlaceholderText(f"{status_text} - 请选择报告目录...")
    
    def get_android_version_mode(self):
        """获取当前Android版本模式"""
        current_text = self.android_version_combo.currentText()
        if current_text == "GO 版本":
            return "GO"
        elif current_text == "FULL 版本":
            return "FULL"
        else:
            return "DEFAULT"  # 默认检查所有
    
    def should_check_apts(self):
        """根据当前选择的Android版本判断是否应该检查APTS"""
        mode = self.get_android_version_mode()
        if mode == "GO" or mode == "DEFAULT":
            return True
        elif mode == "FULL":
            return False
        return True  # 默认检查
    
    def set_analysis_state(self, enabled):
        """设置分析状态 - 修复分析完成后的状态显示"""
        self.select_directory_btn.setEnabled(enabled)
        self.analyze_btn.setEnabled(enabled)
        
        if enabled:
            # 分析完成或可重新分析时
            if self.is_analyzing:
                # 如果还在人工核对中，保持选中状态
                self.analyze_btn.setChecked(True)
                self.analyze_btn.setText("人工核对中")
            else:
                # 分析完成，保持选中状态但改变文本
                self.analyze_btn.setChecked(True)  # 保持选中状态
                self.analyze_btn.setText("分析完成")
        else:
            # 开始分析时设置为选中状态
            self.analyze_btn.setChecked(True)
            self.analyze_btn.setText("人工核对中")
            self.is_analyzing = True
        
        # 强制更新样式
        self.force_button_style_update()
    
    def clear_results(self):
        """清空分析结果和错误信息"""
        self.result_text.clear()
        self.result_text.setPlaceholderText("分析结果将显示在这里...")
        self.error_text.clear()
        self.error_text.setPlaceholderText("错误信息将显示在这里...")
        # 清空错误状态
        self.error_status.clear()
        self.original_error_text = ""
        self.error_block_identifiers.clear()
        
        # 重置文本框边框为默认蓝色
        self.result_text.setStyleSheet(self.get_status_text_style(False))
        self.error_text.setStyleSheet(self.get_status_text_style(False))
        
        # 重置目录路径边框为蓝色（如果没有目录）
        if not self.directory_path.text().strip():
            self.directory_path.setStyleSheet(self.get_line_edit_style(False))
    
    def update_results(self, full_results, error_results):
        """更新分析结果和错误信息"""
        self.result_text.setPlainText(full_results)
        
        # 保存原始错误文本
        self.original_error_text = error_results
        
        # 处理错误信息，添加图片
        formatted_errors = self.format_errors_with_status(error_results)
        self.error_text.setHtml(formatted_errors)  # 使用setHtml而不是setPlainText
        
        # 初始化所有错误块的状态为"pending"
        self.initialize_error_status(error_results)
        
        # 根据是否有内容更新文本框边框样式
        has_result_content = bool(full_results.strip())
        has_error_content = bool(error_results.strip()) and error_results != "没有发现错误"
        
        self.result_text.setStyleSheet(self.get_status_text_style(has_result_content))
        self.error_text.setStyleSheet(self.get_status_text_style(has_error_content))
    
    def format_errors_with_status(self, error_text):
        """根据错误状态格式化错误信息为HTML - 支持错误和警告"""
        if "没有发现错误" in error_text:
            return error_text
        
        # 按分隔符分割错误信息
        blocks = error_text.split(self.delimiter)
        formatted_blocks = []
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
                
            # 检查这个块是否包含错误信息或警告信息
            if any(marker in block for marker in ['❌', '⚠️']):
                # 这是一个错误或警告块，使用清理后的文本作为标识
                block_identifier = self.clean_error_text(block)
                    
                status = self.error_status.get(block_identifier, "pending")
                image_html = self.get_image_html(status)
                
                # 根据状态设置颜色
                color_style = ""
                if status == "passed":
                    color_style = "color: #27ae60;"  # 绿色
                    # 将❌和⚠️替换为✅
                    block = block.replace('❌', '✅').replace('⚠️', '✅')
                elif status == "failed":
                    color_style = "color: #e74c3c;"  # 红色
                    # 将❌和⚠️替换为❌（保持为❌，不替换为图片）
                    # 这样确保后续仍然可以识别这个错误块
                    block = block.replace('❌', '❌').replace('⚠️', '❌')
                else:  # pending
                    color_style = "color: #2c3e50;"  # 默认颜色
                    # 对于pending状态，确保使用原始符号
                    # 这里不需要替换，因为原始文本已经包含❌和⚠️
                
                # 添加图片和分隔符，然后添加处理后的块内容
                formatted_block = f"{image_html}{self.delimiter}\n<span style='{color_style}'>{block}</span>"
                formatted_blocks.append(formatted_block)
        
        # 在最后添加一个分隔符
        if formatted_blocks:
            formatted_blocks.append(self.delimiter)
        
        # 使用等宽字体显示
        html_content = "<pre style='font-family: \"Courier New\", Monaco, Consolas, monospace; font-size: 12px;'>" + "\n".join(formatted_blocks) + "</pre>"
        return html_content
    
    def get_image_html(self, status):
        """根据状态获取图片的HTML"""
        base64_data = self.image_base64.get(status)
        
        if base64_data:
            # 使用Base64编码的图片
            return f"<img src='{base64_data}' width='16' height='16' style='vertical-align: middle; margin-right: 5px;'>"
        else:
            # 图片不存在，使用文本替代
            text_map = {
                "pending": "[PENDING]",
                "passed": "[PASS]", 
                "failed": "[FAIL]"
            }
            return f"<span style='color: gray; font-weight: bold;'>{text_map.get(status, '')}</span>"
    
    def initialize_error_status(self, error_text):
        """初始化错误状态 - 支持错误和警告"""
        if "没有发现错误" in error_text:
            return
        
        # 按分隔符分割错误信息
        blocks = error_text.split(self.delimiter)
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
                
            # 检查这个块是否包含错误信息或警告信息
            if any(marker in block for marker in ['❌', '⚠️']):
                # 获取标识 - 使用清理后的文本
                block_identifier = self.clean_error_text(block)
                    
                if block_identifier and block_identifier not in self.error_status:
                    self.error_status[block_identifier] = "pending"
                    # 保存标识符映射
                    self.error_block_identifiers[block_identifier] = block
    
    def show_error_context_menu(self, position):
        """显示错误信息的右键菜单 - 支持在任何行点击，包括已标记状态的块"""
        # 获取光标位置
        cursor = self.error_text.cursorForPosition(position)
        
        # 获取当前块号
        block_number = cursor.blockNumber()
        
        # 获取文档
        document = self.error_text.document()
        
        # 查找当前块所属的错误块
        error_block_key = None
        
        # 向上查找分隔符
        start_index = -1
        for i in range(block_number, -1, -1):
            block = document.findBlockByNumber(i)
            text = block.text().strip()
            if self.delimiter in text:
                start_index = i
                break
        
        # 向下查找分隔符
        end_index = -1
        if start_index != -1:
            for i in range(start_index + 1, document.blockCount()):
                block = document.findBlockByNumber(i)
                text = block.text().strip()
                if self.delimiter in text:
                    end_index = i
                    break
        
        # 提取错误块内容
        if start_index != -1 and end_index != -1:
            error_block_lines = []
            for i in range(start_index + 1, end_index):
                block = document.findBlockByNumber(i)
                text = block.text().strip()
                if text:
                    error_block_lines.append(text)
            
            if error_block_lines:
                # 使用整个错误块内容作为标识符
                error_block_content = "\n".join(error_block_lines)
                
                # 在错误状态中查找匹配的块
                for key in self.error_status.keys():
                    # 创建一个清理后的版本进行比较，移除状态符号
                    clean_key = self.clean_error_text(key)
                    clean_content = self.clean_error_text(error_block_content)
                    
                    # 检查清理后的内容是否匹配
                    if clean_content in clean_key or clean_key in clean_content:
                        error_block_key = key
                        break
                
                # 如果没有找到匹配的键，尝试使用保存的标识符映射
                if not error_block_key:
                    for key, original_block in self.error_block_identifiers.items():
                        clean_key = self.clean_error_text(key)
                        clean_content = self.clean_error_text(error_block_content)
                        
                        # 检查清理后的内容是否匹配
                        if clean_content in clean_key or clean_key in clean_content:
                            error_block_key = key
                            break
        
        if error_block_key:
            menu = QMenu(self)
            
            # 设置菜单样式 - 蓝色背景，悬停时文字变绿色
            menu.setStyleSheet("""
                QMenu {
                    background-color: #3498db;
                    border: 1px solid #2980b9;
                    border-radius: 5px;
                    padding: 5px;
                }
                QMenu::item {
                    background-color: transparent;
                    padding: 8px 16px;
                    border-radius: 3px;
                    color: white;
                    font-size: 14px;
                }
                QMenu::item:selected {
                    background-color: #2980b9;
                    color: #27ae60;  /* 悬停时文字变为绿色 */
                }
                QMenu::item:disabled {
                    color: #bdc3c7;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #2980b9;
                    margin: 5px 0px;
                }
            """)
            
            mark_pass_action = QAction("标记为通过(PASS)", self)
            mark_fail_action = QAction("标记为失败(FAIL)", self)
            reset_action = QAction("重置状态", self)
            
            mark_pass_action.triggered.connect(lambda: self.mark_error_status(error_block_key, "passed"))
            mark_fail_action.triggered.connect(lambda: self.mark_error_status(error_block_key, "failed"))
            reset_action.triggered.connect(lambda: self.mark_error_status(error_block_key, "pending"))
            
            menu.addAction(mark_pass_action)
            menu.addAction(mark_fail_action)
            menu.addAction(reset_action)
            
            menu.exec(self.error_text.mapToGlobal(position))
    
    def clean_error_text(self, text):
        """清理错误文本，移除状态符号"""
        # 移除所有状态符号
        cleaned = text.replace('❌', '').replace('⚠️', '').replace('✅', '')
        # 移除状态图片的HTML标签
        cleaned = re.sub(r'<img[^>]*>', '', cleaned)
        # 移除多余的空白字符
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def mark_error_status(self, block_key, status):
        """标记错误状态"""
        # 保存当前的滚动位置
        scrollbar = self.error_text.verticalScrollBar()
        old_scroll_position = scrollbar.value()
        
        # 设置新的状态
        self.error_status[block_key] = status
        
        # 使用原始错误文本重新格式化错误信息
        formatted_errors = self.format_errors_with_status(self.original_error_text)
        self.error_text.setHtml(formatted_errors)
        
        # 恢复滚动位置
        scrollbar.setValue(old_scroll_position)
    
    def handle_analysis_error(self, error_message):
        """处理分析过程中出现的错误 - 保持选中状态"""
        self.error_text.setPlainText(error_message)
        self.progress_bar.setVisible(False)
        # 分析出错时，按钮保持选中状态但显示错误状态
        self.analyze_btn.setChecked(True)
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("分析出错")
        self.is_analyzing = False
        # 强制更新样式
        self.force_button_style_update()
        
        # 更新错误文本框边框为绿色（因为有错误信息）
        self.error_text.setStyleSheet(self.get_status_text_style(True))