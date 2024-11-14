import cx from 'classnames';
import { isToday, isYesterday, subMonths, subWeeks } from 'date-fns';
import { MoreHorizontal, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';


import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';
import { useHistory } from '@/lib/hooks/use-history';
import { Conversation } from '@/types/chat';

type GroupedConversations = {
  today: Conversation[];
  yesterday: Conversation[];
  lastWeek: Conversation[];
  lastMonth: Conversation[];
  older: Conversation[];
};

const ConversationItem = ({
  conversation,
  isActive,
  onDelete,
  setOpenMobile,
}: {
  conversation: Conversation;
  isActive: boolean;
  onDelete: (id: string) => void;
  setOpenMobile: (open: boolean) => void;
}) => (
  <SidebarMenuItem>
    <SidebarMenuButton asChild isActive={isActive}>
      <Link href={`/chat/${conversation.id}`} onClick={() => setOpenMobile(false)}>
        <span className="truncate">{conversation.title || 'New Conversation'}</span>
      </Link>
    </SidebarMenuButton>
    <DropdownMenu modal={true}>
      <DropdownMenuTrigger asChild>
        <SidebarMenuAction
          className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground mr-0.5"
          showOnHover={!isActive}
        >
          <MoreHorizontal className="size-4" />
          <span className="sr-only">More</span>
        </SidebarMenuAction>
      </DropdownMenuTrigger>
      <DropdownMenuContent side="bottom" align="end">
        <DropdownMenuItem
          className="cursor-pointer text-destructive focus:bg-destructive/15 focus:text-destructive"
          onSelect={() => onDelete(conversation.id)}
        >
          <Trash2 className="size-4 mr-2" />
          <span>Delete</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </SidebarMenuItem>
);

const LoadingSkeleton = () => (
  <SidebarGroup>
    <div className="px-2 py-1 text-xs text-sidebar-foreground/50">
      Loading...
    </div>
    <SidebarGroupContent>
      <div className="flex flex-col">
        {[44, 32, 28, 64, 52].map((width) => (
          <div
            key={width}
            className="rounded-md h-8 flex gap-2 px-2 items-center"
          >
            <div
              className="h-4 rounded-md flex-1 max-w-[--skeleton-width] animate-pulse bg-sidebar-accent-foreground/10"
              style={{ '--skeleton-width': `${width}%` } as React.CSSProperties}
            />
          </div>
        ))}
      </div>
    </SidebarGroupContent>
  </SidebarGroup>
);

const ErrorState = () => (
  <SidebarGroup>
    <SidebarGroupContent>
      <div className="text-destructive w-full flex flex-row justify-center items-center text-sm gap-2">
        Failed to load conversations
      </div>
    </SidebarGroupContent>
  </SidebarGroup>
);

const EmptyState = () => (
  <SidebarGroup>
    <SidebarGroupContent>
      <div className="text-zinc-500 w-full flex flex-row justify-center items-center text-sm gap-2">
        <div>Your conversations will appear here</div>
      </div>
    </SidebarGroupContent>
  </SidebarGroup>
);

const groupConversationsByDate = (conversations: Conversation[]): GroupedConversations => {
  const now = new Date();
  const oneWeekAgo = subWeeks(now, 1);
  const oneMonthAgo = subMonths(now, 1);

  // First, sort all conversations by date in descending order (newest first)
  const sortedConversations = [...conversations].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  return sortedConversations.reduce(
    (groups, conversation) => {
      const date = new Date(conversation.created_at);

      if (isToday(date)) {
        groups.today.push(conversation);
      } else if (isYesterday(date)) {
        groups.yesterday.push(conversation);
      } else if (date > oneWeekAgo) {
        groups.lastWeek.push(conversation);
      } else if (date > oneMonthAgo) {
        groups.lastMonth.push(conversation);
      } else {
        groups.older.push(conversation);
      }

      return groups;
    },
    {
      today: [],
      yesterday: [],
      lastWeek: [],
      lastMonth: [],
      older: [],
    } as GroupedConversations
  );
};

export function SidebarHistory() {
  const { setOpenMobile } = useSidebar();
  const { id } = useParams();
  const router = useRouter();
  const { conversations, isLoading, error, deleteConversation } = useHistory();

  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const handleDelete = async () => {
    if (!deleteId) return;

    try {
      await deleteConversation(deleteId);
      setShowDeleteDialog(false);

      // Redirect to home if the deleted conversation is currently active
      if (deleteId === id) {
        router.push('/');
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  if (error) return <ErrorState />;
  if (isLoading) return <LoadingSkeleton />;
  if (!conversations?.length) return <EmptyState />;

  const groupedConversations = groupConversationsByDate(conversations);

  const renderConversationGroup = (
    conversations: Conversation[],
    label: string,
    showMarginTop: boolean = true
  ) => {
    if (conversations.length === 0) return null;

    return (
      <>
        <div
          className={cx(
            "px-2 py-1 text-xs text-sidebar-foreground/50",
            showMarginTop && "mt-6"
          )}
        >
          {label}
        </div>
        {conversations.map((conversation) => (
          <ConversationItem
            key={conversation.id}
            conversation={conversation}
            isActive={conversation.id === id}
            onDelete={(id) => {
              setDeleteId(id);
              setShowDeleteDialog(true);
            }}
            setOpenMobile={setOpenMobile}
          />
        ))}
      </>
    );
  };

  return (
    <>
      <SidebarGroup>
        <SidebarGroupContent>
          <SidebarMenu>
            {renderConversationGroup(groupedConversations.today, "Today", false)}
            {renderConversationGroup(groupedConversations.yesterday, "Yesterday")}
            {renderConversationGroup(groupedConversations.lastWeek, "Last 7 days")}
            {renderConversationGroup(groupedConversations.lastMonth, "Last 30 days")}
            {renderConversationGroup(groupedConversations.older, "Older")}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete your
              conversation and remove it from our servers.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}