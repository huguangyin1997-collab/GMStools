# 从各个模块导入类
from .CheckupReport import CheckupReport
from .Ctsverifierdb.Ctsverifierdb import Ctsverifierdb
from .Modulecomparison.ModuleComparison import Modulecomparison
from .Concerning.Concerning import Concerning
from .SMRComparison.SMRComparison import SMRComparison
from .CVAutomation.CVAutomation import CVAutomation
from .Disclaimer.Disclaimer import Disclaimer
# 定义导出的名称
__all__ = ['CheckupReport', 'Ctsverifierdb', 'Modulecomparison', 'Concerning',"SMRComparison", "CVAutomation", "Disclaimer"]