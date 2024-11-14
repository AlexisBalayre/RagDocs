'use client';

import { toast } from 'sonner';
import { useCopyToClipboard } from 'usehooks-ts';

import { Message } from '@/types/chat';

import { CopyIcon } from './icons';
import { Button } from '../ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';

interface MessageActionsProps {
  chatId?: string;
  message: Message;
  isLoading: boolean;
}

export function MessageActions({ message, isLoading }: MessageActionsProps) {
  const [_, copyToClipboard] = useCopyToClipboard();

  // Don't render actions for user messages or while loading
  if (isLoading || message.role === 'user') {
    return null;
  }

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex flex-row gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              className="py-1 px-2 h-fit text-muted-foreground"
              variant="outline"
              onClick={async () => {
                await copyToClipboard(message.content as string);
                toast.success('Copied to clipboard!');
              }}
            >
              <CopyIcon />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Copy</TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}