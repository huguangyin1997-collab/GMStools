import os
import json

class SMR_FileUtils:
    """SMR对比的文件操作工具类"""
    
    @staticmethod
    def read_json_file(file_path):
        """读取JSON文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
        except Exception as e:
            print(f"读取文件错误: {e}")
            return None
    
    @staticmethod
    def find_json_files_in_directory(directory):
        """在目录中查找指定的JSON文件"""
        feature_file = None
        package_file = None
        
        # 遍历目录及其子目录
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file == "FeatureDeviceInfo.deviceinfo.json":
                    feature_file = os.path.join(root, file)
                elif file == "PackageDeviceInfo.deviceinfo.json":
                    package_file = os.path.join(root, file)
                
                # 如果两个文件都找到了，就停止搜索
                if feature_file and package_file:
                    break
            
            if feature_file and package_file:
                break
        
        return feature_file, package_file
    
    @staticmethod
    def format_json_content(json_data, title):
        """格式化JSON内容为可读的文本"""
        if json_data is None:
            return f"{title}: 文件不存在或读取失败\n"
        
        result = f"{title}:\n"
        try:
            # 尝试提取常见字段
            if isinstance(json_data, dict):
                for key, value in json_data.items():
                    result += f"  {key}: {value}\n"
            elif isinstance(json_data, list):
                for i, item in enumerate(json_data[:5]):  # 只显示前5项
                    result += f"  [{i}]: {item}\n"
                if len(json_data) > 5:
                    result += f"  ... (共{len(json_data)}项，显示前5项)\n"
            else:
                result += f"  内容: {json_data}\n"
        except:
            result += f"  内容: {json_data}\n"
        
        return result + "\n"