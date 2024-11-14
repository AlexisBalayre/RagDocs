"""
A Retrieval-Augmented Generation (RAG) system specialized for technology documentation comparison.

This module implements a RAG system that can process, index, and search across technical documentation
from multiple technologies. It supports incremental updates, semantic search, and categorical 
filtering of content.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
import numpy as np
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from sentence_transformers import SentenceTransformer
import markdown
import re
import logging
from collections import defaultdict

from ragdocs_api.file_tracker import FileTracker
from ragdocs_api.logger_config import setup_logger
from ragdocs_api.markdown_processor import MarkdownProcessor


@dataclass
class SearchResult:
    """
    Data class representing a single search result from the RAG system.

    Attributes:
        content (str): The actual content of the search result
        technology (str): The technology/platform this content refers to
        file_path (str): Path to the source file containing this content
        section_title (str): Title of the section containing this content
        section_level (int): Heading level of the section (1-6)
        category (str): Classified category of the content (e.g., 'deployment', 'security')
        score (float): Relevance score of the result to the search query (0-1)
    """

    content: str
    technology: str
    file_path: str
    section_title: str
    section_level: int
    category: str
    score: float


class RagSystem:
    """
    A RAG system designed for comparing technical documentation across different technologies.

    Attributes:
        logger (logging.Logger): Logger instance for tracking operations
        host (str): Milvus server host address
        port (str): Milvus server port
        collection_name (str): Name of the Milvus collection to use
        encoder (SentenceTransformer): Model for generating text embeddings
        category_keywords (Dict[str, Set[str]]): Mapping of categories to their keywords
        available_technologies (Set[str]): Set of indexed technologies
    """

    def __init__(
        self,
        logger: logging.Logger,
        host: str = "localhost",
        port: str = "19530",
        collection_name: str = "docs_tech",
    ):
        """
        Initialize the RAG system with specified configuration.

        Args:
            logger (logging.Logger): Logger instance for operation tracking
            host (str, optional): Milvus server host address. Defaults to "localhost"
            port (str, optional): Milvus server port. Defaults to "19530"
            collection_name (str, optional): Name for Milvus collection. Defaults to "docs_tech"

        Raises:
            Exception: If unable to load sentence transformer model or connect to Milvus
        """
        # Initialize logger
        self.logger = logger
        self.logger.info(f"Initializing RAG system with collection: {collection_name}")

        # Basic configuration
        self.host = host
        self.port = port
        self.collection_name = collection_name

        # Initialize components
        try:
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            self.logger.debug("Loaded sentence transformer model")
        except Exception as e:
            self.logger.error(f"Failed to load sentence transformer: {str(e)}")
            raise

        # Category definitions
        self.category_keywords = {
            "deployment": {"deployment", "install", "setup", "configuration"},
            "performance": {"performance", "speed", "latency", "throughput"},
            "features": {"feature", "functionality", "capability"},
            "scalability": {"scale", "scalability", "distributed", "cluster"},
            "security": {"security", "authentication", "encryption"},
            "integration": {"integration", "connector", "plugin"},
        }

        # Initialize processors
        self.file_tracker = FileTracker()
        self.markdown_processor = MarkdownProcessor(self.category_keywords)
        self.available_technologies = set()

        # Connect to Milvus
        self.connect_to_milvus()

        # Update documentation for all available technologies
        self.update_documentation("data/milvus_docs", "milvus")
        self.update_documentation("data/qdrant_docs", "qdrant")
        self.update_documentation("data/weaviate_docs", "weaviate")

    def connect_to_milvus(self):
        """
        Establish connection to Milvus server.

        This method attempts to connect to the Milvus server using the configured
        host and port. It uses the default connection alias.

        Raises:
            Exception: If connection to Milvus server fails
        """
        try:
            self.logger.info(f"Connecting to Milvus at {self.host}:{self.port}")
            connections.connect(alias="default", host=self.host, port=self.port)
            self.logger.debug("Successfully connected to Milvus")
        except Exception as e:
            self.logger.error(f"Failed to connect to Milvus: {str(e)}")
            raise

    def ensure_collection(self) -> Collection:
        """
        Create or retrieve the Milvus collection for document storage.

        This method checks if the specified collection exists and creates it if necessary.
        It also sets up the appropriate schema and index for vector search.

        Returns:
            Collection: Milvus collection object ready for use

        Raises:
            Exception: If collection creation or index creation fails
        """
        try:
            if not utility.has_collection(self.collection_name):
                self.logger.info(f"Creating new collection: {self.collection_name}")
                fields = [
                    FieldSchema(
                        name="id", dtype=DataType.INT64, is_primary=True, auto_id=True
                    ),
                    FieldSchema(
                        name="content",
                        dtype=DataType.VARCHAR,
                        max_length=65535,
                    ),
                    FieldSchema(
                        name="technology", dtype=DataType.VARCHAR, max_length=64
                    ),
                    FieldSchema(
                        name="file_path", dtype=DataType.VARCHAR, max_length=512
                    ),
                    FieldSchema(
                        name="file_hash", dtype=DataType.VARCHAR, max_length=32
                    ),
                    FieldSchema(
                        name="section_title", dtype=DataType.VARCHAR, max_length=512
                    ),
                    FieldSchema(name="section_level", dtype=DataType.INT16),
                    FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
                    FieldSchema(
                        name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=384
                    ),
                ]

                schema = CollectionSchema(fields=fields)
                collection = Collection(
                    name=self.collection_name,
                    schema=schema,
                    using="default",
                    shards_num=2,
                )

                # Create HNSW index
                self.logger.debug("Creating HNSW index")
                index_params = {
                    "metric_type": "L2",
                    "index_type": "HNSW",
                    "params": {"M": 8, "efConstruction": 64},
                }
                collection.create_index(
                    field_name="embeddings", index_params=index_params
                )
                self.logger.info("Collection and index created successfully")
            else:
                self.logger.debug(f"Using existing collection: {self.collection_name}")
                collection = Collection(self.collection_name)

            return collection
        except Exception as e:
            self.logger.error(f"Failed to ensure collection: {str(e)}")
            raise

    def process_markdown_file(self, file_path: str, technology: str) -> List[Dict]:
        """
        Process a markdown file into chunks with metadata.

        This method reads a markdown file, processes its content into meaningful chunks,
        and adds relevant metadata including embeddings and categories.

        Args:
            file_path (str): Path to the markdown file to process
            technology (str): Name of the technology this documentation belongs to

        Returns:
            List[Dict]: List of chunks, each containing processed content and metadata

        Raises:
            Exception: If file processing fails at any stage
        """
        self.logger.debug(f"Processing markdown file: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get file hash
            file_hash = self.file_tracker.compute_file_hash(file_path)
            self.logger.debug(f"File hash: {file_hash}")

            # Clean and process content
            processed_content = self.markdown_processor.clean_code_blocks(content)
            metadata, processed_content = self.markdown_processor.extract_frontmatter(
                processed_content
            )
            sections = self.markdown_processor.extract_sections(processed_content)

            # Process sections into chunks
            chunks = []
            for section in sections:
                # Preprocess section for vector search
                processed_section = self.markdown_processor.preprocess_section(
                    content=section["content"],
                    title=section["title"],
                    level=section["level"],
                )

                category = self.markdown_processor.detect_category(
                    processed_section["content"], processed_section["title"]
                )

                chunks.append(
                    {
                        "content": processed_section["content"],
                        "technology": technology,
                        "file_path": str(file_path),
                        "file_hash": file_hash,
                        "section_title": processed_section["title"],
                        "section_level": processed_section["level"],
                        "category": category,
                        "embeddings": self.encoder.encode(
                            processed_section["content"]
                        ).tolist(),
                    }
                )

            self.logger.info(
                f"Processed {file_path}: {len(sections)} sections, {len(chunks)} chunks"
            )
            return chunks

        except Exception as e:
            self.logger.error(f"Failed to process file {file_path}: {str(e)}")
            raise

    def update_documentation(self, docs_path: str, technology: str):
        """
        Incrementally update documentation for a specific technology.

        This method handles the addition, modification, and deletion of documentation
        files for a given technology. It tracks file changes and updates the vector
        database accordingly.

        Args:
            docs_path (str): Path to the documentation directory
            technology (str): Name of the technology to update

        Note:
            This method is incremental - it only processes files that have changed
            since the last update.

        Raises:
            Exception: If documentation update fails at any stage
        """
        self.logger.info(f"Updating documentation for {technology} from {docs_path}")

        try:
            # Get file changes
            new_files, modified_files, deleted_files = (
                self.file_tracker.get_modified_files(docs_path, technology)
            )

            if not (new_files or modified_files or deleted_files):
                self.logger.info(f"No changes detected for {technology}")
                return

            collection = self.ensure_collection()

            # Remove deleted and modified files from collection
            files_to_remove = deleted_files + modified_files
            if files_to_remove:
                self.logger.debug(
                    f"Removing {len(files_to_remove)} files from collection"
                )
                expr = f"file_path in {files_to_remove}"
                collection.delete(expr)

            # Process new and modified files
            files_to_process = new_files + modified_files
            all_chunks = []
            for file_path in files_to_process:
                chunks = self.process_markdown_file(file_path, technology)
                all_chunks.extend(chunks)

            # Insert new chunks
            if all_chunks:
                self.logger.debug(f"Inserting {len(all_chunks)} chunks into collection")
                collection.insert(
                    [
                        [chunk["content"] for chunk in all_chunks],
                        [chunk["technology"] for chunk in all_chunks],
                        [chunk["file_path"] for chunk in all_chunks],
                        [chunk["file_hash"] for chunk in all_chunks],
                        [chunk["section_title"] for chunk in all_chunks],
                        [chunk["section_level"] for chunk in all_chunks],
                        [chunk["category"] for chunk in all_chunks],
                        [chunk["embeddings"] for chunk in all_chunks],
                    ]
                )
                collection.flush()

            # Update available technologies
            self.available_technologies.add(technology)

            self.logger.info(
                f"Updated {technology} documentation:\n"
                f"- New files: {len(new_files)}\n"
                f"- Modified files: {len(modified_files)}\n"
                f"- Deleted files: {len(deleted_files)}"
            )
        except Exception as e:
            self.logger.error(f"Failed to update documentation: {str(e)}")
            raise

    def search(
        self,
        query: str,
        technologies: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        top_k: int = 3,
    ) -> Dict[str, List[SearchResult]]:
        """
        Perform semantic search across the documentation with optional filtering.

        This method searches for relevant content across all indexed documentation using
        semantic similarity and returns the most relevant results organized by technology.
        The search can be filtered by specific technologies and/or categories.

        Args:
            query (str): The search query text
            technologies (Optional[List[str]], optional): List of technologies to search within.
                If None, searches across all technologies. Defaults to None.
            categories (Optional[List[str]], optional): List of categories to filter by.
                If None, includes all categories. Defaults to None.
            top_k (int, optional): Number of top results to return per technology.
                Defaults to 3.

        Returns:
            Dict[str, List[SearchResult]]: Dictionary mapping technology names to lists
                of SearchResult objects, sorted by relevance score.

        Raises:
            Exception: If the search operation fails at any stage

        Example:
            >>> results = rag.search(
            ...     query="How to scale deployments?",
            ...     technologies=["milvus", "qdrant"],
            ...     categories=["deployment"],
            ...     top_k=3
            ... )
            >>> for tech, tech_results in results.items():
            ...     print(f"\\n{tech} results:")
            ...     for result in tech_results:
            ...         print(f"- {result.section_title} (score: {result.score:.2f})")

        Note:
            - The search uses vector similarity with the all-MiniLM-L6-v2 model
            - Results are normalized to a 0-1 score range where 1 is most relevant
            - The method uses async collection loading for better performance
        """
        try:
            # 1. Pre-build the expression outside the main search logic
            expr = self._build_filter_expression(technologies, categories)

            # 2. Get collection and encode query in parallel
            collection = Collection(self.collection_name)
            query_embedding = self.encoder.encode(query).tolist()

            # 3. Load collection with optimized consistency_level
            collection.load(_async=True)  # Async load for better performance

            # 4. Define minimal output fields - only what we need
            output_fields = [
                "content",  # Needed for result display
                "technology",  # Needed for organizing results
                "file_path",  # Needed for raw content
                "section_title",  # Needed for result display
                "section_level",  # Needed for result structure
                "category",  # Needed for filtering/display
            ]

            # 5. Optimize search parameters
            search_params = {
                "metric_type": "L2",
                "params": {
                    "ef": min(64, top_k * 2),  # Adjust ef based on top_k
                    "nprobe": 16,  # Balance between speed and recall
                },
            }

            # 6. Perform search with optimized parameters
            results = collection.search(
                data=[query_embedding],
                anns_field="embeddings",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=output_fields,
                consistency_level="Eventually",  # Faster consistency level
            )

            # 7. Process results efficiently
            organized_results = defaultdict(list)
            for hits in results:
                for hit in hits:
                    normalized_score = 1 - (hit.score**2 / 4)  # Normalize score to 0-1

                    # Get entity data efficiently
                    entity = hit.entity
                    content = entity.get("content")
                    file_path = entity.get("file_path")

                    result = SearchResult(
                        content=content,
                        technology=entity.get("technology"),
                        file_path=file_path,
                        section_title=entity.get("section_title"),
                        section_level=entity.get("section_level"),
                        category=entity.get("category"),
                        score=normalized_score,
                    )
                    organized_results[result.technology].append(result)

            # 8. Release collection asynchronously
            collection.release(_async=True)

            return dict(organized_results)

        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            raise

    def _build_filter_expression(
        self, technologies: Optional[List[str]], categories: Optional[List[str]]
    ) -> Optional[str]:
        """
        Build a Milvus filter expression for querying specific technologies and categories.

        This method constructs a filter expression string that combines technology and category
        filters using AND operations. The resulting expression is used to filter Milvus search
        results.

        Args:
            technologies (Optional[List[str]]): List of technology names to filter by.
                If None, no technology filter is applied.
            categories (Optional[List[str]]): List of category names to filter by.
                If None, no category filter is applied.

        Returns:
            Optional[str]: A Milvus-compatible filter expression string. Examples:
                - With both filters: "technology in ['milvus'] && category in ['deployment']"
                - With one filter: "technology in ['milvus']"
                - With no filters: None
        """
        expr_parts = []

        if technologies:
            expr_parts.append(f"technology in {technologies}")

        if categories:
            expr_parts.append(f"category in {categories}")

        return " && ".join(expr_parts) if expr_parts else None

    def get_available_technologies(self) -> Set[str]:
        """
        Retrieve the set of all available technologies in the RAG system.

        This method returns a set of technology names that have been successfully
        indexed in the system through the update_documentation method.

        Returns:
            Set[str]: A set containing the names of all available technologies.
                Empty set if no technologies have been processed yet.
                
        Note:
            The set is updated automatically when new technologies are added
            via the update_documentation method.
        """
        return self.available_technologies

    def get_categories(self) -> Set[str]:
        """
        Retrieve the set of all available content categories in the RAG system.

        This method returns the predefined set of categories used to classify
        documentation content. These categories are defined in the category_keywords
        dictionary during initialization.

        Returns:
            Set[str]: A set containing all available category names:
                - deployment: Installation and setup instructions
                - performance: Performance-related content
                - features: Feature descriptions and capabilities
                - scalability: Scaling and distribution information
                - security: Security and authentication content
                - integration: Integration and connectivity details
        """
        return set(self.category_keywords.keys())
