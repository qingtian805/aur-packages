"""常量定义模块"""

from enum import Enum

DOWNLOAD_DIR = "downloads"


class ArchEnum(Enum):
    """支持的 CPU 架构"""

    X86_64 = "x86_64"
    AARCH64 = "aarch64"
    LOONG64 = "loong64"
    MIPS64EL = "mips64el"


class HashAlgorithmEnum(Enum):
    """哈希算法"""

    SHA256 = "sha256"
    SHA512 = "sha512"


class ParserEnum(Enum):
    """解析器名称"""

    QQ = "QQParser"
    NAVICAT_PREMIUM_CS = "NavicatPremiumCSParser"
    TRAE = "TraeParser"
    TRAE_SG = "TraeParser_SG"
    TRAE_US = "TraeParser_US"
