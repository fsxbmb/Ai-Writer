"""
向量数据库服务
使用 Milvus 存储和检索文档向量
"""
import logging
from typing import List, Dict, Optional, Tuple
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility
)

logger = logging.getLogger(__name__)


class VectorStore:
    """Milvus 向量存储服务"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        collection_name: str = "document_chunks"
    ):
        """
        初始化向量存储

        Args:
            host: Milvus 服务器地址
            port: Milvus 服务器端口
            collection_name: 集合名称
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.collection = None
        self.connected = False

    def connect(self):
        """连接到 Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            self.connected = True
            logger.info(f"成功连接到 Milvus: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"连接 Milvus 失败: {e}")
            raise

    def create_collection(self, dimension: int, drop_existing: bool = False):
        """
        创建集合

        Args:
            dimension: 向量维度
            drop_existing: 是否删除已存在的集合
        """
        if not self.connected:
            self.connect()

        # 检查集合是否存在
        has_collection = utility.has_collection(self.collection_name)

        if has_collection and drop_existing:
            utility.drop_collection(self.collection_name)
            has_collection = False
            logger.info(f"已删除旧集合: {self.collection_name}")

        if has_collection:
            # 使用现有集合
            self.collection = Collection(self.collection_name)
            logger.info(f"使用现有集合: {self.collection_name}")
        else:
            # 创建新集合
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="level", dtype=DataType.INT64),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension)
            ]

            schema = CollectionSchema(
                fields=fields,
                description="文档块向量存储",
                enable_dynamic_field=True
            )

            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )

            # 创建索引
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 128}
            }

            self.collection.create_index(
                field_name="vector",
                index_params=index_params
            )

            logger.info(f"创建新集合: {self.collection_name}, 维度: {dimension}")

    def insert_chunks(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ):
        """
        插入文档块

        Args:
            chunks: 文档块列表
            embeddings: 对应的向量列表
        """
        if not self.collection:
            raise ValueError("集合未初始化，请先调用 create_collection")

        try:
            data = [
                [chunk["id"] for chunk in chunks],
                [chunk["document_id"] for chunk in chunks],
                [chunk["chunk_index"] for chunk in chunks],
                [chunk["title"] for chunk in chunks],
                [chunk["content"] for chunk in chunks],
                [chunk["level"] for chunk in chunks],
                embeddings
            ]

            self.collection.insert(data)
            self.collection.flush()

            logger.info(f"成功插入 {len(chunks)} 个文档块")

        except Exception as e:
            logger.error(f"插入文档块失败: {e}")
            raise

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        document_id: Optional[str] = None
    ) -> List[Dict]:
        """
        向量搜索

        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            document_id: 限制搜索范围到特定文档

        Returns:
            搜索结果列表
        """
        # 如果collection未初始化，自动加载
        if not self.collection:
            if not self.connected:
                self.connect()
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                self.collection.load()
            else:
                raise ValueError(f"集合 {self.collection_name} 不存在")

        try:
            # 加载集合到内存
            self.collection.load()

            # 构建搜索参数
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

            # 构建表达式
            expr = f"document_id == '{document_id}'" if document_id else None

            # 执行搜索
            results = self.collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["document_id", "chunk_index", "title", "content", "level"]
            )

            # 格式化结果
            formatted_results = []
            for hit in results[0]:
                formatted_results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "document_id": hit.entity.get("document_id"),
                    "chunk_index": hit.entity.get("chunk_index"),
                    "title": hit.entity.get("title"),
                    "content": hit.entity.get("content"),
                    "level": hit.entity.get("level")
                })

            logger.info(f"搜索完成，返回 {len(formatted_results)} 个结果")
            return formatted_results

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise

    def get_document_chunks(self, document_id: str) -> List[Dict]:
        """
        获取文档的所有块

        Args:
            document_id: 文档 ID

        Returns:
            文档块列表
        """
        if not self.collection:
            raise ValueError("集合未初始化")

        try:
            self.collection.load()

            # 使用 query 获取所有块
            results = self.collection.query(
                expr=f"document_id == '{document_id}'",
                output_fields=["document_id", "chunk_index", "title", "content", "level"]
            )

            # 按 chunk_index 排序
            results.sort(key=lambda x: x.get("chunk_index", 0))

            logger.info(f"获取文档 {document_id} 的 {len(results)} 个块")
            return results

        except Exception as e:
            logger.error(f"获取文档块失败: {e}")
            raise

    def delete_document(self, document_id: str):
        """
        删除文档的所有块

        Args:
            document_id: 文档 ID
        """
        if not self.collection:
            raise ValueError("集合未初始化")

        try:
            self.collection.delete(expr=f"document_id == '{document_id}'")
            self.collection.flush()
            logger.info(f"删除文档 {document_id} 的所有块")
        except Exception as e:
            logger.error(f"删除文档块失败: {e}")
            raise


# 全局向量存储实例
vector_store = VectorStore()
