import { notFound } from 'next/navigation';

import { Chat } from '@/components/custom/chat';
import { Message, Conversation } from '@/types/chat';

async function getChat(id: string): Promise<{ messages: Message[] } | null> {
    try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/conversations/${id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            cache: 'no-store',
        });

        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error('Failed to fetch chat');
        }

        const data: Conversation = await response.json();

        if (!data?.messages) {
            return { messages: [] };
        }

        return { messages: data.messages };
    } catch (error) {
        console.error('Error fetching chat:', error);
        return null;
    }
}

interface PageProps {
    params: Promise<{ id: string }>;
}

export default async function ChatPage({ params }: PageProps) {
    // Await the params
    const { id } = await params;

    try {
        // If this is a new chat, return empty messages
        if (id === 'new') {
            return (
                <div className="flex-1 h-dvh">
                    <Chat initialMessages={[]} />
                </div>
            );
        }

        // Try to fetch existing chat
        const data = await getChat(id);

        // If chat not found, show not found page
        if (data === null) {
            notFound();
        }

        return (
            <div className="flex-1 h-dvh">
                <Chat initialMessages={data.messages} initialId={id} />
            </div>
        );
    } catch (error) {
        console.error('Error in ChatPage:', error);
        notFound();
    }
}

// Generate metadata for the page
export async function generateMetadata({ params }: PageProps) {
    const { id } = await params;

    if (id === 'new') {
        return {
            title: 'New Chat',
            description: 'Start a new conversation with your vector database assistant',
        };
    }

    try {
        const data = await getChat(id);
        if (!data) {
            return {
                title: 'Chat Not Found',
                description: 'The requested chat could not be found',
            };
        }

        return {
            title: 'Chat',
            description: 'Continue your conversation with your vector database assistant',
        };
    } catch (error) {
        return {
            title: 'Chat Error',
            description: 'An error occurred while loading the chat',
        };
    }
}