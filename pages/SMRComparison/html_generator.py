import os
import json
from datetime import datetime
from .data_models import ComparisonResult, data_modelsChangeType


class HTMLReportGenerator:
    """HTML报告生成器"""
    
    def __init__(self):
        pass
    
    def generate_html_report(self, result: ComparisonResult, output_path: str) -> str:
        """生成HTML格式的报告"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 准备数据
        total_old = len(result.old_features)
        total_new = len(result.new_features)
        summary = result.summary
        
        # 构建HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FeatureDeviceInfo 智能对比报告 (BCompare算法)</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_header(now)}
        {self._generate_result_summary(result)}
        {self._generate_file_info(total_old, total_new)}
        {self._generate_stats_section(summary)}
        {self._generate_comparison_section(result)}
        {self._generate_footer(now)}
    </div>
    
    <script>
        {self._get_js_scripts()}
    </script>
</body>
</html>'''
        
        # 保存HTML文件
        self._save_html_file(html, output_path)
        
        return html
    
    def _get_css_styles(self):
        """获取CSS样式"""
        return '''
        :root {
            --color-same: #4CAF50;
            --color-moved: #2196F3;
            --color-modified: #FF9800;
            --color-added: #8BC34A;
            --color-removed: #F44336;
            --color-bg-light: #f8f9fa;
            --color-bg-white: #ffffff;
            --color-border: #dee2e6;
            --color-text: #333;
            --color-text-light: #666;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--color-text);
            background-color: #f5f7fa;
            padding: 20px;
        }
        
        .container {
            max-width: 1800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        /* 头部样式 */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.2rem;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .header .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 15px;
        }
        
        .timestamp {
            background: rgba(255,255,255,0.15);
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        
        /* 结果摘要 */
        .result-summary {
            padding: 20px 40px;
            border-bottom: 1px solid var(--color-border);
        }
        
        .result-badge {
            display: inline-block;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: bold;
        }
        
        .result-pass {
            background-color: var(--color-same);
            color: white;
        }
        
        .result-fail {
            background-color: var(--color-modified);
            color: white;
        }
        
        /* 文件信息 */
        .file-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 30px 40px;
            border-bottom: 1px solid var(--color-border);
        }
        
        .file-card {
            background: var(--color-bg-light);
            border-radius: 8px;
            padding: 25px;
            border: 1px solid var(--color-border);
        }
        
        .file-card.old {
            border-left: 4px solid var(--color-removed);
        }
        
        .file-card.new {
            border-left: 4px solid var(--color-added);
        }
        
        .file-card h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        
        .info-item {
            margin-bottom: 12px;
            display: flex;
        }
        
        .info-label {
            font-weight: 600;
            min-width: 100px;
            color: var(--color-text-light);
        }
        
        .info-value {
            color: var(--color-text);
            flex: 1;
            word-break: break-all;
            font-family: 'Consolas', monospace;
            font-size: 0.9rem;
        }
        
        /* 统计卡片 */
        .stats-section {
            padding: 30px 40px;
            border-bottom: 1px solid var(--color-border);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 20px;
            margin-top: 20px;
        }
        
        .stat-card {
            text-align: center;
            padding: 25px 15px;
            border-radius: 8px;
            background: var(--color-bg-light);
            border: 1px solid var(--color-border);
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .stat-same { color: var(--color-same); }
        .stat-moved { color: var(--color-moved); }
        .stat-modified { color: var(--color-modified); }
        .stat-added { color: var(--color-added); }
        .stat-removed { color: var(--color-removed); }
        
        .stat-label {
            font-size: 1rem;
            color: var(--color-text-light);
        }
        
        /* 对比表格 */
        .comparison-section {
            padding: 30px 40px;
        }
        
        .section-title {
            font-size: 1.5rem;
            color: #2c3e50;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        
        .legend {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            padding: 15px;
            background: var(--color-bg-light);
            border-radius: 8px;
            border: 1px solid var(--color-border);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            font-size: 0.9rem;
        }
        
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 8px;
        }
        
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 0.9rem;
        }
        
        .comparison-table th {
            background-color: #f1f5f9;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #2c3e50;
            border-bottom: 2px solid var(--color-border);
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .comparison-table td {
            padding: 15px;
            border-bottom: 1px solid var(--color-border);
            vertical-align: top;
        }
        
        .comparison-table tr:hover {
            background-color: #f8fafc;
        }
        
        .index-col {
            width: 60px;
            text-align: center;
            font-weight: bold;
            color: var(--color-text-light);
        }
        
        .status-col {
            width: 100px;
            text-align: center;
        }
        
        .change-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            color: white;
        }
        
        .badge-same { background-color: var(--color-same); }
        .badge-moved { background-color: var(--color-moved); }
        .badge-modified { background-color: var(--color-modified); }
        .badge-added { background-color: var(--color-added); }
        .badge-removed { background-color: var(--color-removed); }
        
        .feature-info {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.85rem;
        }
        
        .feature-name {
            font-weight: bold;
            margin-bottom: 5px;
            color: #2c3e50;
        }
        
        .feature-details {
            background: var(--color-bg-light);
            padding: 10px;
            border-radius: 5px;
            border: 1px solid var(--color-border);
            margin-top: 5px;
            max-height: 150px;
            overflow-y: auto;
            font-size: 0.8rem;
        }
        
        .changes-list {
            margin-top: 10px;
            padding-left: 20px;
        }
        
        .change-item {
            margin-bottom: 5px;
            color: var(--color-text-light);
        }
        
        .change-old {
            color: var(--color-removed);
            text-decoration: line-through;
            margin-right: 5px;
        }
        
        .change-new {
            color: var(--color-added);
            margin-left: 5px;
        }
        
        .arrow {
            color: var(--color-text-light);
            margin: 0 5px;
        }
        
        /* 控制按钮 */
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: 1px solid var(--color-border);
            background: white;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .filter-btn:hover {
            background: var(--color-bg-light);
        }
        
        .filter-btn.active {
            background: #3498db;
            color: white;
            border-color: #3498db;
        }
        
        /* 页脚 */
        .footer {
            text-align: center;
            padding: 20px 40px;
            background-color: var(--color-bg-light);
            color: var(--color-text-light);
            border-top: 1px solid var(--color-border);
            font-size: 0.9rem;
        }
        
        /* 响应式设计 */
        @media (max-width: 1200px) {
            .stats-grid {
                grid-template-columns: repeat(3, 1fr);
            }
            
            .file-info {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .header, .file-info, .stats-section, .comparison-section {
                padding: 20px;
            }
            
            .comparison-table {
                font-size: 0.8rem;
            }
        }
        
        @media (max-width: 480px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
        '''
    
    def _generate_header(self, now):
        """生成头部"""
        return f'''
        <div class="header">
            <h1>🔍 FeatureDeviceInfo 智能对比报告</h1>
            <div class="subtitle">采用BCompare算法 - 识别相同、移动、修改、新增、删除</div>
            <div class="timestamp">生成时间: {now}</div>
        </div>
        '''
    
    def _generate_result_summary(self, result):
        """生成结果摘要"""
        if result.is_identical:
            return '''
            <div class="result-summary">
                <div class="result-badge result-pass">✅ PASS - 文件完全一致</div>
            </div>
            '''
        else:
            return '''
            <div class="result-summary">
                <div class="result-badge result-fail">❌ 发现差异 - 详细对比如下</div>
            </div>
            '''
    
    def _generate_file_info(self, total_old, total_new):
        """生成文件信息"""
        return f'''
        <div class="file-info">
            <div class="file-card old">
                <h3>📁 MR文件 (基准)</h3>
                <div class="info-item">
                    <div class="info-label">功能数量:</div>
                    <div class="info-value">{total_old} 项</div>
                </div>
            </div>
            
            <div class="file-card new">
                <h3>📁 SMR文件 (对比)</h3>
                <div class="info-item">
                    <div class="info-label">功能数量:</div>
                    <div class="info-value">{total_new} 项</div>
                </div>
            </div>
        </div>
        '''
    
    def _generate_stats_section(self, summary):
        """生成统计部分"""
        return f'''
        <div class="stats-section">
            <h2 class="section-title">📊 变更统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number stat-same">{summary.get('same', 0)}</div>
                    <div class="stat-label">相同</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number stat-moved">{summary.get('moved', 0)}</div>
                    <div class="stat-label">移动</div>
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
        '''
    
    def _generate_comparison_section(self, result):
        """生成对比表格部分"""
        # 生成图例
        legend = '''
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: var(--color-same);"></div>
                <span>相同 - 位置和内容都相同</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: var(--color-moved);"></div>
                <span>移动 - 位置变化，内容相同</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: var(--color-modified);"></div>
                <span>修改 - 内容发生变化</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: var(--color-added);"></div>
                <span>新增 - 新文件中独有的功能</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: var(--color-removed);"></div>
                <span>删除 - 旧文件中独有的功能</span>
            </div>
        </div>
        '''
        
        # 生成过滤按钮
        controls = '''
        <div class="controls">
            <button class="filter-btn active" onclick="filterChanges('all')">显示全部</button>
            <button class="filter-btn" onclick="filterChanges('same')">仅显示相同</button>
            <button class="filter-btn" onclick="filterChanges('moved')">仅显示移动</button>
            <button class="filter-btn" onclick="filterChanges('modified')">仅显示修改</button>
            <button class="filter-btn" onclick="filterChanges('added')">仅显示新增</button>
            <button class="filter-btn" onclick="filterChanges('removed')">仅显示删除</button>
        </div>
        '''
        
        # 生成表格行
        table_rows = ""
        for i, change in enumerate(result.changes):
            table_rows += self._generate_table_row(change, i)
        
        table = f'''
        <table class="comparison-table" id="comparison-table">
            <thead>
                <tr>
                    <th class="index-col">#</th>
                    <th class="status-col">状态</th>
                    <th>MR版本</th>
                    <th>SMR版本</th>
                    <th>变更详情</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        '''
        
        return f'''
        <div class="comparison-section">
            <h2 class="section-title">🔍 详细对比</h2>
            {legend}
            {controls}
            {table}
        </div>
        '''
    
    def _generate_table_row(self, change, index):
        """生成表格行"""
        # 确定状态类名和显示文本
        status_class = f"badge-{change.change_type.value}"
        status_text = {
            "same": "相同",
            "moved": "移动",
            "modified": "修改",
            "added": "新增",
            "removed": "删除"
        }.get(change.change_type.value, change.change_type.value)
        
        # MR版本信息
        mr_info = ""
        if change.old_item:
            mr_json = json.dumps(change.old_item.data, indent=2, ensure_ascii=False)
            mr_info = f'''
                <div class="feature-info">
                    <div class="feature-name">{change.old_item.name}</div>
                    <div class="feature-details">{mr_json}</div>
                </div>
            '''
        
        # SMR版本信息
        smr_info = ""
        if change.new_item:
            smr_json = json.dumps(change.new_item.data, indent=2, ensure_ascii=False)
            smr_info = f'''
                <div class="feature-info">
                    <div class="feature-name">{change.new_item.name}</div>
                    <div class="feature-details">{smr_json}</div>
                </div>
            '''
        
        # 变更详情
        change_details = ""
        if change.changes:
            change_details = '<div class="changes-list">'
            for field, old_val, new_val in change.changes:
                old_str = json.dumps(old_val, ensure_ascii=False) if old_val is not None else "null"
                new_str = json.dumps(new_val, ensure_ascii=False) if new_val is not None else "null"
                change_details += f'''
                    <div class="change-item">
                        <span class="change-field">{field}:</span>
                        <span class="change-old">{old_str}</span>
                        <span class="arrow">→</span>
                        <span class="change-new">{new_str}</span>
                    </div>
                '''
            change_details += '</div>'
        
        # 移动信息
        move_info = ""
        if change.change_type == data_modelsChangeType.MOVED and change.old_item and change.new_item:
            if change.old_item.index != change.new_item.index:
                move_info = f'<div style="margin-top: 5px; color: var(--color-moved);">位置: {change.old_item.index+1} → {change.new_item.index+1}</div>'
        
        return f'''
        <tr class="change-row" data-change-type="{change.change_type.value}">
            <td class="index-col">{index+1}</td>
            <td class="status-col">
                <span class="change-badge {status_class}">{status_text}</span>
                {move_info}
            </td>
            <td>{mr_info}</td>
            <td>{smr_info}</td>
            <td>{change_details}</td>
        </tr>
        '''
    
    def _generate_footer(self, now):
        """生成页脚"""
        return f'''
        <div class="footer">
            <p>生成时间: {now} | 对比算法: BCompare风格 | 版本: 2.0</p>
            <p style="margin-top: 5px; font-size: 0.8rem; color: #888;">
                说明：算法会智能识别功能项的移动、修改、新增和删除，而不仅仅是按索引位置比较。
            </p>
        </div>
        '''
    
    def _get_js_scripts(self):
        """获取JavaScript脚本"""
        return '''
        // 过滤功能
        function filterChanges(type) {
            const rows = document.querySelectorAll('.change-row');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // 更新按钮状态
            buttons.forEach(btn => {
                if (btn.textContent.includes(type) || (type === 'all' && btn.textContent.includes('全部'))) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            
            // 显示/隐藏行
            rows.forEach(row => {
                if (type === 'all') {
                    row.style.display = '';
                } else {
                    const rowType = row.getAttribute('data-change-type');
                    if (rowType === type) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
        }
        
        // 默认展开所有行
        document.addEventListener('DOMContentLoaded', function() {
            // 可以添加其他初始化代码
        });
        
        // 点击功能详情展开/收起
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('feature-name')) {
                const details = e.target.nextElementSibling;
                if (details.style.display === 'none') {
                    details.style.display = 'block';
                } else {
                    details.style.display = 'none';
                }
            }
        });
        '''
    
    def _save_html_file(self, html_content, output_path):
        """保存HTML文件"""
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ HTML报告已保存: {output_path}")
        except Exception as e:
            print(f"❌ 保存HTML报告失败: {e}")