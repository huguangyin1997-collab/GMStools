"""HTML 加载工具：解码 JS unescape() 编码的 HTML，转换为 QTextBrowser 兼容格式"""
import re
import urllib.parse


def load_html(filepath):
    """从 JS unescape() 编码的文件中提取并解码 HTML，做 QTextBrowser 兼容转换"""
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()

    m = re.search(r'unescape\(\"(.*?)\"\)', raw, re.DOTALL)
    if not m:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    encoded = m.group(1)
    # JS unescape() %uXXXX Unicode 格式
    decoded = re.sub(
        r'%u([0-9a-fA-F]{4})',
        lambda m2: chr(int(m2.group(1), 16)), encoded)
    html = urllib.parse.unquote(decoded)

    # === 转换为 QTextBrowser 兼容格式 ===
    # flex → block
    html = html.replace('display: flex', 'display: block')
    html = html.replace('display:flex', 'display:block')
    for prop in ('flex-direction', 'align-items', 'justify-content',
                 'flex-wrap', 'flex', 'order', 'flex-grow', 'flex-shrink',
                 'flex-basis', 'align-self', 'align-content'):
        html = re.sub(rf'{prop}\s*:\s*[^;]+;?', '', html)
    # 去掉不支持的
    for prop in ('position: sticky', 'box-shadow', 'transition',
                 'transform', 'animation', 'will-change'):
        html = re.sub(rf'{prop}\s*:\s*[^;]+;?', '', html)
    html = re.sub(r'::selection\s*\{[^}]*\}', '', html)
    html = re.sub(r':hover\s*\{[^}]*\}', '', html)
    html = re.sub(r':focus\s*\{[^}]*\}', '', html)
    html = re.sub(r'@\w+[^}]*\{[^}]*\}', '', html)
    html = re.sub(r'top\s*:\s*\d+px\s*;', '', html)
    # 白色背景确保透明背景上文字可读
    html = html.replace(
        '<body', '<body style="background-color: white; padding: 20px;"')
    # sidebar 用 float 模拟
    html = re.sub(r'\.sidebar\s*\{',
                  '.sidebar { width: 200px; float: left; ', html)
    html = re.sub(r'\.intro-and-content\s*\{',
                  '.intro-and-content { margin-left: 220px; ', html)
    # 侧边栏链接颜色
    html = re.sub(r'\.sidebar ul li a\s*\{',
                  '.sidebar ul li a { color: #1a5276; text-decoration: underline; ',
                  html)

    return html
