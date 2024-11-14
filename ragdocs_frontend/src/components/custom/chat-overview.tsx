'use client';

import { motion } from 'framer-motion';
import { Database, Search, BookOpen } from 'lucide-react';

const exampleQuestions = [
  {
    title: "How does Milvus handle scalability?",
    description: "Learn about scaling options and deployment strategies"
  },
  {
    title: "What indexing methods are available?",
    description: "Explore different vector index types and their use cases"
  },
  {
    title: "Compare performance characteristics",
    description: "Understand performance metrics and optimization"
  }
];

export function ChatOverview() {
  return (
    <motion.div
      className="w-full max-w-2xl mx-auto"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Icons */}
      <div className="flex justify-center gap-8 items-center mb-8">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Database className="size-8 text-muted-foreground" />
        </motion.div>
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Search className="size-8 text-muted-foreground" />
        </motion.div>
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <BookOpen className="size-8 text-muted-foreground" />
        </motion.div>
      </div>

      {/* Main content */}
      <div className="space-y-8 text-center px-4">
        <div>
          <h1 className="text-2xl font-semibold mb-2">
            Welcome to VectorDB RAG Assistant 
          </h1>
          <p className="text-muted-foreground">
            Get accurate, source-backed answers from the documentation
          </p>
        </div>

        {/* Example questions */}
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-muted-foreground">
            Try asking about:
          </h2>
          <div className="grid gap-3">
            {exampleQuestions.map((question, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.1 }}
                className="p-4 border rounded-lg bg-muted/50 text-left hover:bg-muted/80 transition-colors"
              >
                <h3 className="font-medium mb-1">{question.title}</h3>
                <p className="text-sm text-muted-foreground">
                  {question.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}