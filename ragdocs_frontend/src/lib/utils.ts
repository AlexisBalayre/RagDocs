import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'


// Helper for combining Tailwind classes
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

// Format date for display
export function formatDate(date: string | Date) {
    const d = new Date(date)
    return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    })
}

// Format time for display
export function formatTime(date: string | Date) {
    const d = new Date(date)
    return d.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    })
}

// Truncate text with ellipsis
export function truncateText(text: string, maxLength: number) {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength - 3) + '...'
}

// Generate chat title from first message
export function generateTitle(message: string) {
    const words = message.split(/\s+/)
    const titleWords = words.slice(0, 6)
    let title = titleWords.join(' ')

    if (title.length > 80) {
        title = title.slice(0, 77) + '...'
    }

    return title
}

// Sleep utility for artificial delays
export const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export function generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

