import { cookies } from 'next/headers';

import { AppSidebar } from '@/components/custom/app-sidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

export const experimental_ppr = true;

interface LayoutProps {
  children: React.ReactNode;
}

export default async function ChatLayout({ children }: LayoutProps) {
  const cookieStore = await cookies();
  const isCollapsed = cookieStore.get('sidebar:state')?.value !== 'true';

  return (
    <div className="flex h-dvh bg-background overflow-hidden">
      <SidebarProvider defaultOpen={!isCollapsed}>
        <AppSidebar />
        <SidebarInset className="flex-1 min-w-0">
          {children}
        </SidebarInset>
      </SidebarProvider>
    </div>
  );
}