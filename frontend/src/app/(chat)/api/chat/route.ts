import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

import { ChatResponse } from '@/types/chat';

// API configuration 
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Validation schemas
export const chatRequestSchema = z.object({
    message: z.string().min(1, 'Message is required'),
    conversation_id: z.string().optional(),
    technologies: z.array(z.string()).optional(),
    categories: z.array(z.string()).optional()
});

export async function POST(request: NextRequest) {
    try {
        // Parse and validate request body
        const body = await request.json();

        if (!body.message) {
            throw new z.ZodError([{
                path: ['message'],
                message: 'Message is required',
                code: 'invalid_type',
                expected: 'string',
                received: 'undefined',
            }]);
        }
        const validatedData = chatRequestSchema.parse(body);

        // Forward request to backend API
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(validatedData),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            return NextResponse.json(
                {
                    error: errorData?.detail || 'Backend API error',
                    status: response.status
                },
                { status: response.status }
            );
        }

        const data: ChatResponse = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('Chat API Error:', error);

        if (error instanceof z.ZodError) {
            return NextResponse.json(
                { error: 'Invalid request data', details: error.errors },
                { status: 400 }
            );
        }

        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}
