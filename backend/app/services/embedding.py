"""
文本向量化服务
使用 Ollama 本地模型生成文本嵌入向量
"""
import logging
import httpx
from typing import List, Union
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """文本嵌入服务 - 使用 Ollama"""

    def __init__(
        self,
        model_name: str = "qwen3-embedding:8b",
        ollama_base_url: str = "http://localhost:11434"
    ):
        """
        初始化嵌入服务

        Args:
            model_name: Ollama 模型名称（支持 embedding 的模型）
            ollama_base_url: Ollama 服务地址
        """
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.client = None
        self.dimension = 768  # qwen2.5 默认维度，会根据实际调整

    def get_client(self):
        """获取 HTTP 客户端"""
        if self.client is None:
            self.client = httpx.Client(timeout=300.0)  # 5分钟超时
        return self.client

    async def encode_async(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        异步将文本编码为向量

        Args:
            texts: 单个文本或文本列表

        Returns:
            向量数组，形状为 (n, dimension)
        """
        if isinstance(texts, str):
            texts = [texts]

        client = self.get_client()
        embeddings = []

        try:
            for text in texts:
                response = await client.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                result = response.json()

                if "embedding" in result:
                    embedding = np.array(result["embedding"], dtype=np.float32)
                    embeddings.append(embedding)

                    # 更新维度
                    if self.dimension != len(embedding):
                        self.dimension = len(embedding)
                        logger.info(f"更新向量维度为: {self.dimension}")

            logger.info(f"成功编码 {len(texts)} 个文本")
            return np.array(embeddings)

        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            raise

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        将文本编码为向量（同步版本）

        Args:
            texts: 单个文本或文本列表

        Returns:
            向量数组，形状为 (n, dimension)
        """
        if isinstance(texts, str):
            texts = [texts]

        client = self.get_client()
        embeddings = []
        expected_dim = None

        try:
            for i, text in enumerate(texts):
                try:
                    response = client.post(
                        f"{self.ollama_base_url}/api/embeddings",
                        json={
                            "model": self.model_name,
                            "prompt": text
                        },
                        timeout=60.0  # 单个请求60秒超时
                    )
                    response.raise_for_status()
                    result = response.json()

                    if "embedding" in result:
                        embedding = np.array(result["embedding"], dtype=np.float32)

                        # 跳过空向量
                        if len(embedding) == 0:
                            logger.warning(f"第 {i} 个文本的向量为空，跳过")
                            continue

                        # 设置期望的维度（使用第一个成功的向量）
                        if expected_dim is None:
                            expected_dim = len(embedding)
                            self.dimension = expected_dim
                            logger.info(f"设置向量维度为: {expected_dim}")

                        # 检查向量维度一致性
                        if len(embedding) != expected_dim:
                            logger.warning(f"第 {i} 个文本的向量维度 ({len(embedding)}) 与期望维度 ({expected_dim}) 不一致，跳过")
                            continue

                        embeddings.append(embedding)

                except Exception as e:
                    logger.warning(f"编码第 {i} 个文本失败: {e}，跳过")
                    continue

            if not embeddings:
                raise ValueError("没有成功编码任何文本")

            logger.info(f"成功编码 {len(embeddings)} 个文本，向量维度: {len(embeddings[0])}")
            return np.array(embeddings)

        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            raise

    def encode_with_indices(self, texts: List[str]) -> tuple[List[int], np.ndarray]:
        """
        编码文本并返回成功的索引和向量

        Args:
            texts: 文本列表

        Returns:
            (成功的索引列表, 向量数组)
        """
        client = self.get_client()
        embeddings = []
        successful_indices = []
        expected_dim = None

        try:
            for i, text in enumerate(texts):
                try:
                    response = client.post(
                        f"{self.ollama_base_url}/api/embeddings",
                        json={
                            "model": self.model_name,
                            "prompt": text
                        },
                        timeout=60.0
                    )
                    response.raise_for_status()
                    result = response.json()

                    if "embedding" in result:
                        embedding = np.array(result["embedding"], dtype=np.float32)

                        # 跳过空向量
                        if len(embedding) == 0:
                            logger.warning(f"第 {i} 个文本的向量为空，跳过")
                            continue

                        # 设置期望的维度
                        if expected_dim is None:
                            expected_dim = len(embedding)
                            self.dimension = expected_dim
                            logger.info(f"设置向量维度为: {expected_dim}")

                        # 检查向量维度一致性
                        if len(embedding) != expected_dim:
                            logger.warning(f"第 {i} 个文本的向量维度 ({len(embedding)}) 与期望维度 ({expected_dim}) 不一致，跳过")
                            continue

                        embeddings.append(embedding)
                        successful_indices.append(i)

                except Exception as e:
                    logger.warning(f"编码第 {i} 个文本失败: {e}，跳过")
                    continue

            if not embeddings:
                raise ValueError("没有成功编码任何文本")

            logger.info(f"成功编码 {len(embeddings)} 个文本（共 {len(texts)} 个），向量维度: {len(embeddings[0])}")
            return successful_indices, np.array(embeddings)

        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            raise

    def encode_single(self, text: str) -> List[float]:
        """
        编码单个文本，返回列表格式

        Args:
            text: 文本内容

        Returns:
            向量列表
        """
        embedding = self.encode(text)
        return embedding[0].tolist()

    def unload_model(self):
        """
        卸载 Ollama 模型，释放 GPU 显存
        """
        try:
            client = self.get_client()
            # 使用 Ollama 的 API 卸载模型
            response = client.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": "",
                    "keep_alive": -1  # -1 表示立即卸载模型
                }
            )
            logger.info(f"已卸载模型 {self.model_name}，释放 GPU 显存")
            return True
        except Exception as e:
            logger.error(f"卸载模型失败: {e}")
            return False

    def test_connection(self) -> bool:
        """测试 Ollama 连接"""
        try:
            client = self.get_client()
            response = client.get(f"{self.ollama_base_url}/api/tags")
            response.raise_for_status()

            # 检查模型是否存在
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]

            if self.model_name in model_names:
                logger.info(f"Ollama 连接成功，模型 {self.model_name} 可用")
                return True
            else:
                logger.warning(f"模型 {self.model_name} 不在可用模型列表中: {model_names}")
                return False

        except Exception as e:
            logger.error(f"Ollama 连接失败: {e}")
            return False


# 全局嵌入服务实例
embedding_service = EmbeddingService()
