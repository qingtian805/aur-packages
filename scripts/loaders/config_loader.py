"""配置文件加载模块"""

import yaml
from pydantic import BaseModel, Field

from constants.constants import ArchEnum


class DownloadSettings(BaseModel):
    """下载配置"""

    max_retries: int = 3
    retry_wait: int = 1
    timeout: int = 60
    connections: int = 16
    show_progress: bool = True

    class Config:
        extra = "ignore"


class Settings(BaseModel):
    """全局配置"""

    download: DownloadSettings = Field(default_factory=DownloadSettings)

    class Config:
        extra = "ignore"


class PackageConfig(BaseModel):
    """单个包的配置"""

    name: str
    source: str
    fetch_url: str
    upstream: str
    parser: str
    pkgbuild: str
    arch: list[str] = Field(default_factory=list)
    update_source_url: bool = Field(default=True)
    enable: bool = Field(default=True)

    class Config:
        extra = "ignore"
        validate_by_name = True

    def get_supported_archs(self) -> list[ArchEnum]:
        """将字符串架构列表转换为 ArchEnum 列表"""
        supported_archs = []
        for arch_str in self.arch:
            for arch_enum in ArchEnum:
                if arch_enum.value == arch_str:
                    supported_archs.append(arch_enum)
                    break
        return supported_archs


class ConfigLoader(BaseModel):
    """配置加载器，管理全局设置和包配置"""

    settings: Settings = Field(default_factory=Settings)
    packages: dict[str, PackageConfig] = Field(default_factory=dict)

    class Config:
        extra = "ignore"

    @classmethod
    def load_from_yaml(cls, filepath: str = "config.yaml") -> "ConfigLoader":
        """从 YAML 文件加载配置"""
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)
