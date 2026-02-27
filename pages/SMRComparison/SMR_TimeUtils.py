# SMR_TimeUtils.py
from datetime import datetime, timedelta

class SMR_TimeUtils:
    """时间工具类 - 获取系统时间"""
    
    @staticmethod
    def get_system_time():
        """获取系统当前时间"""
        return datetime.now()
    
    @staticmethod
    def get_reference_time():
        """
        获取参考时间（只使用系统时间）
        
        Returns:
            tuple: (reference_time, is_network_time, message)
        """
        reference_time = datetime.now()
        is_network_time = False
        message = "使用本地系统时间"
        
        return reference_time, is_network_time, message
    
    @staticmethod
    def validate_patch_date(patch_date_str, reference_time=None):
        """
        验证安全补丁日期
        
        Args:
            patch_date_str: 安全补丁日期字符串 (YYYY-MM-DD)
            reference_time: 参考时间（datetime对象）
            
        Returns:
            tuple: (is_valid, message, days_diff)
        """
        if patch_date_str == "未找到":
            return False, "安全补丁日期未找到", None
        
        if reference_time is None:
            reference_time = datetime.now()
        
        try:
            # 解析安全补丁日期
            patch_date = datetime.strptime(patch_date_str, '%Y-%m-%d')
            
            # 计算天数差（参考时间 - 补丁日期）
            days_diff = (reference_time - patch_date).days
            
            # 检查是否超过3个月（约90天）
            three_months_ago = reference_time - timedelta(days=90)
            
            # 检查是否超过1个月（约30天）的未来
            one_month_later = reference_time + timedelta(days=30)
            
            if patch_date > one_month_later:
                return False, f"安全补丁日期({patch_date_str})超过参考时间1个月", days_diff
            elif patch_date < three_months_ago:
                return False, f"安全补丁日期({patch_date_str})超过参考时间3个月", days_diff
            else:
                if days_diff < 0:
                    return True, f"安全补丁日期在有效范围内（未来{-days_diff}天）", days_diff
                else:
                    return True, f"安全补丁日期在有效范围内（{days_diff}天前）", days_diff
                    
        except ValueError:
            return False, f"安全补丁日期格式无效: {patch_date_str}", None
        except Exception as e:
            return False, f"安全补丁日期验证错误: {str(e)}", None