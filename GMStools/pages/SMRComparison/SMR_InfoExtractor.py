# SMR_InfoExtractor.py
import os
import re
from datetime import datetime
from .SMR_FileUtils import SMR_FileUtils

class SMR_InfoExtractor:
    """SMR信息提取器，专门负责从文件中提取各种信息"""
    
    def __init__(self, file_utils=None):
        self.file_utils = file_utils or SMR_FileUtils()
    
    def extract_fingerprint_from_html(self, directory):
        """从HTML报告中提取Fingerprint"""
        fingerprint = "未找到"
        
        # 查找HTML报告文件
        html_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.html'):
                    html_files.append(os.path.join(root, file))
        
        # 按常见报告文件名排序，优先检查标准报告
        html_files.sort(key=lambda x: (
            0 if 'test_result' in x.lower() else
            1 if 'compatibility' in x.lower() else
            2 if 'gts' in x.lower() else
            3 if 'cts' in x.lower() else 4
        ))
        
        # 从HTML文件中提取Fingerprint
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # 精确匹配格式: <td class="rowtitle">Fingerprint</td><td>指纹值</td>
                    pattern = r'<td[^>]*class="rowtitle"[^>]*>Fingerprint</td>\s*<td[^>]*>([^<]+)</td>'
                    match = re.search(pattern, content, re.IGNORECASE)
                    
                    if match:
                        fingerprint = match.group(1).strip()
                        return fingerprint
                    
                    # 尝试其他可能的格式
                    alternative_patterns = [
                        r'Fingerprint.*?</td>\s*<td[^>]*>([^<]+)</td>',
                        r'<td[^>]*>Fingerprint</td>\s*<td[^>]*>([^<]+)</td>',
                    ]
                    
                    for pattern in alternative_patterns:
                        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                        if match:
                            fingerprint = match.group(1).strip()
                            return fingerprint
            
            except Exception as e:
                print(f"读取HTML文件 {html_file} 时出错: {e}")
        
        return fingerprint
    
    def extract_generic_info(self, directory):
        """从目录中提取GenericDeviceInfo.deviceinfo.json中的信息"""
        generic_info = {
            "build_fingerprint": "未找到",
            "build_version_base_os": "未找到"
        }
        
        # 查找GenericDeviceInfo.deviceinfo.json文件
        json_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower() == 'genericdeviceinfo.deviceinfo.json':
                    json_files.append(os.path.join(root, file))
        
        if json_files:
            # 通常只有一个，取第一个
            json_file = json_files[0]
            try:
                data = self.file_utils.read_json_file(json_file)
                if data:
                    generic_info["build_fingerprint"] = data.get("build_fingerprint", "未找到")
                    generic_info["build_version_base_os"] = data.get("build_version_base_os", "未找到")
            except Exception as e:
                print(f"读取GenericDeviceInfo文件 {json_file} 时出错: {e}")
        
        return generic_info
    
    def extract_security_patch(self, directory):
        """从目录中提取安全补丁日期"""
        security_patch = "未找到"
        
        # 查找HTML报告文件
        html_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.html'):
                    html_files.append(os.path.join(root, file))
        
        # 按常见报告文件名排序，优先检查标准报告
        html_files.sort(key=lambda x: (
            0 if 'test_result' in x.lower() else
            1 if 'compatibility' in x.lower() else
            2 if 'gts' in x.lower() else
            3 if 'cts' in x.lower() else 4
        ))
        
        # 从HTML文件中提取安全补丁日期
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # 精确匹配格式: <td class="rowtitle">Security Patch</td><td>日期</td>
                    pattern = r'<td[^>]*class="rowtitle"[^>]*>Security Patch</td>\s*<td[^>]*>([^<]+)</td>'
                    match = re.search(pattern, content, re.IGNORECASE)
                    
                    if match:
                        security_patch = match.group(1).strip()
                        # 验证日期格式是否为YYYY-MM-DD
                        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
                        if re.match(date_pattern, security_patch):
                            return security_patch
                        else:
                            print(f"警告: 提取的安全补丁日期格式不正确: {security_patch}")
                            return security_patch
                    
                    # 尝试其他可能的格式
                    alternative_patterns = [
                        r'Security Patch.*?</td>\s*<td[^>]*>([^<]+)</td>',
                        r'Security.*?Patch.*?</td>\s*<td[^>]*>([^<]+)</td>',
                        r'<td[^>]*>Security Patch</td>\s*<td[^>]*>([^<]+)</td>',
                    ]
                    
                    for pattern in alternative_patterns:
                        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                        if match:
                            security_patch = match.group(1).strip()
                            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
                            if re.match(date_pattern, security_patch):
                                return security_patch
                            else:
                                print(f"警告: 提取的安全补丁日期格式不正确: {security_patch}")
                                return security_patch
            
            except Exception as e:
                print(f"读取HTML文件 {html_file} 时出错: {e}")
        
        return security_patch
    
    def extract_gms_version(self, directory):
        """从PropertyDeviceInfo.deviceinfo.json中提取GMS版本"""
        gms_version = "未找到"
        
        # 查找PropertyDeviceInfo.deviceinfo.json文件
        json_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower() == 'propertydeviceinfo.deviceinfo.json':
                    json_files.append(os.path.join(root, file))
        
        if json_files:
            # 通常只有一个，取第一个
            json_file = json_files[0]
            try:
                data = self.file_utils.read_json_file(json_file)
                if data and "ro_property" in data:
                    for prop in data["ro_property"]:
                        if prop.get("name") == "ro.com.google.gmsversion":
                            gms_version = prop.get("value", "未找到")
                            break
            except Exception as e:
                print(f"读取PropertyDeviceInfo文件 {json_file} 时出错: {e}")
        
        return gms_version
    
    def extract_mainline_version(self, directory):
        """从MainlineDeviceInfo.deviceinfo.json中提取Mainline版本信息"""
        mainline_info = {
            "type": "unknown",  # "GO" 或 "non-GO"
            "version": "未找到",
            "module_name": "未找到"
        }
        
        # 查找MainlineDeviceInfo.deviceinfo.json文件
        json_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower() == 'mainlinedeviceinfo.deviceinfo.json':
                    json_files.append(os.path.join(root, file))
        
        if json_files:
            # 通常只有一个，取第一个
            json_file = json_files[0]
            try:
                data = self.file_utils.read_json_file(json_file)
                if data and "mainline_modules" in data:
                    # 首先查找GO版本
                    go_found = False
                    for module in data["mainline_modules"]:
                        module_name = module.get("mainline_module_name", "")
                        
                        # 检查是否是GO版本
                        if "com.google.mainline.go.primary" in module_name:
                            mainline_info["type"] = "GO"
                            mainline_info["version"] = module.get("mainline_module_version_name", "未找到")
                            mainline_info["module_name"] = module_name
                            go_found = True
                            break
                    
                    # 如果没有找到GO版本，查找non-GO版本
                    if not go_found:
                        for module in data["mainline_modules"]:
                            module_name = module.get("mainline_module_name", "")
                            
                            # 检查是否是non-GO版本
                            if "com.google.android.modulemetadata" in module_name:
                                mainline_info["type"] = "non-GO"
                                mainline_info["version"] = module.get("mainline_module_version_name", "未找到")
                                mainline_info["module_name"] = module_name
                                break
            except Exception as e:
                print(f"读取MainlineDeviceInfo文件 {json_file} 时出错: {e}")
        
        return mainline_info
    
    def analyze_report_files(self, report_name, directory, prefix, security_patch, extra_info):
        """分析单个报告目录的文件"""
        result = f"{report_name}分析:\n"
        result += "-" * 30 + "\n"
        
        # 显示安全补丁日期
        result += f"安全补丁日期: {security_patch}\n"
        
        # 根据报告类型显示不同信息
        if prefix == "MR":
            # MR报告显示从HTML提取的Fingerprint
            result += f"Fingerprint (从HTML提取): {extra_info}\n"
        else:
            # SMR报告显示GenericDeviceInfo信息
            if extra_info["build_fingerprint"] != "未找到":
                result += f"Build Fingerprint: {extra_info['build_fingerprint']}\n"
            
            if extra_info["build_version_base_os"] != "未找到":
                result += f"Build Version Base OS: {extra_info['build_version_base_os']}\n"
            else:
                result += "Build Version Base OS: 未找到 (SMR应该有此值)\n"
        
        # 查找JSON文件
        feature_file, package_file = self.file_utils.find_json_files_in_directory(directory)
        
        # 记录文件信息
        if feature_file:
            result += f"Feature文件位置: {feature_file}\n"
            result += f"Feature文件大小: {os.path.getsize(feature_file)} bytes\n"
        else:
            result += "未找到 FeatureDeviceInfo.deviceinfo.json 文件\n"
        
        if package_file:
            result += f"Package文件位置: {package_file}\n"
            result += f"Package文件大小: {os.path.getsize(package_file)} bytes\n"
        else:
            result += "未找到 PackageDeviceInfo.deviceinfo.json 文件\n"
        
        result += "\n" + "=" * 50 + "\n\n"
        
        return result