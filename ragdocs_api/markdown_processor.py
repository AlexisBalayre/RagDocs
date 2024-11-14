"""
Markdown Processor for Technical Documentation

This module provides utilities to preprocess and extract meaningful sections from
markdown files, enabling structured processing for technical documentation. It includes
features like truncating text to fit database constraints, extracting YAML frontmatter,
and categorizing content based on predefined keywords. The processor is designed for
integration with retrieval-augmented generation (RAG) systems.
"""

import re
from typing import Dict, List, Tuple
import frontmatter
from collections import defaultdict
import yaml
from yaml.scanner import ScannerError
from yaml.parser import ParserError


class MarkdownProcessor:
    """
    Handles markdown document processing and chunking.

    Attributes:
        category_keywords (Dict[str, set]): A dictionary mapping categories to sets of keywords.
        max_title_length (int): Maximum allowed length for section titles.
        max_content_length (int): Maximum allowed length for section content.
    """

    def __init__(self, category_keywords: Dict[str, set]):
        """
        Initialize the MarkdownProcessor.

        Args:
            category_keywords (Dict[str, set]): Keywords used to categorize sections.
        """
        self.category_keywords = category_keywords
        self.max_title_length = 512  # Milvus varchar field limit
        self.max_content_length = 65535  # Milvus varchar field limit

    def truncate_text(
        self, text: str, max_length: int, add_ellipsis: bool = True
    ) -> str:
        """
        Truncate text to a maximum length while preserving word boundaries.

        Args:
            text (str): The text to truncate.
            max_length (int): Maximum allowed length of the text.
            add_ellipsis (bool): Whether to add ellipsis to truncated text. Defaults to True.

        Returns:
            str: Truncated text.
        """
        if len(text) <= max_length:
            return text

        truncated = text[:max_length]
        # Find last space to avoid cutting words
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]

        if add_ellipsis and len(text) > max_length:
            truncated = truncated.rstrip() + "..."

        return truncated

    def extract_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """
        Extract YAML frontmatter from markdown if present.

        Args:
            content (str): Markdown content.

        Returns:
            Tuple[Dict, str]: A tuple containing the extracted metadata and remaining content.
        """
        try:
            if not content.startswith("---\n"):
                return {}, content

            end_delimiter_pos = content.find("\n---\n", 4)
            if end_delimiter_pos == -1:
                return {}, content

            yaml_content = content[4:end_delimiter_pos]
            remaining_content = content[end_delimiter_pos + 5 :]

            try:
                metadata = yaml.safe_load(yaml_content)
                if not isinstance(metadata, dict):
                    metadata = {}
            except (ScannerError, ParserError) as e:
                print(f"YAML parsing error: {str(e)}")
                return {}, content

            return metadata, remaining_content.strip()

        except Exception as e:
            print(f"Unexpected error in frontmatter extraction: {str(e)}")
            return {}, content

    def clean_code_blocks(self, text: str) -> str:
        """
        Process code blocks in markdown to maintain their context.

        Args:
            text (str): Markdown content with potential code blocks.

        Returns:
            str: Processed text with placeholders for code blocks.
        """

        def replace_code_block(match):
            lang = match.group(1) or "code"
            return f"[CODE_BLOCK_{lang}: Code example]"

        text = re.sub(
            r"```(\w+)?\n(.*?)\n```", replace_code_block, text, flags=re.DOTALL
        )

        lines = text.split("\n")
        in_code_block = False
        processed_lines = []

        for line in lines:
            if line.startswith("    ") or line.startswith("\t"):
                if not in_code_block:
                    in_code_block = True
                    processed_lines.append("[CODE_BLOCK: Indented code example]")
            else:
                in_code_block = False
                processed_lines.append(line)

        return "\n".join(processed_lines)

    def extract_sections(self, markdown_text: str) -> List[Dict[str, str]]:
        """
        Extract sections from markdown content based on headers.

        Args:
            markdown_text (str): The markdown text to process.

        Returns:
            List[Dict[str, str]]: A list of sections, each containing title, level, and content.
        """
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

        headers = [
            (match.group(1), match.group(2), match.start())
            for match in header_pattern.finditer(markdown_text)
        ]

        if not headers:
            return [
                {
                    "title": "Main Content",
                    "level": 0,
                    "content": self.truncate_text(
                        markdown_text, self.max_content_length
                    ),
                }
            ]

        sections = []
        for i in range(len(headers)):
            current_header = headers[i]
            next_pos = headers[i + 1][2] if i + 1 < len(headers) else len(markdown_text)

            title = self.truncate_text(current_header[1], self.max_title_length)
            content = markdown_text[current_header[2] : next_pos].strip()
            content = self.truncate_text(content, self.max_content_length)

            sections.append(
                {
                    "title": title,
                    "level": len(current_header[0]),
                    "content": content,
                }
            )

        return sections

    def detect_category(self, text: str, title: str) -> str:
        """
        Detect the category of a text section based on keywords.

        Args:
            text (str): Content of the section.
            title (str): Title of the section.

        Returns:
            str: Detected category name.
        """
        text_lower = text.lower() + " " + title.lower()

        category_scores = defaultdict(int)
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    category_scores[category] += 1

        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        return "general"

    def preprocess_section(
        self, content: str, title: str, level: int
    ) -> Dict[str, str]:
        """
        Preprocess a section's content and ensure field length limits.

        Args:
            content (str): Content of the section.
            title (str): Title of the section.
            level (int): Header level of the section.

        Returns:
            Dict[str, str]: Processed section dictionary with title, content, and level.
        """
        return {
            "title": self.truncate_text(title, self.max_title_length),
            "content": self.truncate_text(content, self.max_content_length),
            "level": level,
        }
