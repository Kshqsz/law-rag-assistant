# coding: utf-8
"""
法律文档加载模块

功能说明：
- LawLoader: 自定义目录加载器，继承自 LangChain 的 DirectoryLoader
  专用于加载法律书籍（Markdown 格式）
  自动递归扫描指定目录下的所有 .md 文件
  返回加载的 Document 对象列表

使用示例：
    from law_ai.loader import LawLoader
    
    # 创建加载器，指定法律书籍所在目录
    loader = LawLoader(path="./Law-Book")
    
    # 加载所有法律文档
    documents = loader.load()
    
    print(f"共加载 {len(documents)} 个文档")
    
    # 查看第一个文档的内容
    if documents:
        first_doc = documents[0]
        print(f"文档名: {first_doc.metadata.get('source', '未知')}")
        print(f"内容预览: {first_doc.page_content[:100]}...")
    
    # 文档对象包含两部分：
    # - page_content: 文件的文本内容
    # - metadata: 元数据，包括 source（文件路径）等信息
"""
from typing import Any
from langchain.document_loaders import TextLoader, DirectoryLoader


class LawLoader(DirectoryLoader):
    """Load law books."""
    def __init__(self, path: str, **kwargs: Any) -> None:
        loader_cls = TextLoader
        glob = "**/*.md"
        super().__init__(path, loader_cls = loader_cls, glob = glob, **kwargs)