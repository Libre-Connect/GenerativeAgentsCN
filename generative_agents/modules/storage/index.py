"""generative_agents.storage.index"""

import os
import time
import requests
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.indices.vector_store.retrievers import VectorIndexRetriever
from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from llama_index.core.embeddings import BaseEmbedding

from modules import utils


class GLMEmbedding(BaseEmbedding):
    """GLM Embedding implementation"""
    
    def __init__(self, model_name="embedding-3", base_url="https://open.bigmodel.cn/api/paas/v4", api_key=""):
        super().__init__()
        self._model_name = model_name
        self._base_url = base_url
        self._api_key = api_key or os.getenv('ZHIPUAI_API_KEY', 'c776b1833ad5e38df90756a57b1bcafc.Da0sFSNyQE2BMJEd')
    
    def _get_query_embedding(self, query: str):
        """Get embedding for a single query"""
        return self._get_text_embedding(query)
    
    async def _aget_query_embedding(self, query: str):
        """Get embedding for a single query (async version)"""
        return self._get_text_embedding(query)
    
    def _get_text_embedding(self, text: str):
        """Get embedding for a single text with retry mechanism"""
        max_retries = 3
        base_delay = 1  # 基础延迟时间（秒）
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    url=f"{self._base_url}/embeddings",
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self._api_key}'
                    },
                    json={
                        "model": self._model_name,
                        "input": text
                    },
                    timeout=30
                )
                
                if response.ok:
                    result = response.json()
                    if result and 'data' in result and len(result['data']) > 0:
                        return result['data'][0]['embedding']
                
                # 如果是 429 错误且还有重试次数，则等待后重试
                if response.status_code == 429 and attempt < max_retries:
                    delay = base_delay * (2 ** attempt)  # 指数退避
                    print(f"GLM API 速率限制，等待 {delay} 秒后重试 (尝试 {attempt + 1}/{max_retries + 1})")
                    time.sleep(delay)
                    continue
                
                # 其他错误或最后一次尝试失败
                raise Exception(f"GLM Embedding API 失败: HTTP {response.status_code}")
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    print(f"GLM API 请求异常，等待 {delay} 秒后重试: {e}")
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(f"GLM Embedding API 请求失败: {e}")
        
        raise Exception("GLM Embedding API 重试次数已用完")
    
    def _get_text_embeddings(self, texts):
        """Get embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embeddings.append(self._get_text_embedding(text))
        return embeddings
    
    async def _aget_text_embedding(self, text: str):
        """Get embedding for a single text (async version)"""
        return self._get_text_embedding(text)
    
    async def _aget_text_embeddings(self, texts):
        """Get embeddings for multiple texts (async version)"""
        embeddings = []
        for text in texts:
            embeddings.append(self._get_text_embedding(text))
        return embeddings


class FallbackEmbedding(BaseEmbedding):
    """带有降级策略的 Embedding 类"""
    
    def __init__(self, primary_embedding, fallback_embedding):
        super().__init__()
        self.primary_embedding = primary_embedding
        self.fallback_embedding = fallback_embedding
        self.fallback_active = False
    
    def _get_query_embedding(self, query: str):
        return self._get_text_embedding(query)
    
    async def _aget_query_embedding(self, query: str):
        return self._get_text_embedding(query)
    
    def _get_text_embedding(self, text: str):
        """优先使用主要 embedding，失败时使用降级 embedding"""
        if not self.fallback_active:
            try:
                return self.primary_embedding._get_text_embedding(text)
            except Exception as e:
                print(f"主要 embedding 失败，切换到降级模式: {e}")
                self.fallback_active = True
        
        # 使用降级 embedding
        return self.fallback_embedding._get_text_embedding(text)
    
    def _get_text_embeddings(self, texts):
        """Get embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embeddings.append(self._get_text_embedding(text))
        return embeddings
    
    async def _aget_text_embedding(self, text: str):
        """Get embedding for a single text (async version)"""
        return self._get_text_embedding(text)
    
    async def _aget_text_embeddings(self, texts):
        """Get embeddings for multiple texts (async version)"""
        embeddings = []
        for text in texts:
            embeddings.append(self._get_text_embedding(text))
        return embeddings


