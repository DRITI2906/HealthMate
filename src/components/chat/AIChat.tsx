import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Bot, User, Brain, Stethoscope, Apple, Heart, MessageSquare, FileText } from 'lucide-react';

import { Button } from '../ui/Button';
import { api } from '../../utils/api';
import { ChatMessage } from '../../types/health';
import ReactMarkdown from "react-markdown"; 

const agentTypes = [
  { id: 'general', name: 'General Health', icon: <Stethoscope className="w-4 h-4" />, color: 'bg-blue-500' },
  { id: 'symptom', name: 'Symptom Checker', icon: <Heart className="w-4 h-4" />, color: 'bg-red-500' },
  { id: 'nutrition', name: 'Nutrition', icon: <Apple className="w-4 h-4" />, color: 'bg-green-500' },
  { id: 'mental-health', name: 'Mental Health', icon: <Brain className="w-4 h-4" />, color: 'bg-purple-500' }
];

const mockMessages: ChatMessage[] = [
  {
    id: '1',
    content: "Hello! I'm your AI health assistant. I have specialized agents to help with different aspects of your health. How can I assist you today?",
    sender: 'ai',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    agentType: 'general'
  }
];

// ADD THIS UTILITY FUNCTION
const isValidToken = (token: string | null): boolean => {
  if (!token) return false;
  
  try {
    // Simple check for JWT structure (3 parts separated by dots)
    const parts = token.split('.');
    return parts.length === 3;
  } catch {
    return false;
  }
};

// ✅ MAKE SURE THIS IS A NAMED EXPORT (not default export)
export function AIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>(mockMessages);
  const [inputValue, setInputValue] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string>('general');
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [responseStyle, setResponseStyle] = useState<'concise' | 'detailed'>('concise');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // ADD THIS USEEFFECT FOR INITIAL AUTH CHECK
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    console.log('AIChat mounted with token:', token);
    if (!isValidToken(token)) {
      setError("Please log in to use the AI chat feature");
    }
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isTyping) return;
    
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date(),
      agentType: selectedAgent as any
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);
    setError(null);

    try {
      const response = await api.post<{ response: string }>('/api/chat', {
        message: inputValue,
        agent_type: selectedAgent,
        response_style: responseStyle
      });

      if (response.error) {
        if (response.error.includes('401') || response.error.includes('403')) {
          // Token is expired or invalid
          localStorage.removeItem('access_token');
          setError("❌ Session expired. Please log in again.");
          setTimeout(() => navigate('/signin'), 2000);
        } else {
          setError(`Error: ${response.error}`);
        }
        setIsTyping(false);
        return;
      }

      if (!response.data) {
        throw new Error('No data in response');
      }

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: response.data.response,
        sender: 'ai',
        timestamp: new Date(),
        agentType: selectedAgent as any
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (err: any) {
      console.error("Error in chat:", err);
      setError('⚠️ Could not reach AI backend.');
    } finally {
      setIsTyping(false);
    }
  };

  const getAgentInfo = (agentType?: string) => {
    return agentTypes.find(agent => agent.id === agentType) || agentTypes[0];
  };

  // ADD THIS TO CHECK AUTH STATUS
  const isAuthenticated = isValidToken(localStorage.getItem("access_token"));

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800">
      <div className="border-b border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">AI Health Assistant</h2>
        <p className="text-gray-600 dark:text-gray-300 mt-1">Multi-agent AI system powered by Gemini, LangGraph & CrewAI</p>
      </div>
      
      {/* Agent Selector and Response Style Toggle */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Agent Selector */}
          <div className="flex flex-wrap gap-2">
            {agentTypes.map((agent) => (
              <button
                key={agent.id}
                onClick={() => setSelectedAgent(agent.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                  selectedAgent === agent.id 
                    ? `${agent.color} text-white shadow-md` 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600 border border-gray-200 dark:border-gray-600 shadow-sm'
                }`}
              >
                {agent.icon}
                {agent.name}
              </button>
            ))}
          </div>
          
          {/* Response Style Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 dark:text-gray-300 font-medium">Response Style:</span>
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setResponseStyle('concise')}
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  responseStyle === 'concise'
                    ? 'bg-white dark:bg-gray-600 text-gray-800 dark:text-gray-100 shadow-sm'
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100'
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                Concise
              </button>
              <button
                onClick={() => setResponseStyle('detailed')}
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  responseStyle === 'detailed'
                    ? 'bg-white dark:bg-gray-600 text-gray-800 dark:text-gray-100 shadow-sm'
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100'
                }`}
              >
                <FileText className="w-4 h-4" />
                Detailed
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ADD LOGIN PROMPT FOR UNAUTHENTICATED USERS */}
      {!isAuthenticated && (
        <div className="text-center p-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg mx-6 my-4">
          <p className="text-yellow-700 dark:text-yellow-300 font-medium">
            Please log in to use the AI chat feature
          </p>
          <Button 
            onClick={() => navigate('/signin')} 
            className="mt-2 bg-yellow-500 hover:bg-yellow-600"
          >
            Log In
          </Button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex items-start gap-3 max-w-[80%] ${message.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  message.sender === 'user' ? 'bg-gray-600 text-white' : getAgentInfo(message.agentType).color + ' text-white'
                }`}>
                  {message.sender === 'user' ? <User className="w-4 h-4" /> : getAgentInfo(message.agentType).icon}
                </div>
                <div className={`rounded-2xl px-4 py-3 ${
                  message.sender === 'user' 
                    ? 'bg-blue-600 text-white shadow-md' 
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-white shadow-md border border-gray-200 dark:border-gray-600'
                }`}>
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                  <p className="text-xs mt-2 opacity-70">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getAgentInfo(selectedAgent).color} text-white`}>
                  <Bot className="w-5 h-5" />
                </div>
                <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl px-4 py-3 border border-gray-200 dark:border-gray-600 shadow-md">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          {error && (
            <div className="text-red-500 text-sm px-4">{error}</div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={`Ask the ${getAgentInfo(selectedAgent).name} agent... (${responseStyle === 'concise' ? 'brief' : 'detailed'} response)`}
            className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            disabled={isTyping || !isAuthenticated}
          />
          <Button onClick={handleSendMessage} disabled={!inputValue.trim() || isTyping || !isAuthenticated}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}