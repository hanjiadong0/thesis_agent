import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Loader2, Lightbulb, CheckCircle, ArrowRight } from 'lucide-react';
import { 
  brainstormChat, 
  finalizeTopic, 
  ChatMessage, 
  BrainstormingResponse,
  AI_PROVIDERS,
  THESIS_FIELDS 
} from '../services/api';

interface BrainstormingChatProps {
  onTopicFinalized: (topic: string, description: string) => void;
  onBack?: () => void;
}

export default function BrainstormingChat({ onTopicFinalized, onBack }: BrainstormingChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [topicClarity, setTopicClarity] = useState<'low' | 'medium' | 'high'>('low');
  const [suggestedTopic, setSuggestedTopic] = useState<string | null>(null);
  const [suggestedDescription, setSuggestedDescription] = useState<string | null>(null);
  const [selectedField, setSelectedField] = useState('Computer Science');
  const [selectedAI, setSelectedAI] = useState('ollama');
  const [isReady, setIsReady] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    // Send initial message when ready
    if (isReady && messages.length === 0) {
      handleInitialMessage();
    }
  }, [isReady, selectedField]);

  const handleInitialMessage = async () => {
    // Clear any previous brainstorming data
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem('brainstormed_topic');
      window.sessionStorage.removeItem('brainstormed_description');
      window.sessionStorage.removeItem('brainstormed_field');
    }
    
    const initialMessage = `Hello! I'm studying ${selectedField} and I need help brainstorming a thesis topic. I'm not sure where to start.`;
    await sendMessage(initialMessage, true);
  };

  const sendMessage = async (message: string, isInitial: boolean = false) => {
    if ((!message.trim() && !isInitial) || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    const newMessages = isInitial ? [userMessage] : [...messages, userMessage];
    setMessages(newMessages);
    setCurrentMessage('');
    setIsLoading(true);

    try {
      const response: BrainstormingResponse = await brainstormChat({
        message: message,
        conversation_history: messages,
        user_field: selectedField,
        ai_provider: selectedAI
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setTopicClarity(response.topic_clarity);
      
      if (response.suggested_topic) {
        setSuggestedTopic(response.suggested_topic);
      }
      if (response.suggested_description) {
        setSuggestedDescription(response.suggested_description);
      }

    } catch (error) {
      console.error('Brainstorming error:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Could you please try again?',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(currentMessage);
  };

  const handleFinalizeTopic = async () => {
    if (messages.length === 0) return;

    setIsLoading(true);
    try {
      const result = await finalizeTopic({
        conversation_history: messages,
        user_field: selectedField,
        ai_provider: selectedAI
      });

      // Store the field along with topic and description
      window.sessionStorage.setItem('brainstormed_field', selectedField);
      
      onTopicFinalized(result.thesis_topic, result.thesis_description);
    } catch (error) {
      console.error('Topic finalization error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getTopicClarityColor = () => {
    switch (topicClarity) {
      case 'high': return 'text-success-600 bg-success-50 border-success-200';
      case 'medium': return 'text-warning-600 bg-warning-50 border-warning-200';
      default: return 'text-secondary-600 bg-secondary-50 border-secondary-200';
    }
  };

  const getTopicClarityText = () => {
    switch (topicClarity) {
      case 'high': return 'Topic is well-defined!';
      case 'medium': return 'Getting clearer...';
      default: return 'Let\'s explore your ideas...';
    }
  };

  if (!isReady) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card-clean">
          <div className="card-header text-center">
            <div className="flex items-center justify-center mb-4">
              <Lightbulb className="h-8 w-8 text-primary-600 mr-3" />
              <h1 className="text-3xl font-bold text-secondary-900">Thesis Topic Brainstorming</h1>
            </div>
            <p className="text-secondary-600 text-lg">
              Let's have a conversation to help you develop the perfect thesis topic!
            </p>
          </div>

          <div className="space-y-6">
            {/* Field Selection */}
            <div>
              <label className="block text-lg font-medium text-secondary-900 mb-3">
                What field are you studying? *
              </label>
              <select
                value={selectedField}
                onChange={(e) => setSelectedField(e.target.value)}
                className="form-input text-lg"
              >
                {THESIS_FIELDS.map((field) => (
                  <option key={field} value={field}>{field}</option>
                ))}
              </select>
            </div>

            {/* AI Provider Selection */}
            <div>
              <label className="block text-lg font-medium text-secondary-900 mb-3">
                Choose Your AI Assistant *
              </label>
              <div className="space-y-3">
                {AI_PROVIDERS.map((provider) => (
                  <label
                    key={provider.value}
                    className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                      selectedAI === provider.value
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-secondary-200 hover:border-secondary-300'
                    }`}
                  >
                    <input
                      type="radio"
                      value={provider.value}
                      checked={selectedAI === provider.value}
                      onChange={(e) => setSelectedAI(e.target.value)}
                      className="sr-only"
                    />
                    <div className={`flex-shrink-0 w-4 h-4 rounded-full border-2 mt-1 mr-3 ${
                      selectedAI === provider.value
                        ? 'border-primary-500 bg-primary-500'
                        : 'border-secondary-300'
                    }`}>
                      {selectedAI === provider.value && (
                        <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                      )}
                    </div>
                    <div>
                      <h4 className="font-medium text-secondary-900">{provider.label}</h4>
                      <p className="text-sm text-secondary-600 mt-1">{provider.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Start Button */}
            <div className="text-center pt-4">
              <button
                onClick={() => setIsReady(true)}
                className="btn-primary text-lg px-8 py-3 flex items-center mx-auto"
              >
                <MessageCircle className="h-5 w-5 mr-2" />
                Start Brainstorming Session
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="card-clean">
        {/* Header */}
        <div className="card-header">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Lightbulb className="h-6 w-6 text-primary-600 mr-3" />
              <div>
                <h2 className="text-xl font-bold text-secondary-900">Brainstorming: {selectedField}</h2>
                <p className="text-secondary-600">Developing your thesis topic through conversation</p>
              </div>
            </div>
            <div className={`px-3 py-1 rounded-full border text-sm font-medium ${getTopicClarityColor()}`}>
              {getTopicClarityText()}
            </div>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="h-96 overflow-y-auto p-4 space-y-4 bg-secondary-50">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl p-4 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-secondary-900 border border-secondary-200'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.timestamp && (
                  <p className={`text-xs mt-2 ${
                    message.role === 'user' ? 'text-primary-100' : 'text-secondary-500'
                  }`}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white text-secondary-900 border border-secondary-200 p-4 rounded-lg flex items-center">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                <span>Thinking...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Topic Preview */}
        {suggestedTopic && topicClarity === 'high' && (
          <div className="border-t border-secondary-200 p-4 bg-success-50">
            <div className="flex items-start">
              <CheckCircle className="h-5 w-5 text-success-600 mr-3 mt-1" />
              <div className="flex-1">
                <h4 className="font-medium text-success-900 mb-1">Suggested Topic:</h4>
                <p className="text-success-800 font-medium">{suggestedTopic}</p>
                {suggestedDescription && (
                  <p className="text-success-700 text-sm mt-2">{suggestedDescription}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Message Input */}
        <div className="border-t border-secondary-200 p-4">
          <form onSubmit={handleSendMessage} className="flex gap-3">
            <input
              type="text"
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              placeholder="Share your thoughts, interests, or ask questions..."
              className="flex-1 form-input"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !currentMessage.trim()}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center p-4 border-t border-secondary-200 bg-secondary-50">
          {onBack && (
            <button
              onClick={onBack}
              className="btn-secondary"
              disabled={isLoading}
            >
              Back
            </button>
          )}
          
          <div className="flex gap-3">
            {topicClarity === 'high' && (
              <button
                onClick={handleFinalizeTopic}
                disabled={isLoading}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Finalizing...
                  </>
                ) : (
                  <>
                    Finalize Topic
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </button>
            )}
            
            {topicClarity !== 'high' && messages.length > 2 && (
              <button
                onClick={handleFinalizeTopic}
                disabled={isLoading}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Use Current Discussion
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 