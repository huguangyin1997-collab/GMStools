# SMR_Comparator.py
import os
import re
from datetime import datetime
from .SMR_FileUtils import SMR_FileUtils

class SMR_Comparator:
    """SMR核心对比器，负责主要的对比逻辑"""
    
    def __init__(self, file_utils=None):
        self.file_utils = file_utils or SMR_FileUtils()
    
    def compare_security_patches(self, mr_security_patch, smr_security_patch):
        """
        对比安全补丁日期（使用SMR_PatchChecker的验证规则）
        
        Args:
            mr_security_patch: MR安全补丁日期
            smr_security_patch: SMR安全补丁日期
            
        Returns:
            tuple: (result_text, security_patch_result)
        """
        # 导入SMR_PatchChecker进行验证
        from .SMR_PatchChecker import SMR_PatchChecker
        
        # 使用SMR_PatchChecker的严格验证规则
        patch_checker = SMR_PatchChecker()
        patch_result = patch_checker.compare_patches(mr_security_patch, smr_security_patch)
        
        # 根据结果生成文本和状态
        result_text = "安全补丁日期对比（严格验证规则）:\n"
        result_text += f"  MR安全补丁:  {mr_security_patch}\n"
        result_text += f"  SMR安全补丁: {smr_security_patch}\n"
        result_text += f"  参考时间: {patch_checker.reference_time.strftime('%Y-%m-%d %H:%M:%S')} ({patch_checker.time_message})\n"
        
        # 整体判定
        if patch_result['all_checks_passed']:
            result_text += "  ✅ 所有安全补丁检查通过\n"
            security_patch_result = "PASS"
        else:
            result_text += "  ❌ 安全补丁检查未通过\n"
            security_patch_result = "FAIL"
        
        return result_text, security_patch_result
    
    def compare_fingerprint_info(self, mr_fingerprint, smr_generic_info):
        """Base_OS Fingerprint信息对比"""
        result_text = "Base_OS Fingerprint信息对比:\n"
        result_text += f"  MR Fingerprint: {mr_fingerprint}\n"
        result_text += f"  SMR Base OS: {smr_generic_info['build_version_base_os']}\n"
        
        # 检查条件
        # 1. SMR必须有build_version_base_os值
        # 2. SMR的build_version_base_os必须与MR的Fingerprint完全一致
        fingerprint_result = "未知"
        
        if smr_generic_info['build_version_base_os'] == "未找到":
            result_text += "  ❌ FAIL: SMR缺少build_version_base_os值\n"
            fingerprint_result = "FAIL"
        elif mr_fingerprint == "未找到":
            result_text += "  ❌ FAIL: MR缺少Fingerprint值\n"
            fingerprint_result = "FAIL"
        else:
            # 比较SMR的build_version_base_os和MR的Fingerprint
            # 根据要求：必须完全一致才能PASS
            smr_base_os = smr_generic_info['build_version_base_os']
            
            # 去掉可能的末尾空格
            smr_base_os = smr_base_os.strip()
            mr_fingerprint = mr_fingerprint.strip()
            
            # 检查是否完全一致
            if smr_base_os == mr_fingerprint:
                result_text += "  ✅ PASS: SMR的build_version_base_os与MR的Fingerprint完全一致\n"
                fingerprint_result = "PASS"
            else:
                result_text += "  ❌ FAIL: SMR的build_version_base_os与MR的Fingerprint不一致\n"
                result_text += f"    差异详情:\n"
                result_text += f"      MR Fingerprint: {mr_fingerprint}\n"
                result_text += f"      SMR Build Version Base OS: {smr_base_os}\n"
                
                # 显示更详细的差异信息
                if len(mr_fingerprint) != len(smr_base_os):
                    result_text += f"      长度不同: MR={len(mr_fingerprint)}字符, SMR={len(smr_base_os)}字符\n"
                else:
                    result_text += f"      长度相同: {len(mr_fingerprint)}字符\n"
                
                # 找出第一个不同的字符位置
                min_len = min(len(mr_fingerprint), len(smr_base_os))
                for i in range(min_len):
                    if mr_fingerprint[i] != smr_base_os[i]:
                        result_text += f"      第一个差异在第{i+1}个字符: MR='{mr_fingerprint[i]}'(ASCII:{ord(mr_fingerprint[i])}), SMR='{smr_base_os[i]}'(ASCII:{ord(smr_base_os[i])})\n"
                        break
                if len(mr_fingerprint) != len(smr_base_os) and min_len > 0:
                    if len(mr_fingerprint) > len(smr_base_os):
                        result_text += f"      MR多出字符: '{mr_fingerprint[min_len:]}'\n"
                    else:
                        result_text += f"      SMR多出字符: '{smr_base_os[min_len:]}'\n"
                
                fingerprint_result = "FAIL"
        
        return result_text, fingerprint_result
    
    def check_file_existence(self, mr_dir, smr_dir):
        """检查必要的JSON文件是否存在"""
        mr_feature_file, mr_package_file = self.file_utils.find_json_files_in_directory(mr_dir)
        smr_feature_file, smr_package_file = self.file_utils.find_json_files_in_directory(smr_dir)
        
        missing_files = []
        
        if not mr_feature_file:
            missing_files.append("MR FeatureDeviceInfo.deviceinfo.json")
        if not mr_package_file:
            missing_files.append("MR PackageDeviceInfo.deviceinfo.json")
        if not smr_feature_file:
            missing_files.append("SMR FeatureDeviceInfo.deviceinfo.json")
        if not smr_package_file:
            missing_files.append("SMR PackageDeviceInfo.deviceinfo.json")
        
        return {
            "mr_feature_file": mr_feature_file,
            "mr_package_file": mr_package_file,
            "smr_feature_file": smr_feature_file,
            "smr_package_file": smr_package_file,
            "missing_files": missing_files,
            "all_files_exist": len(missing_files) == 0
        }