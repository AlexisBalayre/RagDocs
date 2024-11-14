'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { toast } from 'sonner';

import { useChat } from '@/lib/hooks/use-chat';
import { useScrollToBottom } from '@/lib/hooks/use-scroll-to-bottom';
import { Message } from '@/types/chat';

import { ChatHeader } from './chat-header';
import { ChatInput } from './chat-input';
import { ChatOverview } from './chat-overview';
import LoadingMessages from './loading-messages';
import { PreviewMessage } from './message';

interface ChatProps {
  initialMessages?: Array<Message>;
  initialId?: string;
}

export function Chat({ initialId, initialMessages = [] }: ChatProps) {
  const router = useRouter();
  const [conversationId, setConversationId] = useState<string | undefined>(initialId);

  const {
    messages,
    error,
    append,
    reload,
    stop,
    setMessages,
    input,
    setInput,
    handleInputChange,
    handleSubmit,
    isLoading
  } = useChat({
    api: '/api/chat',
    id: conversationId,
    initialMessages,
    body: {
      technologies: [],
      categories: []
    },
    onResponse: (response) => {
      if (!response.ok) {
        toast.error(`Error: ${response.statusText}`);
        return;
      }
    },
    onFinish: (message) => {
      router.refresh();
    },
    onError: (error) => {
      toast.error(error.message);
    }
  });

  const [messagesContainerRef, messagesEndRef] = useScrollToBottom<HTMLDivElement>();

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <ChatHeader />

      <div
        ref={messagesContainerRef}
        className="flex flex-col min-w-0 gap-6 flex-1 overflow-y-scroll pt-4 px-4 text-clip"
      >
        {messages.length === 0 && <ChatOverview />}

        {messages.map((message, index) => (
          <PreviewMessage
            key={message.id ?? String(index)}
            chatId={conversationId}
            message={message}
            isLoading={isLoading && index === messages.length - 1}
          />
        ))}

        {isLoading &&
          messages.length > 0 &&
          messages[messages.length - 1].role === 'user' && (
            <LoadingMessages />
          )}

        <div
          ref={messagesEndRef}
          className="shrink-0 min-w-[24px] min-h-[24px]"
        />
      </div>

      <form
        className="flex mx-auto px-4 bg-background pb-4 md:pb-6 gap-2 w-full md:max-w-3xl"
        onSubmit={handleSubmit}
      >
        <ChatInput
          chatId={conversationId}
          messages={messages}
          input={input}
          handleInputChange={handleInputChange}
          isLoading={isLoading}
          stop={stop}
          onSubmit={handleSubmit}
          onRegenerate={() => {
            if (isLoading) {
              toast.error("Please wait for the current response to complete");
              return Promise.resolve(null);
            }
            return reload();
          }}
        />
      </form>
    </div>
  );
}