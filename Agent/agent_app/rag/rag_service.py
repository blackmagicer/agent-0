
"""
Agentic RAG 服务类：提供知识库检索、文件元信息、chunk 读取与总结能力。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from agent_app.model.factory import chat_model
from agent_app.rag.vector_store import VectorStoreService
from agent_app.utils.config_handler import chroma_conf
from agent_app.utils.file_handler import get_file_md5_hex, listdir_with_allowed_type, pdf_loader, txt_loader
from agent_app.utils.path_tool import get_abs_path
from agent_app.utils.prompt_loader import load_rag_prompts


def print_prompt(prompt):
    print("=" * 20)
    print(prompt.to_string())
    print("=" * 20)
    return prompt


@dataclass
class FileChunk:
    """文件片段"""

    file_id: int
    chunk_index: int
    content: str


@dataclass
class FileInfo:
    """文件信息"""

    id: int
    filename: str
    chunk_count: int
    status: str = "done"


class RagSummarizeService(object):
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_prompts()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._init_chain()
        self.files = self._build_files()
        self.chunks = self._build_chunks()

    def _init_chain(self):
        chain = self.prompt_template | print_prompt | self.model | StrOutputParser()
        return chain

    def _get_source_files(self) -> list[str]:
        data_path = get_abs_path(chroma_conf["data_path"])
        allowed_types = tuple(chroma_conf["allow_knowledge_file_type"])
        return list(listdir_with_allowed_type(data_path, allowed_types))

    def _load_source_documents(self, path: str) -> list[Document]:
        if path.endswith("txt"):
            return txt_loader(path)
        if path.endswith("pdf"):
            return pdf_loader(path)
        return []

    def _build_files(self) -> list[FileInfo]:
        files = []
        for index, path in enumerate(self._get_source_files(), start=1):
            try:
                documents = self._load_source_documents(path)
                chunk_count = len(self.vector_store.spliter.split_documents(documents)) if documents else 0
                files.append(FileInfo(index, os.path.basename(path), chunk_count))
            except Exception:
                files.append(FileInfo(index, os.path.basename(path), 0, status="error"))
        return files

    def _build_chunks(self) -> dict[tuple[int, int], FileChunk]:
        chunks = {}
        for file_info in self.files:
            source_path = next(
                (path for path in self._get_source_files() if os.path.basename(path) == file_info.filename),
                None,
            )
            if not source_path:
                continue
            try:
                documents = self._load_source_documents(source_path)
                split_documents = self.vector_store.spliter.split_documents(documents)
                for chunk_index, doc in enumerate(split_documents):
                    content = (doc.page_content or "").strip()
                    chunks[(file_info.id, chunk_index)] = FileChunk(file_info.id, chunk_index, content)
            except Exception:
                continue
        return chunks

    def _normalize_text(self, text: str) -> str:
        return (text or "").strip().lower()

    def _score_doc(self, query: str, doc: Document) -> int:
        query_tokens = [token for token in self._normalize_text(query).split() if token]
        content = self._normalize_text(doc.page_content)
        metadata_text = self._normalize_text(str(doc.metadata))
        score = 0
        for token in query_tokens:
            if token in content:
                score += 2
            if token in metadata_text:
                score += 1
        return score

    def _select_docs(self, query: str, docs: list[Document], top_k: int = 3) -> list[Document]:
        unique_docs = []
        seen = set()
        for doc in docs:
            marker = (doc.page_content, str(doc.metadata))
            if marker in seen:
                continue
            seen.add(marker)
            unique_docs.append(doc)

        unique_docs.sort(key=lambda doc: self._score_doc(query, doc), reverse=True)
        return unique_docs[:top_k]

    def _build_context(self, docs: list[Document]) -> str:
        context = ""
        for counter, doc in enumerate(docs, start=1):
            context += f"【参考资料{counter}】: 参考资料：{doc.page_content} | 参考元数据：{doc.metadata}\n"
        return context

    def _convert_chunk_to_doc(self, chunk: FileChunk) -> Document:
        file_info = next((f for f in self.files if f.id == chunk.file_id), None)
        metadata = {
            "file_id": chunk.file_id,
            "chunk_index": chunk.chunk_index,
            "filename": file_info.filename if file_info else "",
            "chunk_count": file_info.chunk_count if file_info else 0,
            "status": file_info.status if file_info else "done",
        }
        return Document(page_content=chunk.content, metadata=metadata)

    def _build_query_variants(self, query: str) -> list[str]:
        normalized = " ".join((query or "").strip().split())
        variants = []

        for candidate in [
            normalized,
            normalized.replace("，", " ").replace("。", " ").replace("、", " ").replace("/", " "),
            normalized.replace("建议", "").replace("怎么", "").replace("如何", "").replace("请问", "").strip(),
        ]:
            candidate = " ".join(candidate.split())
            if candidate and candidate not in variants:
                variants.append(candidate)

        return variants or [query]

    def _get_file_info(self, file_id: int) -> Optional[FileInfo]:
        return next((file for file in self.files if file.id == file_id), None)

    def query_knowledge_base(self, query: str) -> str:
        docs = self.retriever_docs(query)
        results = []
        for index, doc in enumerate(docs, start=1):
            results.append(
                {
                    "rank": index,
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
            )
        return json.dumps(results, ensure_ascii=False, indent=2)

    def get_files_meta(self, file_ids: List[int]) -> str:
        if not file_ids:
            return "请提供文件ID数组"

        results = []
        for file_id in file_ids:
            file_info = self._get_file_info(file_id)
            if file_info:
                results.append(
                    {
                        "id": file_info.id,
                        "filename": file_info.filename,
                        "chunk_count": file_info.chunk_count,
                        "status": file_info.status,
                    }
                )
        return json.dumps(results, ensure_ascii=False, indent=2)

    def read_file_chunks(self, chunks: List[Dict[str, int]]) -> str:
        if not chunks:
            return "请提供要读取的chunk信息数组"

        results = []
        for chunk_spec in chunks:
            file_id = chunk_spec.get("fileId")
            chunk_index = chunk_spec.get("chunkIndex")
            chunk = self.chunks.get((file_id, chunk_index))
            if chunk:
                file_info = self._get_file_info(file_id)
                results.append(
                    {
                        "file_id": file_id,
                        "chunk_index": chunk_index,
                        "filename": file_info.filename if file_info else "",
                        "content": chunk.content,
                    }
                )
        return json.dumps(results, ensure_ascii=False, indent=2)

    def list_files(self, page: int = 0, pageSize: int = 10) -> str:
        start = page * pageSize
        end = start + pageSize
        results = [
            {
                "id": file_info.id,
                "filename": file_info.filename,
                "chunk_count": file_info.chunk_count,
                "status": file_info.status,
            }
            for file_info in self.files[start:end]
        ]
        return json.dumps(results, ensure_ascii=False, indent=2)

    def retriever_docs(self, query: str) -> list[Document]:
        try:
            docs = self.retriever.invoke(query)
            if docs:
                return docs
        except Exception:
            pass

        normalized_query = self._normalize_text(query)
        if normalized_query:
            matched = [self._convert_chunk_to_doc(chunk) for chunk in self.chunks.values()]
            matched_docs = [doc for doc in matched if self._score_doc(query, doc) > 0]
            if matched_docs:
                matched_docs.sort(key=lambda doc: self._score_doc(query, doc), reverse=True)
                return matched_docs[:5]

        return [self._convert_chunk_to_doc(chunk) for chunk in self.chunks.values()][:5]

    def rag_summarize(self, query: str) -> str:
        context_docs = self.retriever_docs(query)
        context = ""
        counter = 0
        for doc in context_docs:
            counter += 1
            context += f"【参考资料{counter}】: 参考资料：{doc.page_content} | 参考元数据：{doc.metadata}\n"

        return self.chain.invoke(
            {
                "input": query,
                "context": context,
            }
        )

    def rebuild_index(self):
        """重建整个知识库索引（files + chunks + 向量库）"""
        self.vector_store.rebuild_store()
        self.files = self._build_files()
        self.chunks = self._build_chunks()

    def sync_file(self, filepath: str) -> dict:
        """
        将单个文件同步到知识库索引：计算 md5，若不在已有记录中则加载并写入向量库。
        返回 {"status": "added"|"skipped", "filename": str, "chunk_count": int}
        """
        from agent_app.utils.logger_handler import logger
        if not os.path.exists(filepath):
            return {"status": "error", "filename": os.path.basename(filepath), "chunk_count": 0, "message": "文件不存在"}

        md5_hex = get_file_md5_hex(filepath)
        if not md5_hex:
            return {"status": "error", "filename": os.path.basename(filepath), "chunk_count": 0, "message": "无法计算文件 md5"}

        md5_store = self.vector_store.get_md5_store_path()
        if not os.path.exists(md5_store):
            open(md5_store, "w", encoding="utf-8").close()
        with open(md5_store, "r", encoding="utf-8") as f:
            existing = set(line.strip() for line in f if line.strip())

        filename = os.path.basename(filepath)
        if md5_hex in existing:
            logger.info(f"[sync_file]文件 {filename} (md5={md5_hex[:8]}) 已存在，跳过")
            file_info = next((fi for fi in self.files if fi.filename == filename), None)
            return {
                "status": "skipped",
                "filename": filename,
                "chunk_count": file_info.chunk_count if file_info else 0
            }

        documents = self._load_source_documents(filepath)
        if not documents:
            return {"status": "error", "filename": filename, "chunk_count": 0, "message": "无法解析文件内容"}

        split_docs = self.vector_store.spliter.split_documents(documents)
        if not split_docs:
            return {"status": "error", "filename": filename, "chunk_count": 0, "message": "文件分片后无有效内容"}

        file_id = len(self.files) + 1
        chunk_count = len(split_docs)
        for ci, doc in enumerate(split_docs):
            doc.metadata = dict(doc.metadata or {})
            doc.metadata.update({
                "file_id": file_id,
                "chunk_index": ci,
                "filename": filename,
                "chunk_count": chunk_count,
                "status": "done",
                "source": filepath,
            })

        self.vector_store.vector_store.add_documents(split_docs)

        with open(md5_store, "a", encoding="utf-8") as f:
            f.write(md5_hex + "\n")

        self.files = self._build_files()
        self.chunks = self._build_chunks()

        logger.info(f"[sync_file]文件 {filename} 已入库，{chunk_count} 个 chunk")
        return {"status": "added", "filename": filename, "chunk_count": chunk_count}

    def _collect_evidence(self, query: str):
        file_list_text = self.list_files(page=0, pageSize=10)
        last_query_result_text = ""
        last_candidate_file_ids = []
        last_candidate_chunks = []
        last_files_meta_text = ""
        last_read_chunks_text = ""

        for attempt, query_variant in enumerate(self._build_query_variants(query), start=1):
            query_result_text = self.query_knowledge_base(query_variant)
            query_result = json.loads(query_result_text) if query_result_text else []

            candidate_file_ids = []
            candidate_chunks = []
            for item in query_result[:5]:
                metadata = item.get("metadata", {}) or {}
                file_id = metadata.get("file_id")
                chunk_index = metadata.get("chunk_index")
                if file_id is not None and file_id not in candidate_file_ids:
                    candidate_file_ids.append(file_id)
                if file_id is not None and chunk_index is not None:
                    candidate_chunks.append({"fileId": file_id, "chunkIndex": chunk_index})

            files_meta_text = self.get_files_meta(candidate_file_ids)
            read_chunks_text = self.read_file_chunks(candidate_chunks[:3])

            last_query_result_text = query_result_text
            last_candidate_file_ids = candidate_file_ids
            last_candidate_chunks = candidate_chunks
            last_files_meta_text = files_meta_text
            last_read_chunks_text = read_chunks_text

            if read_chunks_text and read_chunks_text != "[]":
                break

        return {
            "file_list_text": file_list_text,
            "query_result_text": last_query_result_text,
            "candidate_file_ids": last_candidate_file_ids,
            "candidate_chunks": last_candidate_chunks,
            "files_meta_text": last_files_meta_text,
            "read_chunks_text": last_read_chunks_text,
        }

    def agentic_rag(self, query: str) -> str:
        evidence = self._collect_evidence(query)
        forced_context = (
            f"【文件列表】{evidence['file_list_text']}\n"
            f"【候选检索结果】{evidence['query_result_text']}\n"
            f"【候选文件元信息】{evidence['files_meta_text']}\n"
            f"【精读chunk】{evidence['read_chunks_text']}\n"
        )
        return self.chain.invoke(
            {
                "input": query,
                "context": forced_context,
            }
        )


if __name__ == '__main__':
    rag = RagSummarizeService()

    print(rag.agentic_rag("小户型适合哪些扫地机器人"))
