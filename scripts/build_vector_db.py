# coding: utf-8
"""
构建法律向量数据库

使用方法：
    python scripts/build_vector_db.py               # 增量更新（不清空旧数据）
    python scripts/build_vector_db.py --clear       # 先清空，再重建（推荐用于文书替换后）
    python scripts/build_vector_db.py --clear --law-dir ./Law-Book
    python scripts/build_vector_db.py --chunk-size 800 --chunk-overlap 50
"""
import os
import sys
import argparse

# ── 路径修正：确保所有相对路径（./chroma_db、./Law-Book 等）都从项目根目录解析 ──
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from law_ai.loader import LawLoader
from law_ai.splitter import LawSplitter
from law_ai.utils import law_index, clear_vectorstore


def build(law_dir: str, chunk_size: int, chunk_overlap: int, clear: bool):
    # ── 1. 可选：清空旧数据 ──────────────────────────────────────────────────
    if clear:
        print("⚠️  正在清空旧的向量数据库（chroma_db/law 集合）和记录管理器缓存...")
        # 先显示清空前的数据量
        from law_ai.utils import get_vectorstore as _gvs
        _vs = _gvs("law")
        before_count = _vs._collection.count()
        print(f"   清空前 Chroma 中有 {before_count} 条向量")
        del _vs
        clear_vectorstore("law")
        print("✅ 清空完成\n")

    # ── 2. 加载文档 ──────────────────────────────────────────────────────────
    print(f"📂 加载法律文书目录：{law_dir}")
    loader = LawLoader(law_dir)
    documents = loader.load()
    print(f"   共加载 {len(documents)} 个文件\n")

    if not documents:
        print("❌ 未找到任何文档，请检查目录路径和文件格式（需为 .md 文件）")
        sys.exit(1)

    # ── 3. 分割文档 ──────────────────────────────────────────────────────────
    print(f"✂️  分割文档（chunk_size={chunk_size}, chunk_overlap={chunk_overlap}）...")
    splitter = LawSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = splitter.split_documents(documents)
    print(f"   共生成 {len(split_docs)} 个文本块\n")

    # ── 4. 写入向量库 ────────────────────────────────────────────────────────
    print("🔢 开始 Embedding 并写入向量数据库...")
    result = law_index(split_docs, show_progress=True)
    
    print("\n✅ 索引完成！")
    print(f"   新增文本块：{result.get('num_added', 0)}")
    print(f"   更新文本块：{result.get('num_updated', 0)}")
    print(f"   跳过（无变化）：{result.get('num_skipped', 0)}")
    print(f"   删除文本块：{result.get('num_deleted', 0)}")


def main():
    parser = argparse.ArgumentParser(description="构建法律向量数据库")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="构建前先清空现有向量数据库（推荐在替换法律文书后使用）"
    )
    parser.add_argument(
        "--law-dir",
        default="./Law-Book",
        help="法律文书目录路径（默认：./Law-Book）"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="文本块大小（默认：1000）"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="文本块重叠大小（默认：100）"
    )
    args = parser.parse_args()
    build(
        law_dir=args.law_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        clear=args.clear,
    )


if __name__ == "__main__":
    main()
