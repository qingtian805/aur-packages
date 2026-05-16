#!/usr/bin/env python3
"""AUR 包自动更新工具主入口"""

import argparse
import asyncio
import sys

from core.package_updater import PackageUpdater


async def main() -> None:
    """主函数，处理命令行参数并执行相应操作"""
    parser = argparse.ArgumentParser(description="AUR包更新工具")
    parser.add_argument(
        "--package", "-p", nargs="+", metavar="NAME", help="更新指定的包（可指定多个）"
    )
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用的包")
    parser.add_argument("--all", "-a", action="store_true", help="更新所有包")

    args = parser.parse_args()

    updater = PackageUpdater()

    try:
        # 列出所有包
        if args.list:
            updater.list_available_packages()
            return

        # 更新指定的包
        if args.package:
            success_count, total_count = await updater.update_packages(args.package)
            if total_count > 0 and success_count == 0:
                sys.exit(1)
            return

        # 更新所有包
        success_count, total_count = await updater.update_all_packages()
        if total_count > 0 and success_count == 0:
            sys.exit(1)
    finally:
        await updater.close()


if __name__ == "__main__":
    asyncio.run(main())
