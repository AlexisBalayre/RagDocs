import { Loader2 } from 'lucide-react';
import React, { useState, useEffect } from 'react';

const LoadingMessages = () => {
    const [messageIndex, setMessageIndex] = useState(0);
    const [isComplete, setIsComplete] = useState(false);

    const messages = [
        "Initializing process...",
        "Searching through documentation...",
        "Gathering relevant information...",
        "Analyzing content thoroughly...",
        "Processing data points...",
        "Organizing findings...",
        "Preparing comprehensive response...",
        "Validating information...",
        "Formatting results...",
        "Almost ready with your answer...",
        "Finalizing response..."
    ];

    useEffect(() => {
        const interval = setInterval(() => {
            setMessageIndex((current) => {
                if (current === messages.length - 1) {
                    setIsComplete(true);
                    return current;
                }
                return current + 1;
            });
        }, 3000);

        return () => clearInterval(interval);
    }, [messages.length]);

    const progress = isComplete 
        ? 100 
        : ((messageIndex + 1) / messages.length) * 100;

    return (
        <div className="flex flex-col items-center space-y-4 p-8">
            <div className="flex items-center space-x-2">
                <Loader2 className="size-6 animate-spin text-primary" />
                <span className="text-lg font-medium text-primary animate-pulse">
                    {messages[messageIndex]}
                </span>
            </div>
            <div className="w-64 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                    className="h-full bg-primary transition-all duration-500 ease-in-out"
                    style={{ width: `${progress}%` }}
                />
            </div>
        </div>
    );
};

export default LoadingMessages;