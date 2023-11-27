"""Embedded Tables Retriever w/ Unstructured.IO."""

from llama_index import ServiceContext, VectorStoreIndex
from llama_index.llms import OpenAI
from llama_index.node_parser import (
    UnstructuredElementNodeParser
)
from typing import List, Dict, Any
from llama_index.llama_pack.base import BaseLlamaPack
from llama_index.retrievers import RecursiveRetriever
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.storage import StorageContext
from llama_index.readers.file.flat_reader import FlatReader
from pathlib import Path

class EmbeddedTablesUnstructuredRetrieverPack(BaseLlamaPack):
    """Embedded Tables + Unstructured.io Retriever pack.

    Use unstructured.io to parse out embedded tables from an HTML document, build 
    a node graph, and then run our recursive retriever against that.

    **NOTE**: must take in a single HTML file.
    
    """

    def __init__(
        self,
        html_path: str,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        self.reader = FlatReader()
        docs = self.reader.load_data(Path(html_path))
        self.node_parser = UnstructuredElementNodeParser()
        raw_nodes = self.node_parser.get_nodes_from_documents(docs)
        base_nodes, node_mappings = self.node_parser.get_base_nodes_and_mappings(
            raw_nodes
        )
        # construct top-level vector index + query engine
        vector_index = VectorStoreIndex(base_nodes)
        vector_retriever = vector_index.as_retriever(similarity_top_k=1)
        self.recursive_retriever = RecursiveRetriever(
            "vector",
            retriever_dict={"vector": vector_retriever},
            node_dict=node_mappings,
            verbose=True,
        )
        self.query_engine = RetrieverQueryEngine.from_args(self.recursive_retriever)
        

    def get_modules(self) -> Dict[str, Any]:
        """Get modules."""
        return {
            "node_parser": self.node_parser,
            "recursive_retriever": self.recursive_retriever,
            "query_engine": self.query_engine,
        }

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the pipeline."""
        return self.query_engine.query(*args, **kwargs)