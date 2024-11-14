'use client';

import cx from 'classnames';
import { motion } from 'framer-motion';
import { ArrowUp, StopCircle, RotateCcw, Database } from 'lucide-react';
import React, { useRef, useEffect, useCallback, useState } from 'react';
import { toast } from 'sonner';
import { useLocalStorage } from 'usehooks-ts';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Textarea } from '@/components/ui/textarea';

const suggestedPrompts = [
  {
    title: 'Explain vector databases',
    label: 'and their use cases',
    action: 'Explain vector databases and their main use cases in modern applications.',
  },
  {
    title: 'Compare Milvus and Weaviate',
    label: 'performance characteristics',
    action: 'Compare the performance characteristics of Milvus and Weaviate for vector search.',
  },
] as const;

const availableTechnologies = [
  { id: 'milvus', name: 'Milvus' },
  { id: 'weaviate', name: 'Weaviate' },
  { id: 'qdrant', name: 'Qdrant' },
] as const;

interface ChatInputProps {
  chatId?: string;
  messages: any[];
  input: string;
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  isLoading: boolean;
  stop: () => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>, options?: { technologies?: string[]; categories?: string[] }) => void;
  onRegenerate?: (options?: { technologies?: string[]; categories?: string[] }) => Promise<string | null | undefined>;
  className?: string;
}

export function ChatInput({
  chatId,
  messages,
  input,
  handleInputChange,
  isLoading,
  stop,
  onSubmit,
  onRegenerate,
  className,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [localStorageInput, setLocalStorageInput] = useLocalStorage(`chat-input-${chatId || 'new'}`, '');
  const [selectedTechnologies, setSelectedTechnologies] = useLocalStorage<string[]>(`selected-technologies-${chatId || 'new'}`, []);

  // Adjust textarea height based on content
  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight + 2}px`;
    }
  }, []);

  // Update local storage when input changes
  useEffect(() => {
    setLocalStorageInput(input);
  }, [input, setLocalStorageInput]);

  // Initialize and adjust textarea height
  useEffect(() => {
    adjustHeight();
  }, [adjustHeight, input]);

  // Handle technology selection
  const handleTechnologyToggle = useCallback((technologyId: string) => {
    setSelectedTechnologies(prev => {
      const isSelected = prev.includes(technologyId);
      if (isSelected) {
        return prev.filter(id => id !== technologyId);
      } else {
        return [...prev, technologyId];
      }
    });
  }, [setSelectedTechnologies]);

  // Handle suggestion click
  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      const changeEvent = new Event('change', { bubbles: true }) as unknown as React.ChangeEvent<HTMLTextAreaElement>;
      Object.defineProperty(changeEvent, 'target', { value: { value: suggestion } });
      handleInputChange(changeEvent);

      const submitEvent = new Event('submit') as unknown as React.FormEvent<HTMLFormElement>;
      submitEvent.preventDefault = () => {};
      
      onSubmit(submitEvent, { technologies: selectedTechnologies });
    },
    [handleInputChange, onSubmit, selectedTechnologies]
  );

  // Handle manual submit button click
  const handleManualSubmit = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      const submitEvent = new Event('submit') as unknown as React.FormEvent<HTMLFormElement>;
      submitEvent.preventDefault = () => {};
      onSubmit(submitEvent, { technologies: selectedTechnologies });
    },
    [onSubmit, selectedTechnologies]
  );

  // Handle regenerate click
  const handleRegenerate = useCallback(async () => {
    if (isLoading) {
      toast.error("Please wait for the current response to complete");
      return;
    }
    if (onRegenerate) {
      await onRegenerate({ technologies: selectedTechnologies });
    }
  }, [isLoading, onRegenerate, selectedTechnologies]);

  return (
    <div className="relative w-full flex flex-col gap-4">
      {!input && !isLoading && messages.length === 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full">
          {suggestedPrompts.map((prompt, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Button
                type="button"
                variant="ghost"
                onClick={() => handleSuggestionClick(prompt.action)}
                className="text-left border rounded-xl px-4 py-3.5 text-sm flex flex-col w-full h-auto justify-start items-start hover:bg-muted"
              >
                <span className="font-medium">{prompt.title}</span>
                <span className="text-muted-foreground">{prompt.label}</span>
              </Button>
            </motion.div>
          ))}
        </div>
      )}

      <div className="relative flex items-end w-full">
        <Textarea
          ref={textareaRef}
          name="message"
          placeholder="Ask a question..."
          value={input}
          onChange={(e) => {
            handleInputChange(e);
            adjustHeight();
          }}
          className={cx(
            'min-h-[48px] max-h-[calc(75dvh)]',
            'overflow-y-auto resize-none',
            'rounded-xl text-base bg-muted',
            'w-full pr-32 py-3',  // Increased right padding for the extra button
            'focus-visible:ring-1',
            'scrollbar-thin scrollbar-thumb-rounded-full scrollbar-track-transparent',
            'scrollbar-thumb-muted-foreground/20 hover:scrollbar-thumb-muted-foreground/25',
            'focus:scrollbar-thumb-muted-foreground/30',
            className
          )}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              if (isLoading) {
                toast.error('Please wait for the current response to complete');
                return;
              }
              const submitEvent = new Event('submit') as unknown as React.FormEvent<HTMLFormElement>;
              submitEvent.preventDefault = () => {};
              onSubmit(submitEvent, { technologies: selectedTechnologies });
            }
          }}
          aria-label="Chat input"
        />

        <div className="absolute bottom-2 right-2 flex gap-1">
          {isLoading ? (
            <Button
              type="button"
              className="rounded-full p-1.5 h-fit m-0.5 border dark:border-zinc-600"
              onClick={stop}
              aria-label="Stop generating"
            >
              <StopCircle size={14} />
            </Button>
          ) : (
            <>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    className="rounded-full p-1.5 h-fit m-0.5 border dark:border-zinc-600"
                    aria-label="Select technologies"
                  >
                    <Database size={14} />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuLabel>Technologies</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {availableTechnologies.map((tech) => (
                    <DropdownMenuCheckboxItem
                      key={tech.id}
                      checked={selectedTechnologies.includes(tech.id)}
                      onCheckedChange={() => handleTechnologyToggle(tech.id)}
                    >
                      {tech.name}
                    </DropdownMenuCheckboxItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              {onRegenerate && (
                <Button
                  type="button"
                  className="rounded-full p-1.5 h-fit m-0.5 border dark:border-zinc-600"
                  onClick={handleRegenerate}
                  disabled={!chatId}
                  aria-label="Regenerate response"
                >
                  <RotateCcw size={14} />
                </Button>
              )}
              <Button
                type="button"
                className="rounded-full p-1.5 h-fit m-0.5 border dark:border-zinc-600"
                onClick={handleManualSubmit}
                disabled={!input.trim()}
                aria-label="Send message"
              >
                <ArrowUp size={14} />
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}