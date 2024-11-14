"""
FastAPI-based Conversation API with RAG capabilities for technical documentation.

This module implements a REST API for managing conversational interactions with technical documentation
using Retrieval-Augmented Generation (RAG). It provides endpoints for chat, conversation management,
and title generation.
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
import json
from pathlib import Path
import datetime
from uuid import uuid4
import logging
from llama_index.core import VectorStoreIndex, Document, ServiceContext, Settings
from llama_index.llms.ollama import Ollama
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.base.llms.types import ChatMessage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import uvicorn
from contextlib import contextmanager

from logger_config import setup_logger
from rag_system import RagSystem
from llm_provider import LLMProvider, OllamaConfig, LLMManager

# Configure logger
logger = setup_logger(name="conversation_api", log_file="conversation_api.log")

# Initialize FastAPI app
app = FastAPI(title="Conversation API", version="1.0.0")


class Source(BaseModel):
    """
    Represents a source of information from the documentation.

    Attributes:
        technology (str): The technology/platform this source is from
        file_path (str): Path to the source file
        section_title (str): Title of the section containing the content
        category (str): Category of the content
        score (float): Relevance score (0-1) of the source to the query
        content_preview (str): Short preview of the content
        full_content (str): Complete content of the source
    """

    technology: str
    file_path: str
    section_title: str
    category: str
    score: float = Field(ge=0.0, le=1.0) 
    content_preview: str
    full_content: str


class Message(BaseModel):
    """
    Represents a single message in a conversation.

    Attributes:
        role (str): Role of the message sender (user/assistant)
        content (str): Content of the message
        sources (Optional[List[Source]]): List of sources used in the message
    """

    role: str = Field(..., pattern="^(user|assistant)$")  # Only allow user or assistant
    content: str
    sources: Optional[List[Source]] = None


class Conversation(BaseModel):
    """
    Represents a complete conversation.

    Attributes:
        title (str): Title of the conversation
        id (str): Unique identifier for the conversation
        messages (List[Message]): List of messages in the conversation
        created_at (str): ISO format timestamp of creation
        updated_at (str): ISO format timestamp of last update
    """

    title: str
    id: str
    messages: List[Message] = Field(default_factory=list)
    created_at: str
    updated_at: str


class ConversationRequest(BaseModel):
    """
    Request model for conversation interactions.

    Attributes:
        message (str): The user's message
        conversation_id (Optional[str]): ID of existing conversation
        technologies (Optional[List[str]]): Technologies to search in
        categories (Optional[List[str]]): Categories to filter by
    """

    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    technologies: Optional[List[str]] = Field(default_factory=list)
    categories: Optional[List[str]] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    """
    Response model for conversation interactions.

    Attributes:
        conversation_id (str): ID of the conversation
        response (str): The assistant's response
        sources (List[Source]): Sources used to generate the response
    """

    conversation_id: str
    response: str
    sources: List[Source]


class TitleRequest(BaseModel):
    """
    Request model for title generation.

    Attributes:
        message (str): Message to generate title from
    """

    message: str = Field(..., min_length=1)


class LLMConfig(BaseModel):
    """
    Configuration model for Language Models.

    Attributes:
        provider (str): Name of the LLM provider
        model (str): Name of the specific model
        temperature (float): Sampling temperature (0-1)
        max_tokens (Optional[int]): Maximum tokens to generate
        timeout (Optional[float]): Request timeout in seconds
    """

    provider: str
    model: str
    temperature: float = Field(ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    timeout: Optional[float] = Field(None, gt=0)


class ConversationManager:
    """
    Manages conversation state, storage, and interactions.

    Attributes:
        conversations_dir (Path): Directory for storing conversations
        rag_system (RagSystem): RAG system instance
        llm_manager (LLMManager): LLM management instance
    """

    def __init__(self, conversations_dir: str = "conversations"):
        """
        Initialize the ConversationManager.

        Args:
            conversations_dir (str): Path to conversations storage directory.
                Defaults to "conversations".

        Raises:
            RuntimeError: If initialization of any component fails
        """
        self.conversations_dir = Path(conversations_dir)
        self._ensure_conversations_directory()
        self._initialize_components()

    def _ensure_conversations_directory(self):
        """
        Create conversations directory if it doesn't exist.

        Raises:
            RuntimeError: If directory creation fails
        """
        try:
            self.conversations_dir.mkdir(mode=0o755, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create conversations directory: {e}")
            raise RuntimeError("Failed to initialize conversation storage")

    def _initialize_components(self):
        """
        Initialize RAG system and LLM components.

        Raises:
            RuntimeError: If component initialization fails
        """
        try:
            self.rag_system = RagSystem(logger)
            self.llm_manager = LLMManager(
                provider=LLMProvider.OLLAMA,
                config=OllamaConfig(model="llama3.2", temperature=0.7),
            )

            # Configure LlamaIndex settings
            Settings.llm = self.llm_manager.get_llm()
            Settings.chunk_size = 1024
            Settings.chunk_overlap = 20
            Settings.embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise RuntimeError("Failed to initialize conversation components")

    @contextmanager
    def _file_operation(self, file_path: Path, mode: str):
        """
        Context manager for safe file operations.

        Args:
            file_path (Path): Path to the file to operate on
            mode (str): File operation mode ('r', 'w', etc.)

        Yields:
            file object: The opened file object

        Raises:
            HTTPException: If file operation fails
        """
        try:
            with open(file_path, mode) as f:
                yield f
        except IOError as e:
            logger.error(f"File operation failed for {file_path}: {e}")
            raise HTTPException(status_code=500, detail="File operation failed")

    def _get_conversation_path(self, conversation_id: str) -> Path:
        """
        Get the file path for a conversation with validation.

        Args:
            conversation_id (str): ID of the conversation

        Returns:
            Path: Path to the conversation file

        Raises:
            ValueError: If conversation_id is invalid
        """
        if not conversation_id.strip() or ".." in conversation_id:
            raise ValueError("Invalid conversation ID")
        return self.conversations_dir / f"{conversation_id}.json"

    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation from storage.

        Args:
            conversation_id (str): ID of the conversation to load

        Returns:
            Optional[Conversation]: Loaded conversation or None if not found

        Note:
            Returns None for both non-existent conversations and corrupted files
        """
        conv_path = self._get_conversation_path(conversation_id)
        if not conv_path.exists():
            return None

        try:
            with self._file_operation(conv_path, "r") as f:
                data = json.load(f)
                return Conversation(**data)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in conversation file: {conversation_id}")
            return None

    def save_conversation(self, conversation: Conversation):
        """
        Save a conversation to storage.

        Args:
            conversation (Conversation): Conversation to save

        Raises:
            HTTPException: If save operation fails
        """
        conv_path = self._get_conversation_path(conversation.id)
        with self._file_operation(conv_path, "w") as f:
            json.dump(conversation.dict(), f, indent=2)

    async def create_conversation(self, initial_message: str) -> Conversation:
        """
        Create a new conversation with generated title.

        Args:
            initial_message (str): First message to start the conversation

        Returns:
            Conversation: Newly created conversation object

        Raises:
            RuntimeError: If conversation creation fails
        """
        try:
            conversation_id = str(uuid4())
            now = datetime.datetime.utcnow().isoformat()

            # Generate title if initial message is provided, otherwise use default
            title = "New Chat"
            try:
                title_response = await generate_title(
                    TitleRequest(message=initial_message)
                )
                title = title_response["title"]
            except Exception as e:
                logger.warning(f"Failed to generate title: {e}")

            # Create the conversation object with explicit default values
            conversation = Conversation(
                id=conversation_id,
                title=title,
                messages=[],
                created_at=now,
                updated_at=now,
            )

            # Save immediately
            self.save_conversation(conversation)
            logger.info(
                f"Successfully created conversation {conversation_id} with title: {title}"
            )
            return conversation

        except Exception as e:
            logger.error(f"Failed to create conversation: {e}", exc_info=True)
            raise RuntimeError(f"Failed to create conversation: {e}")

    async def process_message(
        self, request: Union[Dict, ConversationRequest]
    ) -> ConversationResponse:
        """
        Process an incoming message and generate a response.

        This method handles the complete flow of:
            1. Loading/creating conversation
            2. Retrieving relevant documentation
            3. Generating response using LLM
            4. Updating conversation history

        Args:
            request (Union[Dict, ConversationRequest]): Message request data

        Returns:
            ConversationResponse: Generated response with sources

        Raises:
            HTTPException: If processing fails at any stage
        """
        try:
            # Convert dict to ConversationRequest if needed
            if isinstance(request, dict):
                request = ConversationRequest(**request)

            # Get or create conversation
            conversation = (
                self.load_conversation(request.conversation_id)
                if request.conversation_id
                else await self.create_conversation(request.message)
            )

            logger.info(f"Processing message for conversation {conversation.id}")

            # Get RAG search results
            search_results = self.rag_system.search(
                query=request.message,
                technologies=request.technologies,
                categories=request.categories,
                top_k=6,
            )

            # Process search results
            context, sources = self._process_search_results(search_results)

            # Get chat response
            response = self._get_chat_response(
                conversation, request.message, context, sources
            )

            # Update and save conversation
            self._update_conversation(conversation, request.message, response, sources)

            return ConversationResponse(
                conversation_id=conversation.id, response=response, sources=sources
            )

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def _process_search_results(
        self, search_results: Dict
    ) -> tuple[List[str], List[Source]]:
        """
        Process RAG search results into context and sources.

        Args:
            search_results (Dict): Raw search results from RAG system

        Returns:
            tuple[List[str], List[Source]]: Processed context strings and source objects

        Note:
            The context strings are formatted for LLM consumption while sources
            contain metadata for UI display
        """
        context = []
        sources = []

        for tech, results in search_results.items():
            for result in results:
                context.append(f"From {tech} documentation:\n{result.content}")
                sources.append(
                    Source(
                        technology=tech,
                        file_path=result.file_path,
                        section_title=result.section_title,
                        category=result.category,
                        score=float(result.score),
                        content_preview=(
                            result.content[:200] + "..."
                            if len(result.content) > 200
                            else result.content
                        ),
                        full_content=result.content,
                    )
                )

        return context, sources

    def _get_chat_response(
        self,
        conversation: Conversation,
        message: str,
        context: List[str],
        sources: List[Source],
    ) -> str:
        """
        Generate a chat response using the LLM with provided context.

        This method:
            1. Creates a system prompt for the LLM
            2. Prepares recent chat history
            3. Creates an index from context documents
            4. Generates a response using the chat engine

        Args:
            conversation (Conversation): Current conversation object
            message (str): User's input message
            context (List[str]): List of relevant documentation excerpts
            sources (List[Source]): List of source metadata

        Returns:
            str: Generated response from the LLM

        Note:
            - Uses only recent messages (last 5) for chat history
            - Includes system prompt for technical context
        """
        system_prompt = """You are a technical assistant with expertise in vector databases and search technologies. 
        Use the provided documentation context to answer questions accurately and comprehensively. 
        If the context doesn't contain enough information to answer the question, say so."""

        # Convert conversation messages to ChatMessage objects
        chat_history = [
            ChatMessage(role=msg.role, content=msg.content)
            for msg in conversation.messages[-5:]  # Use only recent messages
        ]

        # Create index and chat engine
        documents = [Document(text="\n\n".join(context))]
        index = VectorStoreIndex.from_documents(documents)
        chat_engine = index.as_chat_engine(
            chat_mode="context", chat_history=chat_history, system_prompt=system_prompt
        )

        # Get and format response
        response = chat_engine.chat(message)
        return str(response)

    def _update_conversation(
        self,
        conversation: Conversation,
        message: str,
        response: str,
        sources: List[Source],
    ):
        """
        Update conversation with new messages and save to storage.

        This method:
            1. Adds the user's message
            2. Adds the assistant's response with sources
            3. Updates the timestamp
            4. Saves the updated conversation

        Args:
            conversation (Conversation): Conversation to update
            message (str): User's message
            response (str): Assistant's response
            sources (List[Source]): Sources used in the response
        """
        conversation.messages.append(Message(role="user", content=message, sources=[]))
        conversation.messages.append(
            Message(role="assistant", content=response, sources=sources)
        )
        conversation.updated_at = datetime.datetime.utcnow().isoformat()
        self.save_conversation(conversation)


