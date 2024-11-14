// hooks/useChat.ts
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';

import { ChatResponse, UseChatOptions, Message } from '@/types/chat';


export interface UseChatHelpers {
    messages: Message[];
    error: undefined | Error;
    append: (content: string, options?: { technologies?: string[]; categories?: string[] }) => Promise<string | null | undefined>;
    reload: (options?: { technologies?: string[]; categories?: string[] }) => Promise<string | null | undefined>;
    stop: () => void;
    setMessages: (messages: Message[] | ((messages: Message[]) => Message[])) => void;
    input: string;
    setInput: React.Dispatch<React.SetStateAction<string>>;
    handleInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    handleSubmit: (e: React.FormEvent<HTMLFormElement>, options?: { technologies?: string[]; categories?: string[] }) => void;
    isLoading: boolean
}

export function useChat({
    api = '/api/chat',
    id: initialId,
    initialMessages = [],
    body = {},
    onResponse,
    onFinish,
    onError
}: UseChatOptions = {}): UseChatHelpers {
    const router = useRouter();
    const [messages, setMessages] = useState<Message[]>(initialMessages);
    const [input, setInput] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<undefined | Error>();
    const abortControllerRef = useRef<AbortController | null>(null);
    const conversationIdRef = useRef<string | undefined>(initialId);

    // Navigate to the conversation when ID changes
    const updateConversationId = useCallback((newId: string) => {
        if (newId !== conversationIdRef.current) {
            conversationIdRef.current = newId;
            router.push(`/chat/${newId}`);
            router.refresh();
        }
    }, [router]);

    useEffect(() => {
        const controller = new AbortController();
        abortControllerRef.current = controller;
        return () => {
            controller.abort();
        };
    }, []);

    const append = useCallback(
        async (content: string, options?: { technologies?: string[]; categories?: string[] }) => {
            if (!content.trim()) {
                return null;
            }

            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }

            const abortController = new AbortController();
            abortControllerRef.current = abortController;
            setIsLoading(true);
            setError(undefined);

            const userMessage: Message = {
                id: uuidv4(),
                content: content.trim(),
                role: 'user',
                sources: []
            };
            setMessages(messages => [...messages, userMessage]);

            try {
                const requestBody = {
                    message: content.trim(),
                    conversation_id: conversationIdRef.current,
                    technologies: options?.technologies || body.technologies || [],
                    categories: options?.categories || body.categories || []
                };

                const response = await fetch(api, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody),
                    signal: abortController.signal
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }

                const data: ChatResponse = await response.json();

                // Update conversation ID and navigate
                if (data.conversation_id) {
                    updateConversationId(data.conversation_id);
                }

                // Call onResponse after processing the response
                if (onResponse) {
                    await onResponse(response);
                }

                const assistantMessage: Message = {
                    id: uuidv4(),
                    content: data.response,
                    role: 'assistant',
                    sources: data.sources
                };

                setMessages(messages => [...messages, assistantMessage]);

                if (onFinish) {
                    onFinish(assistantMessage);
                }

                return data.conversation_id;
            } catch (err) {
                const error = err as Error;
                setError(error);
                if (onError) {
                    onError(error);
                }
            } finally {
                setIsLoading(false);
            }
        },
        [api, body, onResponse, onFinish, onError, updateConversationId]
    );

    const reload = useCallback(
        async (options?: { technologies?: string[]; categories?: string[] }) => {
            if (messages.length === 0) return null;

            const lastUserMessageIndex = messages.reduceRight((acc, message, index) => {
                if (acc === -1 && message.role === 'user') {
                    return index;
                }
                return acc;
            }, -1);

            if (lastUserMessageIndex === -1) return null;

            const newMessages = messages.slice(0, lastUserMessageIndex + 1);
            setMessages(newMessages);

            const lastUserMessage = messages[lastUserMessageIndex];
            return await append(lastUserMessage.content, options);
        },
        [append, messages]
    );

    const stop = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            setIsLoading(false);
        }
    }, []);

    const handleInputChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
            setInput(e.target.value);
        },
        []
    );

    const handleSubmit = useCallback(
        (e: React.FormEvent<HTMLFormElement>, options?: { technologies?: string[]; categories?: string[] }) => {
            e.preventDefault();
            if (!input.trim()) return;

            append(input.trim(), options);
            setInput('');
        },
        [input, append]
    );

    return {
        messages,
        append,
        error,
        reload,
        stop,
        setMessages,
        input,
        setInput,
        handleInputChange,
        handleSubmit,
        isLoading
    };
}