class LlamaIndex:
    def __init__(self, embedding_config, path=None):
        self._config = {"max_nodes": 0}
        
        # 创建降级 embedding（HuggingFace 作为备用）
        fallback_embedding = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        if embedding_config["provider"] == "hugging_face":
            embed_model = HuggingFaceEmbedding(model_name=embedding_config["model"])
        elif embedding_config["provider"] == "glm":
            primary_embedding = GLMEmbedding(
                model_name=embedding_config["model"],
                base_url=embedding_config["base_url"],
                api_key=embedding_config["api_key"],
            )
            # 使用带有降级策略的 embedding
            embed_model = FallbackEmbedding(primary_embedding, fallback_embedding)
        else:
            raise NotImplementedError(
                "embedding provider {} is not supported. Only 'hugging_face' and 'glm' are supported.".format(embedding_config["provider"])
            )

        Settings.embed_model = embed_model
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)
        Settings.num_output = 1024
        Settings.context_window = 4096
        if path and os.path.exists(path):
            self._index = load_index_from_storage(
                StorageContext.from_defaults(persist_dir=path),
                show_progress=True,
            )
            self._config = utils.load_dict(os.path.join(path, "index_config.json"))
        else:
            self._index = VectorStoreIndex([], show_progress=True)
        self._path = path

    def add_node(
        self,
        text,
        metadata=None,
        exclude_llm_keys=None,
        exclude_embedding_keys=None,
        id=None,
    ):
        while True:
            try:
                metadata = metadata or {}
                exclude_llm_keys = exclude_llm_keys or list(metadata.keys())
                exclude_embedding_keys = exclude_embedding_keys or list(metadata.keys())
                id = id or "node_" + str(self._config["max_nodes"])
                self._config["max_nodes"] += 1
                node = TextNode(
                    text=text,
                    id_=id,
                    metadata=metadata,
                    excluded_llm_metadata_keys=exclude_llm_keys,
                    excluded_embed_metadata_keys=exclude_embedding_keys,
                )
                self._index.insert_nodes([node])
                return node
            except Exception as e:
                print(f"LlamaIndex.add_node() caused an error: {e}")
                time.sleep(5)

    def has_node(self, node_id):
        return node_id in self._index.docstore.docs

    def find_node(self, node_id):
        return self._index.docstore.docs[node_id]

    def get_nodes(self, filter=None):
        def _check(node):
            if not filter:
                return True
            return filter(node)

        return [n for n in self._index.docstore.docs.values() if _check(n)]

    def remove_nodes(self, node_ids, delete_from_docstore=True):
        self._index.delete_nodes(node_ids, delete_from_docstore=delete_from_docstore)

    def cleanup(self):
        now, remove_ids = utils.get_timer().get_date(), []
        for node_id, node in self._index.docstore.docs.items():
            create = utils.to_date(node.metadata["create"])
            expire = utils.to_date(node.metadata["expire"])
            if create > now or expire < now:
                remove_ids.append(node_id)
        self.remove_nodes(remove_ids)
        return remove_ids

    def retrieve(
        self,
        text,
        similarity_top_k=5,
        filters=None,
        node_ids=None,
        retriever_creator=None,
    ):
        try:
            retriever_creator = retriever_creator or VectorIndexRetriever
            return retriever_creator(
                self._index,
                similarity_top_k=similarity_top_k,
                filters=filters,
                node_ids=node_ids,
            ).retrieve(text)
        except Exception as e:
            # print(f"LlamaIndex.retrieve() caused an error: {e}")
            return []

    def query(
        self,
        text,
        similarity_top_k=5,
        text_qa_template=None,
        refine_template=None,
        filters=None,
        query_creator=None,
    ):
        kwargs = {
            "similarity_top_k": similarity_top_k,
            "text_qa_template": text_qa_template,
            "refine_template": refine_template,
            "filters": filters,
        }
        while True:
            try:
                if query_creator:
                    query_engine = query_creator(retriever=self._index.as_retriever(**kwargs))
                else:
                    query_engine = self._index.as_query_engine(**kwargs)
                return query_engine.query(text)
            except Exception as e:
                print(f"LlamaIndex.query() caused an error: {e}")
                time.sleep(5)

    def save(self, path=None):
        path = path or self._path
        self._index.storage_context.persist(path)
        utils.save_dict(self._config, os.path.join(path, "index_config.json"))

    @property
    def nodes_num(self):
        return len(self._index.docstore.docs)
