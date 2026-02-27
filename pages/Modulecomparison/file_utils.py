import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from typing import List

def clean_path(path: str) -> str:
    """安全清理文件路径"""
    path = path.strip().strip("'\"")
    return path

def check_file_extension(file_path: str) -> List[str]:
    """文件格式检查与模块提取"""
    try:
        ext = os.path.splitext(file_path)[1].lower().replace('.', '')
        
        if ext in ['html', 'htm']:
            return extract_module_names_html(file_path)
        elif ext == 'txt':
            return extract_module_names_txt(file_path)
        elif ext == 'xml':
            return extract_module_names_xml(file_path)
        else:
            return []
    except Exception as e:
        raise

def extract_module_names_html(html_file: str) -> List[str]:
    """从HTML文件中提取模块名"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        target_table = soup.find('table', class_='testsummary')
        if not target_table:
            return []

        modules_html = []
        for row in target_table.find_all('tr')[1:]:
            first_col = row.find('td')
            if first_col:
                name = first_col.text.strip().replace('\xa0', ' ')
                if name and name not in modules_html:
                    modules_html.append(name)

        return modules_html

    except Exception as e:
        raise

def extract_module_names_txt(txt_file: str) -> List[str]:
    """从TXT文件中提取模块名"""
    try:
        if not os.path.exists(txt_file):
            raise FileNotFoundError(f"文件不存在: {txt_file}")
        if not os.path.isfile(txt_file):
            raise IsADirectoryError(f"路径指向目录: {txt_file}")
            
        modules_txt = []
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                module_part = line.split('\t')[0]
                if module_part:
                    modules_txt.append(module_part)

        return modules_txt
            
    except Exception as e:
        raise

def extract_module_names_xml(xml_file: str) -> List[str]:
    """从XML文件中提取模块名 - 针对CTS Verifier格式"""
    try:
        if not os.path.exists(xml_file):
            raise FileNotFoundError(f"文件不存在: {xml_file}")
        if not os.path.isfile(xml_file):
            raise IsADirectoryError(f"路径指向目录: {xml_file}")
            
        modules_xml = []
        
        # 解析XML文件
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # 查找所有TestCase元素
        for test_case in root.findall('.//TestCase'):
            test_case_name = test_case.get('name', '')
            
            # 查找该TestCase下的所有Test元素
            for test in test_case.findall('.//Test'):
                test_name = test.get('name', '')
                if test_name:
                    # 组合格式: TestCase名称#Test名称
                    full_test_name = f"{test_case_name}#{test_name}"
                    if full_test_name not in modules_xml:
                        modules_xml.append(full_test_name)
        
        # 去重并排序
        modules_xml = sorted(list(set(modules_xml)))
        
        return modules_xml
    except Exception as e:
        raise