# Initialize conversation manager
conversation_manager = ConversationManager()


@app.get("/")
async def root():
    """
    Root endpoint to verify API status.

    Returns:
        dict: API status information
    """
    return {"message": "Conversation API is running", "version": "1.0.0"}


@app.post("/chat", response_model=ConversationResponse)
async def chat(request: ConversationRequest):
    """
    Process a chat message and return a response.

    This endpoint handles:
        - New conversation creation
        - Message processing
        - Response generation with sources

    Args:
        request (ConversationRequest): Chat request containing message and optional parameters

    Returns:
        ConversationResponse: Generated response with conversation ID and sources

    Raises:
        HTTPException: If chat processing fails
    """
    try:
        return await conversation_manager.process_message(request)
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations")
async def get_conversations():
    """
    Retrieve a list of all conversations.

    Returns:
        List[dict]: List of conversation metadata including:
            - id: Conversation identifier
            - created_at: Creation timestamp
            - updated_at: Last update timestamp
            - title: Conversation title

    Raises:
        HTTPException: If conversation retrieval fails
    """
    try:
        conversations = []
        for conv_path in conversation_manager.conversations_dir.glob("*.json"):
            with conversation_manager._file_operation(conv_path, "r") as f:
                data = json.load(f)
                conversation = Conversation(**data)
                conversations.append(
                    {
                        "id": conversation.id,
                        "created_at": conversation.created_at,
                        "updated_at": conversation.updated_at,
                        "title": conversation.title,
                    }
                )
        return conversations
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")


