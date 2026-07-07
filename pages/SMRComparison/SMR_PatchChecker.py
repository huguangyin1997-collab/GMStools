# SMR_PatchChecker.py
import re
from datetime import datetime, timedelta
from .SMR_TimeUtils import SMR_TimeUtils

class SMR_PatchChecker:
    """安全补丁检查器 - 分层验证规则 + 差值要求"""
    
    def __init__(self):
        """
        初始化检查器（不再使用网络时间参数）
        """
        self.reference_time, self.is_network_time, self.time_message = SMR_TimeUtils.get_reference_time()
    
    def validate_single_patch(self, patch_date_str, patch_type="MR"):
        """
        验证单个安全补丁日期

        SMR规则：
        - 超过参考日期 30 天 -> 警告（可能没有测试工具）
        - 低于参考日期 40 天 -> 警告（安全patch有过期的风险）
        - 在 [参考日期-40天, 参考日期+30天] 范围内 -> 有效无警告

        MR规则（保持原有逻辑）：
        - 过去超过 90 天 -> 错误
        - 未来超过 40 天 -> 错误
        - 未来 31-40 天 -> 警告
        - 其他 -> 有效

        Args:
            patch_date_str: 安全补丁日期字符串
            patch_type: 补丁类型 ("MR"/"SMR")

        Returns:
            dict: 验证结果
        """
        if patch_date_str == "未找到":
            return {
                "is_valid": False,
                "warning": False,
                "message": f"{patch_type}安全补丁日期未找到",
                "days_diff": None,
                "status": "not_found"
            }

        # 验证日期格式
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, patch_date_str):
            return {
                "is_valid": False,
                "warning": False,
                "message": f"{patch_type}安全补丁日期格式无效: {patch_date_str}",
                "days_diff": None,
                "status": "invalid_format"
            }

        try:
            # 解析日期
            patch_date = datetime.strptime(patch_date_str, '%Y-%m-%d')

            # 计算天数差（参考时间 - 补丁日期）
            # days_diff > 0: 补丁日期在过去; days_diff < 0: 补丁日期在未来
            days_diff = (self.reference_time - patch_date).days

            if patch_type == "SMR":
                # ===== SMR 专用规则 =====
                # 有效范围：参考日期 - 40天 ≤ SMR ≤ 参考日期 + 30天
                # 超出范围仅警告，不报错

                thirty_days_later = self.reference_time + timedelta(days=30)
                forty_days_ago = self.reference_time - timedelta(days=40)

                if patch_date > thirty_days_later:
                    # 未来超过30天 -> 警告（可能没有测试工具）
                    return {
                        "is_valid": True,
                        "warning": True,
                        "message": f"SMR安全补丁日期({patch_date_str})超过参考时间30天（可能没有测试工具）",
                        "days_diff": days_diff,
                        "status": "too_new_warning",
                        "date_obj": patch_date
                    }
                elif patch_date < forty_days_ago:
                    # 过去超过40天 -> 警告（有过期风险）
                    return {
                        "is_valid": True,
                        "warning": True,
                        "message": f"SMR安全补丁日期({patch_date_str})低于参考时间40天（安全patch有过期的风险）",
                        "days_diff": days_diff,
                        "status": "too_old_warning",
                        "date_obj": patch_date
                    }
                else:
                    # 在 [-40, +30] 天范围内 -> 有效无警告
                    status = "future" if days_diff < 0 else "past"
                    time_desc = f"未来{-days_diff}天" if days_diff < 0 else f"{days_diff}天前"
                    return {
                        "is_valid": True,
                        "warning": False,
                        "message": f"SMR安全补丁日期在有效范围内（{time_desc}）",
                        "days_diff": days_diff,
                        "status": status,
                        "date_obj": patch_date
                    }
            else:
                # ===== MR 原有规则（仅做日期解析，不做严格有效期校验） =====
                # 过去限制：不能小于当前时间3个月（90天）
                three_months_ago = self.reference_time - timedelta(days=90)
                if patch_date < three_months_ago:
                    return {
                        "is_valid": False,
                        "warning": False,
                        "message": f"MR安全补丁日期({patch_date_str})超过参考时间3个月，超过维护期限",
                        "days_diff": days_diff,
                        "status": "too_old",
                        "date_obj": patch_date
                    }

                # 未来限制分层
                forty_days_later = self.reference_time + timedelta(days=40)
                thirty_days_later = self.reference_time + timedelta(days=30)

                if patch_date > forty_days_later:
                    return {
                        "is_valid": False,
                        "warning": False,
                        "message": f"MR安全补丁日期({patch_date_str})超过参考时间40天（可能是Google未发布的安全patch）",
                        "days_diff": days_diff,
                        "status": "too_new_error",
                        "date_obj": patch_date
                    }
                elif patch_date > thirty_days_later:
                    return {
                        "is_valid": True,
                        "warning": True,
                        "message": f"MR安全补丁日期({patch_date_str})超过参考时间30天但未超过40天（警告）",
                        "days_diff": days_diff,
                        "status": "too_new_warning",
                        "date_obj": patch_date
                    }
                else:
                    status = "future" if days_diff < 0 else "past"
                    time_desc = f"未来{-days_diff}天" if days_diff < 0 else f"{days_diff}天前"
                    return {
                        "is_valid": True,
                        "warning": False,
                        "message": f"MR安全补丁日期在有效范围内（{time_desc}）",
                        "days_diff": days_diff,
                        "status": status,
                        "date_obj": patch_date
                    }

        except Exception as e:
            return {
                "is_valid": False,
                "warning": False,
                "message": f"{patch_type}安全补丁日期验证错误: {str(e)}",
                "days_diff": None,
                "status": "error"
            }
    
    def compare_patches(self, mr_patch_str, smr_patch_str):
        """
        对比MR和SMR的安全补丁日期
        
        要求：SMR补丁必须比MR补丁至少大30天
        
        Returns:
            dict: 对比结果
        """
        # 获取时间信息
        time_info = f"参考时间: {self.reference_time.strftime('%Y-%m-%d %H:%M:%S')} ({self.time_message})"
        
        # 检查MR补丁（仅解析日期，不做有效期校验，MR作为旧基线允许超期）
        mr_result = self.validate_single_patch(mr_patch_str, "MR")

        # 检查SMR补丁（完整校验）
        smr_result = self.validate_single_patch(smr_patch_str, "SMR")

        # 检查是否有警告
        has_warning = mr_result.get("warning", False) or smr_result.get("warning", False)

        # 比较结果：只要两边都能解析出日期，就做 SMR vs MR 比较
        comparison_result = "unknown"
        comparison_message = ""

        if 'date_obj' in mr_result and 'date_obj' in smr_result:
            mr_date = mr_result["date_obj"]
            smr_date = smr_result["date_obj"]

            diff_days = (smr_date - mr_date).days

            if diff_days >= 30:
                comparison_result = "pass"
                comparison_message = f"✅ SMR安全补丁日期大于MR安全补丁日期，且相差{diff_days}天（≥30天）"
            else:
                comparison_result = "fail_insufficient_diff"
                comparison_message = f"❌ SMR安全补丁日期与MR安全补丁日期相差{diff_days}天（要求至少30天）"
        else:
            comparison_result = "invalid_input"
            comparison_message = "⚠️ 输入的安全补丁日期无效，无法比较"

        # 计算整体有效性：仅要求 SMR 单独有效 + 比较通过（MR 不参与有效性判断）
        overall_valid = (
            smr_result["is_valid"] and
            comparison_result == "pass"
        )
        
        return {
            "time_info": time_info,
            "mr": mr_result,
            "smr": smr_result,
            "comparison": {
                "result": comparison_result,
                "message": comparison_message,
                "is_valid": comparison_result == "pass"
            },
            "overall_valid": overall_valid,
            "all_checks_passed": overall_valid,
            "has_warning": has_warning
        }
    
    def generate_strict_validation_report(self, mr_patch_str, smr_patch_str):
        """
        生成验证报告
        
        Returns:
            str: 验证报告文本
        """
        result = self.compare_patches(mr_patch_str, smr_patch_str)
        
        report = "安全补丁严格验证结果:\n"
        report += "=" * 50 + "\n"
        report += f"{result['time_info']}\n"
        report += "-" * 50 + "\n"
        
        # MR验证结果
        report += f"MR安全补丁: {mr_patch_str}\n"
        report += f"  验证结果: {result['mr']['message']}\n"
        
        # SMR验证结果
        report += f"SMR安全补丁: {smr_patch_str}\n"
        report += f"  验证结果: {result['smr']['message']}\n"
        
        # 对比结果
        report += f"对比验证: {result['comparison']['message']}\n"
        
        # 整体判定
        report += "-" * 50 + "\n"
        if result['all_checks_passed']:
            if result.get('has_warning', False):
                report += "⚠️ 安全补丁检查通过，但存在警告项（详见上方警告信息）\n"
            else:
                report += "✅ 所有安全补丁检查通过\n"
            report += "   - MR安全补丁在有效范围内\n"
            report += "   - SMR安全补丁在有效范围内\n"
            report += "   - SMR安全补丁大于MR安全补丁\n"
        else:
            report += "❌ 安全补丁检查未通过\n"
            
            fail_reasons = []
            if not result['smr']['is_valid']:
                fail_reasons.append("SMR安全补丁无效")
            if not result['comparison']['is_valid']:
                fail_reasons.append("SMR补丁与MR补丁差值不足30天")
            
            report += f"  失败原因: {'; '.join(fail_reasons)}\n"
        
        report += "\n验证规则说明:\n"
        report += "1. 仅对SMR安全补丁做有效期校验（MR作为旧基线不做校验）\n"
        report += "2. SMR安全补丁超过参考时间30天时，发出警告（可能没有测试工具）\n"
        report += "3. SMR安全补丁低于参考时间40天时，发出警告（安全patch有过期的风险）\n"
        report += "4. SMR安全补丁在[参考日期-40天, 参考日期+30天]范围内为有效\n"
        report += "5. SMR安全补丁必须大于MR安全补丁，且至少相差30天\n"
        report += "6. 使用本地系统时间作为参考时间\n"
        
        return report