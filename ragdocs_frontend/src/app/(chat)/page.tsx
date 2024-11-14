'use client';

import { Chat } from '@/components/custom/chat';
import { generateUUID } from '@/lib/utils';

export default function Page() {
  const id = generateUUID();
  return (
    <Chat 
      key={id}
      initialMessages={[]} 
    />
  );
}