@app.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """
    Retrieve a specific conversation by ID.

    Args:
        conversation_id (str): Unique identifier of the conversation

    Returns:
        Conversation: Complete conversation object

    Raises:
        HTTPException: If conversation not found or retrieval fails
    """
    conversation = conversation_manager.load_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.post("/chat/title")
async def generate_title(request: TitleRequest):
    """
    Generate a meaningful title for a conversation.

    This endpoint:
        1. Uses the LLM to generate a concise title
        2. Cleans and formats the generated title
        3. Falls back to default title on failure

    Args:
        request (TitleRequest): Request containing the message to base title on

    Returns:
        dict: Generated title in format {"title": str}

    Note:
        - Generates titles up to 80 characters
        - Removes quotes and special characters
        - Falls back to "New Chat" on failure
    """
    try:
        # Use the existing LLM manager to generate a title
        system_prompt = """Generate a concise, descriptive title (max 5-7 words) for a chat conversation that starts with this message. 
        The title should capture the main topic or question.
        Do not use quotes or special characters.
        Be direct and clear."""

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Generate title for: {request.message}"),
        ]

        # Get title from LLM
        llm = conversation_manager.llm_manager.get_llm()
        response = llm.chat(messages)

        # Clean and format the title
        title = str(response.message.content).strip()

        # Ensure title length is reasonable
        if len(title) > 80:
            title = title[:77] + "..."

        # Remove any quotes that might have been added
        title = title.replace('"', "").replace("'", "")

        logger.info(f"Generated title: {title}")
        return {"title": title}

    except Exception as e:
        logger.error(f"Error generating title: {str(e)}", exc_info=True)
        return {"title": "New Chat"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
