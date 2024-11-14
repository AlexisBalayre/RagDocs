// hooks/useChat.ts
import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';

import { Conversation } from '@/types/chat';

export function useHistory() {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const fetchConversations = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/history');

            if (!response.ok) {
                throw new Error('Failed to fetch conversations');
            }

            const data = await response.json();
            setConversations(data);
        } catch (err) {
            setError(err as Error);
            toast.error('Failed to fetch conversations');
        } finally {
            setIsLoading(false);
        }
    }, []);

    const getConversation = useCallback(async (id: string) => {
        try {
            const response = await fetch(`/api/history/${id}`);

            if (response.status === 404) {
                return null;
            }

            if (!response.ok) {
                throw new Error('Failed to fetch conversation');
            }

            return await response.json() as Conversation;
        } catch (err) {
            toast.error('Failed to fetch conversation');
            throw err;
        }
    }, []);

    const deleteConversation = useCallback(async (id: string) => {
        try {
            const response = await fetch(`/api/history/${id}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.status === 404) {
                toast.error('Conversation not found');
                return false;
            }

            if (!response.ok) {
                throw new Error('Failed to delete conversation');
            }

            // Optimistically update the UI by removing the conversation from state
            setConversations(prevConversations =>
                prevConversations.filter(conv => conv.id !== id)
            );

            toast.success('Conversation deleted');
            return true;
        } catch (err) {
            toast.error('Failed to delete conversation');
            // If the deletion fails on the server, refresh the list to ensure sync
            await fetchConversations();
            throw err;
        }
    }, [fetchConversations]);

    // Load conversations on mount
    useEffect(() => {
        fetchConversations();
    }, [fetchConversations]);

    // Reload conversations when something changes
    useEffect(() => {
        const interval = setInterval(fetchConversations, 60000);
        return () => clearInterval(interval);
    }, [fetchConversations]);

    return {
        conversations,
        isLoading,
        error,
        refresh: fetchConversations,
        getConversation,
        deleteConversation
    };
}