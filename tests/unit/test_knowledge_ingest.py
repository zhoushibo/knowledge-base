"""
知识导入模块单元测试
"""

import pytest
import os
import tempfile
from pathlib import Path

# 导入被测试模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.knowledge_ingest import KnowledgeIngest


class TestKnowledgeIngest:
    """知识导入器测试类"""
    
    @pytest.fixture
    def ingest(self):
        """创建测试用的导入器"""
        return KnowledgeIngest(max_file_size_mb=1, chunk_size=1024)
    
    @pytest.fixture
    def temp_md_file(self):
        """创建临时 Markdown 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# 测试文档\n\n这是一个测试段落。\n\n这是第二个段落。")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    @pytest.fixture
    def temp_txt_file(self):
        """创建临时 TXT 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("这是纯文本内容。\n第二行内容。")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    def test_import_markdown_file(self, ingest, temp_md_file):
        """测试导入 Markdown 文件"""
        result = ingest.import_file(temp_md_file)
        
        assert len(result) > 0
        assert "content" in result[0]
        assert "metadata" in result[0]
        assert result[0]["metadata"]["source"] == temp_md_file
    
    def test_import_txt_file(self, ingest, temp_txt_file):
        """测试导入 TXT 文件"""
        result = ingest.import_file(temp_txt_file)
        
        assert len(result) > 0
        assert "这是纯文本内容" in result[0]["content"]
    
    def test_import_nonexistent_file(self, ingest):
        """测试导入不存在的文件"""
        with pytest.raises(FileNotFoundError):
            ingest.import_file("/nonexistent/path/file.md")
    
    def test_import_unsupported_format(self, ingest):
        """测试导入不支持的格式"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write("PDF content")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="不支持的文件格式"):
                ingest.import_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_import_with_metadata(self, ingest, temp_md_file):
        """测试导入时添加元数据"""
        metadata = {"tags": ["测试", "示例"], "author": "Test User"}
        result = ingest.import_file(temp_md_file, metadata=metadata)
        
        assert result[0]["metadata"]["tags"] == ["测试", "示例"]
        assert result[0]["metadata"]["author"] == "Test User"
    
    def test_import_text(self, ingest):
        """测试导入纯文本"""
        text = "这是直接导入的文本内容。"
        result = ingest.import_text(text, source="test_input")
        
        assert len(result) == 1
        assert result[0]["content"] == text
        assert result[0]["metadata"]["source"] == "test_input"
    
    def test_import_text_too_long(self, ingest):
        """测试导入过长文本"""
        long_text = "x" * (ingest.chunk_size * 11)  # 超过限制
        
        with pytest.raises(ValueError, match="文本过长"):
            ingest.import_text(long_text)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
