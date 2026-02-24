# Package_html_reporter.py
from datetime import datetime
from typing import Dict, List, Any
from .Package_models import PackageComparisonResult, PackageChange, PackageChangeType
from .Package_file_utils import FileUtils


class HTMLReporter:
    """HTML报告生成器"""
    
    def __init__(self):
        self.file_utils = FileUtils()
    
    def generate_html_report(self, result: PackageComparisonResult, output_path: str) -> str:
        """生成HTML格式的报告"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 准备数据
        total_old = result.old_file_stats['package_count']
        total_new = result.new_file_stats['package_count']
        summary = result.summary
        
        # 构建HTML
        html = self._create_html_structure(now, result, total_old, total_new, summary)
        
        # 保存HTML文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            return f"HTML报告已生成: {output_path}"
        except Exception as e:
            return f"生成HTML报告失败: {e}"
    
    def _create_html_structure(self, now: str, result: PackageComparisonResult,
                              total_old: int, total_new: int, summary: Dict[str, int]) -> str:
        """创建HTML基础结构"""
        
        status_badge = '''
            <div class="result-badge result-pass">✅ PASS - 所有包完全相同</div>
        ''' if result.is_identical else '''
            <div class="result-badge result-fail">❌ 发现差异 - 详细对比如下</div>
        '''
        
        # 生成表格行
        table_rows = ""
        for i, change in enumerate(result.changes):
            table_rows += self._create_table_row(i, change)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Package JSON 对比报告</title>
    <style>
        :root {{
            --color-same: #4CAF50;
            --color-modified: #FF9800;
            --color-added: #8BC34A;
            --color-removed: #F44336;
            --color-bg-light: #f8f9fa;
            --color-bg-white: #ffffff;
            --color-border: #dee2e6;
            --color-text: #333;
            --color-text-light: #666;
            --color-diff-red: #ff4444;  /* 新增：红色用于显示差异 */
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--color-text);
            background-color: #f5f7fa;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        /* 头部样式 */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.2rem;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 15px;
        }}
        
        .timestamp {{
            background: rgba(255,255,255,0.15);
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        
        /* 结果摘要 */
        .result-summary {{
            padding: 20px 40px;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .result-badge {{
            display: inline-block;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: bold;
        }}
        
        .result-pass {{
            background-color: var(--color-same);
            color: white;
        }}
        
        .result-fail {{
            background-color: var(--color-modified);
            color: white;
        }}
        
        /* 文件信息 */
        .file-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 30px 40px;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .file-card {{
            background: var(--color-bg-light);
            border-radius: 8px;
            padding: 25px;
            border: 1px solid var(--color-border);
        }}
        
        .file-card.old {{
            border-left: 4px solid var(--color-removed);
        }}
        
        .file-card.new {{
            border-left: 4px solid var(--color-added);
        }}
        
        .file-card h3 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}
        
        .info-item {{
            margin-bottom: 12px;
            display: flex;
        }}
        
        .info-label {{
            font-weight: 600;
            min-width: 100px;
            color: var(--color-text-light);
        }}
        
        .info-value {{
            color: var(--color-text);
            flex: 1;
            word-break: break-all;
            font-family: 'Consolas', monospace;
            font-size: 0.9rem;
        }}
        
        /* 统计卡片 */
        .stats-section {{
            padding: 30px 40px;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            text-align: center;
            padding: 25px 15px;
            border-radius: 8px;
            background: var(--color-bg-light);
            border: 1px solid var(--color-border);
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .stat-same {{ color: var(--color-same); }}
        .stat-modified {{ color: var(--color-modified); }}
        .stat-added {{ color: var(--color-added); }}
        .stat-removed {{ color: var(--color-removed); }}
        
        .stat-label {{
            font-size: 1rem;
            color: var(--color-text-light);
        }}
        
        /* 对比表格 */
        .comparison-section {{
            padding: 30px 40px;
        }}
        
        .section-title {{
            font-size: 1.5rem;
            color: #2c3e50;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}
        
        .legend {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            padding: 15px;
            background: var(--color-bg-light);
            border-radius: 8px;
            border: 1px solid var(--color-border);
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 0.9rem;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 8px;
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 0.9rem;
        }}
        
        .comparison-table th {{
            background-color: #f1f5f9;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #2c3e50;
            border-bottom: 2px solid var(--color-border);
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .comparison-table td {{
            padding: 15px;
            border-bottom: 1px solid var(--color-border);
            vertical-align: top;
        }}
        
        .comparison-table tr:hover {{
            background-color: #f8fafc;
        }}
        
        .index-col {{
            width: 60px;
            text-align: center;
            font-weight: bold;
            color: var(--color-text-light);
        }}
        
        .status-col {{
            width: 100px;
            text-align: center;
        }}
        
        .package-name-col {{
            width: 250px;
        }}
        
        .change-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            color: white;
        }}
        
        .badge-same {{ background-color: var(--color-same); }}
        .badge-modified {{ background-color: var(--color-modified); }}
        .badge-added {{ background-color: var(--color-added); }}
        .badge-removed {{ background-color: var(--color-removed); }}
        
        .package-info {{
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.85rem;
        }}
        
        .package-name {{
            font-weight: bold;
            margin-bottom: 5px;
            color: #2c3e50;
            cursor: pointer;
            padding: 5px;
            border-radius: 3px;
            transition: background-color 0.2s;
        }}
        
        .package-name:hover {{
            background-color: rgba(0,0,0,0.03);
        }}
        
        .package-summary {{
            font-size: 0.8rem;
            color: var(--color-text-light);
            margin-top: 5px;
            padding: 3px 8px;
            background-color: rgba(0,0,0,0.03);
            border-radius: 4px;
            border-left: 3px solid #ddd;
        }}
        
        .package-details {{
            background: var(--color-bg-light);
            padding: 10px;
            border-radius: 5px;
            border: 1px solid var(--color-border);
            margin-top: 5px;
            max-height: 150px;
            overflow-y: auto;
            font-size: 0.8rem;
        }}
        
        /* 字段项样式 */
        .package-fields {{
            max-height: 200px;
            overflow-y: auto;
            padding: 5px;
        }}
        
        .field-item {{
            margin-bottom: 4px;
            padding: 3px 5px;
            border-radius: 3px;
            transition: background-color 0.2s;
        }}
        
        .field-item:hover {{
            background-color: rgba(0,0,0,0.02);
        }}
        
        /* 差异字段样式 - 突出显示为红色 */
        .diff-old {{
            background-color: rgba(255, 68, 68, 0.1);  /* 浅红色背景 */
            border-left: 3px solid var(--color-diff-red);  /* 红色边框 */
            padding-left: 8px;
            color: var(--color-diff-red);  /* 红色文字 */
            font-weight: bold;  /* 加粗 */
        }}
        
        .diff-new {{
            background-color: rgba(255, 68, 68, 0.1);  /* 浅红色背景 */
            border-left: 3px solid var(--color-diff-red);  /* 红色边框 */
            padding-left: 8px;
            color: var(--color-diff-red);  /* 红色文字 */
            font-weight: bold;  /* 加粗 */
        }}
        
        /* 变更详情样式 */
        .change-details {{
            min-width: 300px;
        }}
        
        .changes-list {{
            margin-top: 10px;
            padding-left: 20px;
        }}
        
        .change-item {{
            margin-bottom: 8px;  /* 增加间距 */
            padding: 8px;  /* 增加内边距 */
            background-color: rgba(255, 68, 68, 0.05);  /* 非常浅的红色背景 */
            border-radius: 4px;
            border-left: 3px solid var(--color-diff-red);  /* 红色边框 */
        }}
        
        .change-index {{
            display: inline-block;
            width: 20px;
            font-weight: bold;
            color: #666;
        }}
        
        .change-field {{
            font-weight: bold;
            color: #2c3e50;
            margin-right: 5px;
        }}
        
        /* 修改：将改变的地方显示为红色 */
        .change-old {{
            color: var(--color-diff-red);  /* 红色文字 */
            text-decoration: line-through;  /* 删除线 */
            margin-right: 5px;
            font-weight: bold;  /* 加粗 */
        }}
        
        .change-new {{
            color: var(--color-diff-red);  /* 红色文字 */
            margin-left: 5px;
            font-weight: bold;  /* 加粗 */
        }}
        
        .arrow {{
            color: var(--color-diff-red);  /* 箭头也用红色 */
            margin: 0 8px;  /* 增加间距 */
            font-weight: bold;  /* 加粗 */
        }}
        
        .permission-change {{
            margin-left: 25px;
            margin-top: 5px;
            padding: 5px;
            background-color: rgba(255, 68, 68, 0.05);  /* 浅红色背景 */
            border-radius: 3px;
            border-left: 2px solid var(--color-diff-red);  /* 红色边框 */
        }}
        
        .no-changes {{
            color: var(--color-same);
            font-style: italic;
            padding: 8px;
            text-align: center;
        }}
        
        .no-data {{
            color: #999;
            font-style: italic;
            text-align: center;
            padding: 10px;
        }}
        
        .package-added, .package-removed {{
            padding: 8px;
            border-radius: 4px;
            text-align: center;
        }}
        
        .package-added {{
            background-color: rgba(139, 195, 74, 0.1);
            color: var(--color-added);
        }}
        
        .package-removed {{
            background-color: rgba(244, 67, 54, 0.1);
            color: var(--color-removed);
        }}
        
        /* 新增：用于突出显示目标SDK的样式 */
        .target-sdk-diff {{
            background-color: rgba(255, 68, 68, 0.15) !important;  /* 更深的红色背景 */
            border: 2px solid var(--color-diff-red) !important;  /* 更粗的红色边框 */
            padding: 5px 10px !important;
            border-radius: 4px !important;
            color: var(--color-diff-red) !important;  /* 红色文字 */
            font-weight: bold !important;  /* 加粗 */
            font-size: 1.1em !important;  /* 稍微放大字体 */
        }}
        
        /* 控制按钮 */
        .controls {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: 1px solid var(--color-border);
            background: white;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .filter-btn:hover {{
            background: var(--color-bg-light);
        }}
        
        .filter-btn.active {{
            background: #3498db;
            color: white;
            border-color: #3498db;
        }}
        
        /* 页脚 */
        .footer {{
            text-align: center;
            padding: 20px 40px;
            background-color: var(--color-bg-light);
            color: var(--color-text-light);
            border-top: 1px solid var(--color-border);
            font-size: 0.9rem;
        }}
        
        /* 响应式设计 */
        @media (max-width: 1200px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .file-info {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .header, .file-info, .stats-section, .comparison-section {{
                padding: 20px;
            }}
            
            .comparison-table {{
                font-size: 0.8rem;
            }}
        }}
        
        @media (max-width: 480px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Package JSON 对比报告</h1>
            <div class="subtitle">MR vs SMR 包信息详细对比 - 差异项显示为红色</div>
            <div class="timestamp">生成时间: {now}</div>
        </div>
        
        <div class="result-summary">
            {status_badge}
        </div>
        
        <div class="file-info">
            <div class="file-card old">
                <h3>📁 MR文件 (基准)</h3>
                <div class="info-item">
                    <div class="info-label">文件名:</div>
                    <div class="info-value">{result.old_file_stats['name']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">路径:</div>
                    <div class="info-value">{result.old_file_stats['directory']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">大小:</div>
                    <div class="info-value">{result.old_file_stats['size']:,} 字节</div>
                </div>
                <div class="info-item">
                    <div class="info-label">MD5:</div>
                    <div class="info-value">{result.old_file_stats['md5'][:16]}...</div>
                </div>
                <div class="info-item">
                    <div class="info-label">包数量:</div>
                    <div class="info-value">{total_old} 个</div>
                </div>
            </div>
            
            <div class="file-card new">
                <h3>📁 SMR文件 (对比)</h3>
                <div class="info-item">
                    <div class="info-label">文件名:</div>
                    <div class="info-value">{result.new_file_stats['name']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">路径:</div>
                    <div class="info-value">{result.new_file_stats['directory']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">大小:</div>
                    <div class="info-value">{result.new_file_stats['size']:,} 字节</div>
                </div>
                <div class="info-item">
                    <div class="info-label">MD5:</div>
                    <div class="info-value">{result.new_file_stats['md5'][:16]}...</div>
                </div>
                <div class="info-item">
                    <div class="info-label">包数量:</div>
                    <div class="info-value">{total_new} 个</div>
                </div>
            </div>
        </div>
        
        <div class="stats-section">
            <h2 class="section-title">📊 变更统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number stat-same">{summary.get('same', 0)}</div>
                    <div class="stat-label">相同</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number stat-modified">{summary.get('modified', 0)}</div>
                    <div class="stat-label">修改</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number stat-added">{summary.get('added', 0)}</div>
                    <div class="stat-label">新增</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number stat-removed">{summary.get('removed', 0)}</div>
                    <div class="stat-label">删除</div>
                </div>
            </div>
        </div>
        
        <div class="comparison-section">
            <h2 class="section-title">🔍 详细对比 - <span style="color: var(--color-diff-red);">差异项已标红</span></h2>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: var(--color-same);"></div>
                    <span>相同 - 两个文件中完全相同</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: var(--color-modified);"></div>
                    <span>修改 - 内容发生变化</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: var(--color-diff-red);"></div>
                    <span><strong>差异项 - 显示为红色</strong></span>
                </div>
            </div>
            
            <div class="controls">
                <button class="filter-btn active" onclick="filterChanges('all')">显示全部</button>
                <button class="filter-btn" onclick="filterChanges('same')">仅显示相同</button>
                <button class="filter-btn" onclick="filterChanges('modified')">仅显示修改</button>
                <button class="filter-btn" onclick="filterChanges('added')">仅显示新增</button>
                <button class="filter-btn" onclick="filterChanges('removed')">仅显示删除</button>
            </div>
            
            <table class="comparison-table" id="comparison-table">
                <thead>
                    <tr>
                        <th class="index-col">#</th>
                        <th class="status-col">状态</th>
                        <th class="package-name-col">包名</th>
                        <th>MR版本</th>
                        <th>SMR版本</th>
                        <th>变更详情</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>生成时间: {now} | 对比算法: PackageComparator | 版本: 2.0</p>
            <p style="margin-top: 5px; font-size: 0.8rem; color: #888;">
                说明：此报告比较两个JSON文件中的package信息，<strong style="color: var(--color-diff-red);">差异项已用红色突出显示</strong>。
            </p>
        </div>
    </div>
    
    <script>
        // 过滤功能
        function filterChanges(type) {{
            const rows = document.querySelectorAll('.change-row');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // 更新按钮状态
            buttons.forEach(btn => {{
                if (btn.textContent.includes(type) || (type === 'all' && btn.textContent.includes('全部'))) {{
                    btn.classList.add('active');
                }} else {{
                    btn.classList.remove('active');
                }}
            }});
            
            // 显示/隐藏行
            rows.forEach(row => {{
                if (type === 'all') {{
                    row.style.display = '';
                }} else {{
                    const rowType = row.getAttribute('data-change-type');
                    if (rowType === type) {{
                        row.style.display = '';
                    }} else {{
                        row.style.display = 'none';
                    }}
                }}
            }});
        }}
        
        // 默认展开所有行
        document.addEventListener('DOMContentLoaded', function() {{
            // 可以添加其他初始化代码
        }});
        
        // 点击包详情展开/收起
        document.addEventListener('click', function(e) {{
            if (e.target.classList.contains('package-name')) {{
                const details = e.target.nextElementSibling;
                if (details.style.display === 'none') {{
                    details.style.display = 'block';
                }} else {{
                    details.style.display = 'none';
                }}
            }}
        }});
        
        // 高亮显示特定包名 - 自动查找并高亮显示com.android.compatibility.common.deviceinfo
        document.addEventListener('DOMContentLoaded', function() {{
            // 查找特定的包名
            const specificPackage = "com.android.compatibility.common.deviceinfo";
            const packageElements = document.querySelectorAll('.package-name');
            
            packageElements.forEach(element => {{
                if (element.textContent.trim() === specificPackage) {{
                    // 高亮显示这个包
                    element.style.backgroundColor = 'rgba(255, 68, 68, 0.1)';
                    element.style.border = '2px solid var(--color-diff-red)';
                    element.style.padding = '8px';
                    element.style.borderRadius = '5px';
                    
                    // 查找目标SDK字段并特别高亮
                    const rows = element.closest('tr');
                    if (rows) {{
                        // 查找目标SDK相关的字段
                        const fieldItems = rows.querySelectorAll('.field-item');
                        fieldItems.forEach(field => {{
                            if (field.textContent.includes('目标SDK') || field.textContent.includes('target_sdk')) {{
                                field.classList.add('target-sdk-diff');
                            }}
                        }});
                    }}
                }}
            }});
        }});
    </script>
</body>
</html>'''
        
        return html
    
    def _create_table_row(self, index: int, change: PackageChange) -> str:
        """创建单个表格行 - 突出显示差异"""
        # 确定状态类名和显示文本
        status_class = f"badge-{change.change_type.value}"
        status_text = {
            "same": "相同",
            "modified": "修改",
            "added": "新增",
            "removed": "删除"
        }.get(change.change_type.value, change.change_type.value)
        
        # 根据变更类型决定显示内容
        if change.change_type == PackageChangeType.ADDED:
            # 新增的包 - 显示SMR版本的所有信息
            mr_info = "<div class='no-data'>❌ 包不存在</div>"
            smr_info = self._format_package_with_differences(change.new_package, [], is_new=True)
        elif change.change_type == PackageChangeType.REMOVED:
            # 删除的包 - 显示MR版本的所有信息
            mr_info = self._format_package_with_differences(change.old_package, [], is_new=False)
            smr_info = "<div class='no-data'>❌ 包不存在</div>"
        elif change.change_type == PackageChangeType.MODIFIED:
            # 修改的包 - 突出显示差异字段
            diff_fields = [field for field, _, _ in change.differences] if change.differences else []
            mr_info = self._format_package_with_differences(change.old_package, diff_fields, is_new=False)
            smr_info = self._format_package_with_differences(change.new_package, diff_fields, is_new=True)
        else:
            # 相同的包 - 显示所有信息，无高亮
            mr_info = self._format_package_basic(change.old_package)
            smr_info = self._format_package_basic(change.new_package)
        
        # 变更详情 - 只显示实际有差异的字段
        change_details = ""
        if change.differences:
            change_details = '<div class="changes-list">'
            for i, (field, old_val, new_val) in enumerate(change.differences):
                # 格式化值
                old_str = self.file_utils.format_value_for_html(old_val)
                new_str = self.file_utils.format_value_for_html(new_val)
                
                # 特别检查是否是目标SDK字段
                is_target_sdk = field == "目标SDK"
                target_sdk_class = "target-sdk-diff" if is_target_sdk else ""
                
                # 特殊处理权限字段
                if field == "请求的权限" and isinstance(old_val, tuple) and isinstance(new_val, tuple):
                    change_details += f'''
                        <div class="change-item {target_sdk_class}">
                            <span class="change-index">{i+1}.</span>
                            <span class="change-field">{field}:</span><br>
                            <div class="permission-change">
                                <span class="change-old">{old_val[0]}</span>
                                <span class="arrow">→</span>
                                <span class="change-new">{new_val[0]}</span>
                            </div>
                        </div>
                    '''
                else:
                    change_details += f'''
                        <div class="change-item {target_sdk_class}">
                            <span class="change-index">{i+1}.</span>
                            <span class="change-field">{field}:</span>
                            <span class="change-old">{old_str}</span>
                            <span class="arrow">→</span>
                            <span class="change-new">{new_str}</span>
                        </div>
                    '''
            change_details += '</div>'
        elif change.change_type == PackageChangeType.SAME:
            change_details = '<div class="no-changes">✅ 所有字段相同</div>'
        else:
            change_details = f'<div class="package-{change.change_type.value}">此包仅在{"SMR" if change.change_type == PackageChangeType.ADDED else "MR"}文件中存在</div>'
        
        return f'''
            <tr class="change-row" data-change-type="{change.change_type.value}">
                <td class="index-col">{index+1}</td>
                <td class="status-col">
                    <span class="change-badge {status_class}">{status_text}</span>
                </td>
                <td class="package-name-col">
                    <div class="package-name" title="点击展开/收起详情">{change.package_name}</div>
                    <div class="package-summary">
                        {self._get_package_summary(change)}
                    </div>
                </td>
                <td class="mr-version">{mr_info}</td>
                <td class="smr-version">{smr_info}</td>
                <td class="change-details">{change_details}</td>
            </tr>
        '''
    
    def _format_package_with_differences(self, package: Dict, diff_fields: List[str], is_new: bool = False) -> str:
        """格式化包信息，突出显示差异字段"""
        if not package:
            return "<div class='no-data'>无数据</div>"
        
        lines = []
        
        # 关键字段
        field_mapping = [
            ("版本名称", "version_name"),
            ("安装路径", "dir"),
            ("系统权限标志", "system_priv"),
            ("最小SDK", "min_sdk"),
            ("目标SDK", "target_sdk"),
            ("共享安装包权限", "shares_install_packages_permission"),
            ("默认通知访问", "has_default_notification_access"),
            ("是否为活动管理员", "is_active_admin"),
            ("是否为默认无障碍服务", "is_default_accessibility_service")
        ]
        
        for display_name, field_key in field_mapping:
            value = package.get(field_key)
            if value is not None:
                formatted_value = self.file_utils.format_value_for_html(value)
                
                # 检查是否为差异字段
                if display_name in diff_fields:
                    # 差异字段 - 高亮显示为红色
                    diff_class = "diff-new" if is_new else "diff-old"
                    
                    # 如果是目标SDK字段，添加额外的高亮
                    if display_name == "目标SDK":
                        diff_class += " target-sdk-diff"
                    
                    lines.append(f"<div class='field-item {diff_class}'><b>{display_name}:</b> {formatted_value}</div>")
                else:
                    # 相同字段 - 正常显示
                    lines.append(f"<div class='field-item'><b>{display_name}:</b> {formatted_value}</div>")
        
        # 权限信息
        perms = package.get("requested_permissions", [])
        if perms:
            perm_count = len(perms)
            if "请求的权限" in diff_fields:
                perm_class = "diff-new" if is_new else "diff-old"
                lines.append(f"<div class='field-item {perm_class}'><b>请求权限:</b> {perm_count}个权限</div>")
            else:
                lines.append(f"<div class='field-item'><b>请求权限:</b> {perm_count}个权限</div>")
        
        return "<div class='package-fields'>" + "".join(lines) + "</div>"
    
    def _format_package_basic(self, package: Dict) -> str:
        """基本格式化包信息（用于相同包）"""
        if not package:
            return "<div class='no-data'>无数据</div>"
        
        return self.file_utils.format_package_for_html(package)
    
    def _get_package_summary(self, change: PackageChange) -> str:
        """获取包的简要信息"""
        if change.change_type == PackageChangeType.SAME:
            return "✅ 完全相同"
        elif change.change_type == PackageChangeType.MODIFIED:
            diff_count = len(change.differences) if change.differences else 0
            diff_fields = [field for field, _, _ in change.differences] if change.differences else []
            
            # 检查是否包含目标SDK字段
            has_target_sdk = "目标SDK" in diff_fields
            target_sdk_note = " <span style='color: var(--color-diff-red);'>⚠️ 目标SDK不同</span>" if has_target_sdk else ""
            
            return f"📝 {diff_count}个字段不同{target_sdk_note}"
        elif change.change_type == PackageChangeType.ADDED:
            return "➕ 新增包"
        elif change.change_type == PackageChangeType.REMOVED:
            return "➖ 删除包"
        return ""