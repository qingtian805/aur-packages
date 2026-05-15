"""异步文件下载器模块"""

import asyncio
import time
from collections.abc import Coroutine
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from httpx import AsyncClient
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)


@dataclass(frozen=True)
class DownloadResult:
    """下载结果"""

    arch: str
    success: bool
    file_path: Path | None = None
    error: str | None = None
    retry_count: int = 0
    download_time: float = 0.0
    downloaded_size: int = 0


class Downloader:
    """
    现代化异步下载器

    特性：
    - 异步并发下载（asyncio + httpx）
    - 智能重试（指数退避）
    - 流式下载（内存高效）
    - Rich 进度条（实时显示速度、进度、剩余时间）
    """

    def __init__(
        self,
        client: AsyncClient,
        *,
        max_concurrent: int = 3,
        max_retries: int = 3,
        base_delay: float = 1.0,
        chunk_size: int = 8192,
        show_progress: bool = True,
    ) -> None:
        self.client = client
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.chunk_size = chunk_size
        self.show_progress = show_progress
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def download_file(
        self,
        url: str,
        file_path: Path,
        *,
        arch: str = "unknown",
    ) -> DownloadResult:
        """下载单个文件（支持智能重试）"""
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay: float = self.base_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)

                start_time: float = time.perf_counter()
                file_path.parent.mkdir(parents=True, exist_ok=True)

                async with self._semaphore, self.client.stream("GET", url) as response:
                    response.raise_for_status()

                    downloaded_size: int = 0
                    with file_path.open("wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                            f.write(chunk)
                            downloaded_size += len(chunk)

                download_time: float = time.perf_counter() - start_time

                return DownloadResult(
                    arch=arch,
                    success=True,
                    file_path=file_path,
                    retry_count=attempt,
                    download_time=download_time,
                    downloaded_size=downloaded_size,
                )

            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
                print(f"  [{arch}] 下载失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {url} -> {error_msg}")
                if attempt == self.max_retries:
                    if file_path.exists():
                        file_path.unlink()
                    return DownloadResult(
                        arch=arch,
                        success=False,
                        error=f"{url} -> {error_msg}",
                        retry_count=attempt,
                    )

        return DownloadResult(
            arch=arch,
            success=False,
            error=f"{url} -> Max retries exceeded",
            retry_count=self.max_retries,
        )

    async def download_file_with_progress(
        self,
        url: str,
        file_path: Path,
        progress: Progress,
        task_id: TaskID,
        *,
        arch: str = "unknown",
    ) -> DownloadResult:
        """下载单个文件（带实时进度更新）"""
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay: float = self.base_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)

                start_time: float = time.perf_counter()
                file_path.parent.mkdir(parents=True, exist_ok=True)

                async with self._semaphore, self.client.stream("GET", url) as response:
                    response.raise_for_status()

                    content_length: str | None = response.headers.get("content-length")
                    total_size: int | None = int(content_length) if content_length else None

                    if total_size:
                        progress.update(task_id, total=total_size)
                        progress.start_task(task_id)

                    downloaded_size: int = 0
                    with file_path.open("wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            progress.update(task_id, advance=len(chunk), refresh=True)

                download_time: float = time.perf_counter() - start_time

                return DownloadResult(
                    arch=arch,
                    success=True,
                    file_path=file_path,
                    retry_count=attempt,
                    download_time=download_time,
                    downloaded_size=downloaded_size,
                )

            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
                print(f"  [{arch}] 下载失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {url} -> {error_msg}")
                if attempt == self.max_retries:
                    if file_path.exists():
                        file_path.unlink()
                    return DownloadResult(
                        arch=arch,
                        success=False,
                        error=f"{url} -> {error_msg}",
                        retry_count=attempt,
                    )

        return DownloadResult(
            arch=arch,
            success=False,
            error=f"{url} -> Max retries exceeded",
            retry_count=self.max_retries,
        )

    async def download_all(
        self,
        downloads: dict[str, tuple[str, Path]],
        package_name: str = "package",
    ) -> dict[str, DownloadResult]:
        """
        并行下载多个文件（带进度条）

        Args:
            downloads: {arch: (url, file_path)} 字典
            package_name: 包名称（用于进度条标题）

        Returns:
            {arch: DownloadResult} 字典
        """
        if not downloads:
            return {}

        results: dict[str, DownloadResult] = {}

        if not self.show_progress:
            tasks: list[Coroutine[Any, Any, DownloadResult]] = [
                self.download_file(url, file_path, arch=arch)
                for arch, (url, file_path) in downloads.items()
            ]
            completed_results: list[DownloadResult] = await asyncio.gather(*tasks)

            for arch, result in zip(downloads.keys(), completed_results):
                results[arch] = result

            return results

        progress: Progress = Progress(
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            refresh_per_second=10,
        )

        with progress:
            tasks: list[Coroutine[Any, Any, DownloadResult]] = []
            for arch, (url, file_path) in downloads.items():
                task_id: TaskID = progress.add_task(
                    f"[{package_name}] {arch}",
                    total=None,
                )
                tasks.append(
                    self.download_file_with_progress(
                        url, file_path, progress, task_id, arch=arch
                    )
                )

            completed_results: list[DownloadResult] = await asyncio.gather(*tasks)

            for arch, result in zip(downloads.keys(), completed_results):
                results[arch] = result

        return results
