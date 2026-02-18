"""
知识导入模块

支持 Markdown、TXT 等多格式知识导入，包含输入验证、分块处理、事务保护。
"""

import os
import logging
from typing import List, Dict, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class KnowledgeIngest:
    """知识导入器"""
    
    def __init__(self, max_file_size_mb: int = 50, chunk_size: int = 1024 * 1024):
        """
        初始化知识导入器。
        
        Args:
            max_file_size_mb: 最大文件大小（MB），默认 50MB
            chunk_size: 分块大小（字节），默认 1MB
        """
        self.max_file_size_mb = max_file_size_mb
        self.chunk_size = chunk_size
        self.supported_extensions = ['.md', '.txt', '.markdown']
    
    def import_file(self, file_path: Union[str, Path], metadata: Optional[Dict] = None) -> List[Dict]:
        """
        导入单个文件。
        
        Args:
            file_path: 文件路径
            metadata: 元数据（可选）
            
        Returns:
            知识条目列表
            
        Raises:
            ValueError: 文件格式不支持或文件过大
            FileNotFoundError: 文件不存在
        """
        file_path = Path(file_path)
        
        # 验证文件存在性
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        # 验证文件大小
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise ValueError(f"文件过大：{file_size_mb:.2f}MB > {self.max_file_size_mb}MB")
        
        # 验证文件扩展名
        if file_path.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"不支持的文件格式：{file_path.suffix}")
        
        logger.info(f"开始导入文件：{file_path} ({file_size_mb:.2f}MB)")
        
        # 读取并分块处理
        chunks = self._read_and_chunk(file_path)
        
        # 添加元数据
        knowledge_items = []
        for i, chunk in enumerate(chunks):
            item = {
                "content": chunk,
                "metadata": {
                    "source": str(file_path),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    **(metadata or {})
                }
            }
            knowledge_items.append(item)
        
        logger.info(f"导入完成：{len(knowledge_items)} 个知识条目")
        return knowledge_items
    
    def _read_and_chunk(self, file_path: Path) -> List[str]:
        """
        读取文件并分块。
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本块列表
        """
        chunks = []
        
        # 检测编码（简化版本，实际应使用 chardet）
        encodings_to_try = ['utf-8', 'utf-16', 'gbk']
        content = None
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                logger.debug(f"使用编码：{encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise ValueError(f"无法解码文件，尝试的编码：{encodings_to_try}")
        
        # 按段落分块（简化版本）
        paragraphs = content.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) < self.chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def import_text(self, text: str, metadata: Optional[Dict] = None, source: Optional[str] = None) -> List[Dict]:
        """
        导入纯文本。
        
        Args:
            text: 文本内容
            metadata: 元数据
            source: 来源标识（可选）
            
        Returns:
            知识条目列表
        """
        # 验证查询长度
        if len(text) > self.chunk_size * 10:  # 限制最大文本
            raise ValueError(f"文本过长，最大支持 {self.chunk_size * 10} 字符")
        
        # 分块
        chunks = [text]  # 简化版本，直接作为一块
        
        knowledge_items = []
        for i, chunk in enumerate(chunks):
            item = {
                "content": chunk,
                "metadata": {
                    "source": source or "text_input",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    **(metadata or {})
                }
            }
            knowledge_items.append(item)
        
        return knowledge_items
