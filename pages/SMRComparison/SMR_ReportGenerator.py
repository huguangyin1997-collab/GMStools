class SMR_ReportGenerator:
    """SMR报告生成器，负责生成各种格式的报告"""
    
    def generate_summary_report(self, security_patch_result, fingerprint_result, 
                               feature_result_status, package_result_status,
                               mr_security_patch, smr_security_patch,
                               gms_result=None, mainline_result=None):
        """生成分析摘要报告"""
        result = "分析摘要:\n"
        result += "-" * 30 + "\n"
        result += f"  1. 安全补丁对比结果: MR={mr_security_patch}, SMR={smr_security_patch} {security_patch_result} \n"
        result += f"  2. Base_OS Fingerprint对比结果: {fingerprint_result}\n"
        result += f"  3. Feature DeviceInfo对比结果: {feature_result_status}\n"
        result += f"  4. Package DeviceInfo对比结果: {package_result_status}\n"
        
        # 新增的GMS包版本对比
        if gms_result is not None:
            result += f"  5. GMS包版本对比结果: {gms_result}\n"
        
        # 新增的Mainline版本对比
        if mainline_result is not None:
            result += f"  6. Mainline版本对比结果: {mainline_result}\n"
        
        result += "  7. 对比范围: Feature和Package设备信息\n"
        result += "  8. 详细报告: 请查看生成的HTML文件\n"
        
        return result
    
    def generate_final_verdict(self, security_patch_result, fingerprint_result,
                              feature_result_status, package_result_status,
                              gms_result=None, mainline_result=None):
        """生成最终判定结果"""
        result = "\n最终判定结果:\n"
        result += "-" * 30 + "\n"
        
        # 收集所有检查结果
        all_results = {
            "安全补丁日期": security_patch_result,
            "Fingerprint": fingerprint_result,
            "Feature DeviceInfo": feature_result_status,
            "Package DeviceInfo": package_result_status
        }
        
        # 添加新检查项
        if gms_result is not None:
            all_results["GMS包版本"] = gms_result
        
        if mainline_result is not None:
            all_results["Mainline版本"] = mainline_result
        
        # 检查所有条件是否都满足
        all_pass = all(result == "PASS" for result in all_results.values())
        
        if all_pass:
            result += "  ✅ 整体结果: PASS (所有检查项通过，可以走SMR)\n"
        else:
            result += "  ❌ 整体结果: FAIL (存在检查项未通过，不能走SMR)\n"
            fail_reasons = []
            
            for check_name, check_result in all_results.items():
                if check_result != "PASS":
                    fail_reasons.append(f"{check_name}检查未通过")
            
            if fail_reasons:
                result += f"     失败原因: {'; '.join(fail_reasons)}\n"
        
        return result