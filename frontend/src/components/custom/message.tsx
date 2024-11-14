'use client';

import cx from 'classnames';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp, ExternalLink, FileText, Info } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Message, Source } from '@/types/chat';

import { SparklesIcon } from './icons';
import { Markdown } from './markdown';
import { MessageActions } from './message-actions';


const SourceContent = ({ filePath }: { filePath: string }) => {
  const [content, setContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContent = async () => {
      try {
        const response = await fetch(`/${filePath}`);
        if (!response.ok) {
          throw new Error('Failed to load documentation');
        }
        const text = await response.text();
        setContent(text);
      } catch (err) {
        console.error('Error loading documentation:', err);
        setError(err instanceof Error ? err.message : 'Failed to load documentation');
      }
    };

    fetchContent();
  }, [filePath]);

  if (error) {
    return <div className="text-destructive">{error}</div>;
  }

  if (!content) {
    return <div className="text-muted-foreground">Loading documentation...</div>;
  }

  return <Markdown>{content}</Markdown>;
};

const SourceDetails = ({ source }: { source: Source }) => {
  let doc_url = ''

  if (source.technology === 'milvus') {
    doc_url = `https://milvus.io/docs/${source.file_path.split("/").pop()}`
  } else if (source.technology === 'weaviate') {
    doc_url = `https://weaviate.io/developers/weaviate/${source.file_path.replace("data/weaviate_docs/", "")?.replace("/index", "")?.split(".")[0]}`
  } else if (source.technology === 'qdrant') {
    doc_url = `https://qdrant.tech/${source.file_path.replace("data/qdrant_docs/", "")?.split(".")[0]}`
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" className="size-6 p-0">
          <Info size={14} />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>{source.technology}</span>
            <Badge variant="secondary">
              Score: {(source.score * 100).toFixed(1)}%
            </Badge>
          </DialogTitle>
          <div className="flex flex-col gap-2">
            <DialogDescription>
              Source from {source.section_title}
            </DialogDescription>
            {doc_url && (
              <Button
                variant="outline"
                size="sm"
                className="w-fit"
                asChild
              >
                <a href={doc_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink size={14} className="mr-2" />
                  Open documentation
                </a>
              </Button>
            )}
          </div>
        </DialogHeader>
        <ScrollArea className="mt-4 h-[50vh] pr-4">
          <SourceContent filePath={source.file_path} />
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}

const SourceItem = ({ source }: { source: Source }) => {
  let doc_url = ''

  if (source.technology === 'milvus') {
    doc_url = `https://milvus.io/docs/${source.file_path.split("/").pop()}`
  } else if (source.technology === 'weaviate') {
    doc_url = `https://weaviate.io/developers/weaviate/${source.file_path.replace("data/weaviate_docs/", "")?.replace("index", "")?.split(".")[0]}`
  } else if (source.technology === 'qdrant') {
    doc_url = `https://qdrant.tech/${source.file_path.replace("data/qdrant_docs/", "")?.split(".")[0]}`
  }

  return (
    <div className="group flex items-center gap-2 rounded-md border bg-muted/50 px-3 py-1.5 text-sm">
      <Badge variant="secondary" className="bg-background">
        {source.technology}
      </Badge>
      <span className="truncate text-muted-foreground">{source.content_preview}</span>
      <div className="ml-auto flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <SourceDetails source={source} />
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="size-6 p-0"
                asChild
              >
                <a href={doc_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink size={14} />
                </a>
              </Button>
            </TooltipTrigger>
            <TooltipContent>Open documentation</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  )
};

export const PreviewMessage = ({
  chatId,
  message,
  isLoading,
}: {
  chatId?: string;
  message: Message;
  isLoading: boolean;
}) => {
  const [isSourcesExpanded, setIsSourcesExpanded] = useState(true);
  const hasSources = message.sources && message.sources.length > 0;

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      data-role={message.role}
    >
      <div
        className={cx(
          'group-data-[role=user]/message:bg-primary group-data-[role=user]/message:text-primary-foreground flex gap-4 group-data-[role=user]/message:px-3 w-full group-data-[role=user]/message:w-fit group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:py-2 rounded-xl'
        )}
      >
        {message.role === 'assistant' && (
          <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
            <SparklesIcon size={14} />
          </div>
        )}

        <div className="flex flex-col gap-2 w-full min-w-0">
          {message.content && (
            <div className="flex flex-col gap-4">
              <Markdown>{message.content as string}</Markdown>
            </div>
          )}

          <MessageActions
            key={`action-${message.id}`}
            chatId={chatId}
            message={message}
            isLoading={isLoading}
          />

          {hasSources && (
            <Collapsible
              open={isSourcesExpanded}
              onOpenChange={setIsSourcesExpanded}
              className="mt-2"
            >
              <div className="flex items-center gap-2">
                <FileText size={14} className="text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  {(message.sources?.length ?? 0)} source{(message.sources?.length ?? 0) > 1 ? 's' : ''}
                </span>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-6 px-2 ml-auto">
                    {isSourcesExpanded ? (
                      <ChevronUp size={14} />
                    ) : (
                      <ChevronDown size={14} />
                    )}
                  </Button>
                </CollapsibleTrigger>
              </div>
              <CollapsibleContent className="space-y-1.5 mt-2">
                {message.sources?.map((source, index) => (
                  <SourceItem
                    key={`${source.technology}-${index}`}
                    source={source}
                  />
                ))}
              </CollapsibleContent>
            </Collapsible>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export const ThinkingMessage = () => (
  <motion.div
    className="w-full mx-auto max-w-3xl px-4 group/message"
    initial={{ y: 5, opacity: 0 }}
    animate={{ y: 0, opacity: 1, transition: { delay: 0.5 } }}
    data-role="assistant"
  >
    <div className="flex gap-4 w-full rounded-xl">
      <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
        <SparklesIcon size={14} />
      </div>

      <div className="flex flex-col gap-2 w-full">
        <div className="flex gap-2 text-muted-foreground items-center">
          <span>Thinking</span>
          <motion.span
            animate={{ opacity: [0, 1, 0] }}
            transition={{ repeat: Infinity, duration: 2 }}
          >
            ...
          </motion.span>
        </div>
      </div>
    </div>
  </motion.div>
);