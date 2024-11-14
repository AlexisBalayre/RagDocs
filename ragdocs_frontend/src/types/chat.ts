export interface Source {
    technology: string;
    file_path: string;
    section_title: string;
    category: string;
    score: number;
    content_preview: string;
    full_content: string;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    sources?: Source[];
}

export interface Conversation {
    id: string;
    title: string;
    messages: Message[];
    created_at: string;
    updated_at: string;
}

export interface ChatResponse {
    conversation_id: string;
    response: string;
    sources: Source[];
}

export interface UseChatOptions {
    api?: string;
    id?: string;
    initialMessages?: Message[];
    body?: {
        technologies?: string[];
        categories?: string[];
    };
    onResponse?: (response: Response) => void | Promise<void>;
    onFinish?: (message: Message) => void;
    onError?: (error: Error) => void;
}