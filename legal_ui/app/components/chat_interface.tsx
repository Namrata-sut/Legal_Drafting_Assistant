'use client';

import React, { useState } from 'react';
import axios from 'axios';

interface Message {
  sender: 'user' | 'ai';
  text: string;
}

interface Question {
  key: string;
  prompt: string;
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuestions, setCurrentQuestions] = useState<Question[]>([]);
  const [context, setContext] = useState<Record<string, any>>({});
  const [query, setQuery] = useState('');

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = { sender: 'user', text: inputValue };
    setMessages(prev => [...prev, userMessage]);

    const currentQuery = messages.length === 0 ? inputValue : query;
    if (messages.length === 0) setQuery(currentQuery);

    const newContext = { ...context };
    if (currentQuestions.length > 0) {
      newContext[currentQuestions[0].key] = inputValue;
      setContext(newContext);
    }

    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/draft/`, {
        query: currentQuery,
        context: newContext,
      });

      const { status, message, questions, draft } = response.data;
      const aiResponse: Message = { sender: 'ai', text: '' };

      if (status === 'in_progress') {
        aiResponse.text = `${message}\n\n${questions.join('\n')}`;
        const structuredQuestions = questions.map((q: string) => {
          const keyMatch = q.match(/'(.*?)'/);
          return { key: keyMatch ? keyMatch[1] : '', prompt: q };
        });
        setCurrentQuestions(structuredQuestions);
      } else if (status === 'complete') {
        aiResponse.text = `**Draft Generated Successfully:**\n\n---\n\n${draft}`;
        setCurrentQuestions([]);
      }

      setMessages(prev => [...prev, aiResponse]);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message;
      setMessages(prev => [...prev, { sender: 'ai', text: `Error: ${errorMessage}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <h2 className="chat-header">2. Draft a New Document</h2>
      <div className="chat-body">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`chat-message ${msg.sender === 'user' ? 'chat-message-user' : 'chat-message-ai'}`}
          >
            <p>{msg.text}</p>
          </div>
        ))}
        {isLoading && <div className="chat-loading">AI is thinking...</div>}
      </div>
      <form onSubmit={handleSendMessage} className="chat-form">
        <div className="chat-input-container">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={messages.length === 0 ? "What would you like to draft?" : "Type your answer here..."}
            className="chat-input"
            disabled={isLoading}
          />
          <button type="submit" className="chat-send-button" disabled={isLoading}>
            Send
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
