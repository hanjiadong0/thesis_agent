import React, { useState, useEffect, useRef } from 'react';
import { Send, ArrowLeft, AlertTriangle, CheckCircle, Settings, FileText, Search, Download, Image, Calculator, Upload } from 'lucide-react';
import { apiService } from '../services/api';

interface TaskChatProps {
  task: {
    title: string;
    description: string;
    estimated_hours: number;
    priority: number;
    due_date: string;
    deliverable?: string;
    focus_sessions?: number;
  };
  onBack: () => void;
  onComplete: (deliverable: string) => void;
  currentProjectId?: number;
  userName?: string;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'ai' | 'system' | 'tool';
  content: string;
  timestamp: Date;
  ethics_score?: number;
  tool_result?: any;
  intervention?: {
    needed: boolean;
    message: string;
  };
}

interface AvailableTool {
  name: string;
  title: string;
  description: string;
  params: string[];
  example: string;
}

const TaskChat: React.FC<TaskChatProps> = ({ 
  task, 
  onBack, 
  onComplete,
  currentProjectId,
  userName = "Student"
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [availableTools, setAvailableTools] = useState<AvailableTool[]>([]);
  const [showTools, setShowTools] = useState(false);
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [deliverableText, setDeliverableText] = useState('');
  const [showDeliverableModal, setShowDeliverableModal] = useState(false);
  const [ethicsAlerts, setEthicsAlerts] = useState<number>(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [taskId] = useState(`task_${currentProjectId}_${Date.now()}`);

  useEffect(() => {
    startTaskSession();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const startTaskSession = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.startTaskSession({
        task_id: taskId,
        user_id: `user_${currentProjectId}`,
        task_info: {
          title: task.title,
          description: task.description,
          deliverable: task.deliverable,
          estimated_hours: task.estimated_hours,
          due_date: task.due_date,
          focus_sessions: task.focus_sessions
        }
      });

      if (response.success) {
        setSessionId(response.session_id);
        setAvailableTools(response.available_tools || []);
        
        // Add welcome message
        const welcomeMessage: ChatMessage = {
          id: 'welcome',
          type: 'system',
          content: response.welcome_message,
          timestamp: new Date()
        };
        setMessages([welcomeMessage]);
      }
    } catch (error) {
      console.error('Failed to start task session:', error);
      const errorMessage: ChatMessage = {
        id: 'error',
        type: 'system',
        content: 'Failed to start task session. Please try again.',
        timestamp: new Date()
      };
      setMessages([errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    let messageContent = inputMessage;
    if (selectedTool) {
      messageContent = `[Using ${getToolDisplayName(selectedTool)}] ${inputMessage}`;
    }

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: messageContent,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // If a specific tool is selected, use that tool
      if (selectedTool) {
        await handleToolExecution(selectedTool, inputMessage);
      } else {
        // Regular AI chat
        const response = await apiService.sendTaskMessage({
          task_id: taskId,
          message: inputMessage
        });

        if (response.success) {
          const aiMessage: ChatMessage = {
            id: `ai_${Date.now()}`,
            type: 'ai',
            content: response.ai_response,
            timestamp: new Date(),
            ethics_score: response.ethics_score,
            tool_result: response.tool_result,
            intervention: response.intervention
          };

          setMessages(prev => [...prev, aiMessage]);

          // Track ethics alerts
          if (response.intervention?.needed) {
            setEthicsAlerts(prev => prev + 1);
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        type: 'system',
        content: 'Failed to send message. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setSelectedTool(''); // Reset tool selection
      setUploadedFile(null); // Reset file upload
    }
  };

  const getToolDisplayName = (toolName: string): string => {
    const tool = availableTools.find(t => t.name === toolName);
    return tool?.title || toolName;
  };

  const handleToolExecution = async (toolName: string, userInput: string) => {
    try {
      let toolParams: any = {};
      
      // Handle file upload first if needed
      if (uploadedFile && (toolName === 'pdf_summary' || toolName === 'ai_detection')) {
        const uploadResponse = await apiService.uploadFile(uploadedFile);
        if (!uploadResponse.success) {
          throw new Error('Failed to upload file');
        }
        toolParams.file_path = uploadResponse.file_path;
        toolParams.filename = uploadResponse.filename;
      }
      
      // Prepare tool parameters based on tool type
      switch (toolName) {
        case 'pdf_summary':
          if (uploadedFile) {
            toolParams.max_chunks = 5;
          } else {
            toolParams = { text: userInput };
          }
          break;
        case 'grammar_check':
          if (uploadedFile) {
            // For uploaded files, we'll extract text content
            toolParams.text = `File: ${uploadedFile.name}`;
          } else {
            toolParams.text = userInput;
          }
          break;
        case 'ai_detection':
          if (uploadedFile) {
            toolParams.text = `File: ${uploadedFile.name}`;
          } else {
            toolParams.text = userInput;
          }
          break;
        case 'web_search':
          toolParams = { query: userInput };
          break;
        case 'wikipedia_search':
          toolParams = { query: userInput };
          break;
        case 'solve_equation':
        case 'calculate':
          toolParams = { expression: userInput };
          break;
        default:
          toolParams = { query: userInput, text: userInput };
      }

      const response = await apiService.useTaskTool({
        task_id: taskId,
        tool_name: toolName,
        tool_params: toolParams
      });

      const toolMessage: ChatMessage = {
        id: `tool_${Date.now()}`,
        type: 'tool',
        content: `🔧 **${getToolDisplayName(toolName)}**: ${response.summary || response.result || 'Tool executed successfully'}`,
        timestamp: new Date(),
        tool_result: response
      };

      setMessages(prev => [...prev, toolMessage]);
    } catch (error) {
      console.error(`Failed to use tool ${toolName}:`, error);
      const errorMessage: ChatMessage = {
        id: `tool_error_${Date.now()}`,
        type: 'system',
        content: `❌ Failed to use ${getToolDisplayName(toolName)}. Please try again.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const useTool = async (toolName: string, toolParams: any) => {
    setIsLoading(true);
    
    try {
      const response = await apiService.useTaskTool({
        task_id: taskId,
        tool_name: toolName,
        tool_params: toolParams
      });

      const toolMessage: ChatMessage = {
        id: `tool_${Date.now()}`,
        type: 'tool',
        content: response.summary || `Tool ${toolName} executed`,
        timestamp: new Date(),
        tool_result: response
      };

      setMessages(prev => [...prev, toolMessage]);
    } catch (error) {
      console.error('Failed to use tool:', error);
      const errorMessage: ChatMessage = {
        id: `tool_error_${Date.now()}`,
        type: 'system',
        content: `Failed to use tool ${toolName}. Please try again.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const completeTask = async () => {
    if (!deliverableText.trim()) return;

    try {
      setIsLoading(true);
      const response = await apiService.completeTask({
        task_id: taskId,
        deliverable: deliverableText
      });

      if (response.success) {
        onComplete(deliverableText);
      }
    } catch (error) {
      console.error('Failed to complete task:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      // Original tools
      case 'research_paper': return Search;
      case 'generate_citation': return FileText;
      case 'ai_detection': return AlertTriangle;
      case 'pdf_summary': return Download;
      case 'image_to_latex': return Calculator;
      
      // Writing tools
      case 'grammar_check': return FileText;
      
      // Web research tools
      case 'web_search': return Search;
      case 'fact_check': return AlertTriangle;
      case 'source_verify': return CheckCircle;
      
      // Wikipedia tools
      case 'wikipedia_search': return Search;
      case 'wikipedia_summary': return FileText;
      case 'topic_overview': return FileText;
      
      // Survey tools
      case 'survey_questions': return FileText;
      case 'data_collection_plan': return Settings;
      
      // Math tools
      case 'solve_equation': return Calculator;
      case 'calculate': return Calculator;
      case 'convert_units': return Calculator;
      case 'statistics': return Calculator;
      
      default: return Settings;
    }
  };

  const getEthicsColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatToolResult = (result: any) => {
    if (!result) return null;

    switch (result.tool) {
      case 'research_paper':
        return (
          <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-900">📚 Found {result.papers_found} papers:</h4>
            {result.papers?.slice(0, 3).map((paper: any, index: number) => (
              <div key={index} className="mt-2 p-2 bg-white rounded border">
                <h5 className="font-medium text-sm">{paper.title}</h5>
                <p className="text-xs text-gray-600">{paper.shortCitation}</p>
                {paper.abstract && (
                  <p className="text-xs text-gray-700 mt-1">{paper.abstract.substring(0, 200)}...</p>
                )}
              </div>
            ))}
          </div>
        );
      
      case 'generate_citation':
        return (
          <div className="mt-2 p-3 bg-green-50 rounded-lg border border-green-200">
            <h4 className="font-semibold text-green-900">📄 BibTeX Citation:</h4>
            <pre className="text-xs bg-white p-2 rounded border mt-2 overflow-x-auto">
              {result.citation}
            </pre>
          </div>
        );
      
      case 'ai_detection':
        return (
          <div className="mt-2 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <h4 className="font-semibold text-yellow-900">🔍 AI Detection Results:</h4>
            <p className="text-sm">
              AI Probability: <span className="font-medium">{(result.ai_probability * 100).toFixed(1)}%</span>
            </p>
            <p className="text-xs text-gray-600">{result.explanation}</p>
          </div>
        );

      case 'grammar_check':
        return (
          <div className="mt-2 p-3 bg-purple-50 rounded-lg border border-purple-200">
            <h4 className="font-semibold text-purple-900">✍️ Grammar & Style Analysis:</h4>
            <p className="text-sm">Issues found: {result.analysis?.issues?.length || 0}</p>
            <p className="text-xs">Readability: {result.analysis?.readability_score?.level}</p>
            <p className="text-xs">Academic tone: {result.analysis?.academic_tone_score?.level}</p>
          </div>
        );

      case 'web_search':
        return (
          <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-900">🌐 Web Search Results:</h4>
            <p className="text-sm">{result.search_results?.results?.length || 0} results found</p>
            {result.search_results?.summary && (
              <p className="text-xs text-gray-600 mt-1">{result.search_results.summary}</p>
            )}
          </div>
        );

      case 'fact_check':
        return (
          <div className="mt-2 p-3 bg-orange-50 rounded-lg border border-orange-200">
            <h4 className="font-semibold text-orange-900">🔍 Fact Check Result:</h4>
            <p className="text-sm">Assessment: <span className="font-medium">{result.assessment || result.fact_check?.assessment || 'Unknown'}</span></p>
            <p className="text-xs text-orange-700">Confidence: {result.confidence || result.fact_check?.confidence || 'Low'}</p>
            {(result.summary || result.fact_check?.summary) && (
              <p className="text-sm mt-2 text-orange-800">{result.summary || result.fact_check?.summary}</p>
            )}
            {result.evidence && result.evidence.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-medium text-orange-700">Sources found: {result.evidence.length}</p>
              </div>
            )}
          </div>
        );

      case 'wikipedia_search':
        return (
          <div className="mt-2 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
            <h4 className="font-semibold text-indigo-900">📖 Wikipedia Search:</h4>
            <p className="text-sm">{result.search_results?.total_found || 0} articles found</p>
          </div>
        );

      case 'solve_equation':
        return (
          <div className="mt-2 p-3 bg-green-50 rounded-lg border border-green-200">
            <h4 className="font-semibold text-green-900">🧮 Equation Solution:</h4>
            <p className="text-sm">Solution: <span className="font-medium">{result.solution?.solution}</span></p>
            <p className="text-xs">Type: {result.solution?.equation_type}</p>
          </div>
        );

      case 'calculate':
        return (
          <div className="mt-2 p-3 bg-green-50 rounded-lg border border-green-200">
            <h4 className="font-semibold text-green-900">🧮 Calculation Result:</h4>
            <p className="text-sm">Result: <span className="font-medium">{result.calculation?.result}</span></p>
          </div>
        );

      case 'convert_units':
        return (
          <div className="mt-2 p-3 bg-cyan-50 rounded-lg border border-cyan-200">
            <h4 className="font-semibold text-cyan-900">🔄 Unit Conversion:</h4>
            <p className="text-sm">{result.conversion?.conversion_string}</p>
          </div>
        );

      case 'statistics':
        return (
          <div className="mt-2 p-3 bg-teal-50 rounded-lg border border-teal-200">
            <h4 className="font-semibold text-teal-900">📊 Statistics:</h4>
            <p className="text-sm">Data points: {result.statistics?.data_count}</p>
            {result.statistics?.statistics?.mean && (
              <p className="text-xs">Mean: {result.statistics.statistics.mean.toFixed(2)}</p>
            )}
          </div>
        );
      
      default:
        return (
          <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <h4 className="font-semibold text-gray-900">🔧 Tool Result:</h4>
            <p className="text-sm">{result.summary}</p>
          </div>
        );
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBack}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="h-5 w-5 mr-1" />
              Back to Timeline
            </button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">{task.title}</h1>
              <p className="text-sm text-gray-600">{task.description}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {ethicsAlerts > 0 && (
              <div className="flex items-center text-amber-600">
                <AlertTriangle className="h-5 w-5 mr-1" />
                <span className="text-sm">{ethicsAlerts} ethics alerts</span>
              </div>
            )}
            
            <button
              onClick={() => setShowTools(!showTools)}
              className="btn-secondary flex items-center space-x-2"
            >
              <Settings className="h-4 w-4" />
              <span>Tools ({availableTools.length})</span>
            </button>
            
            <button
              onClick={() => setShowDeliverableModal(true)}
              className="btn-primary flex items-center space-x-2"
            >
              <CheckCircle className="h-4 w-4" />
              <span>Complete Task</span>
            </button>
          </div>
        </div>
      </div>

      {/* Tools Panel */}
      {showTools && (
        <div className="bg-white border-b border-gray-200 p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Available Tools</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {availableTools.map((tool) => {
              const IconComponent = getToolIcon(tool.name);
              return (
                <div key={tool.name} className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="flex items-center space-x-2 mb-2">
                    <IconComponent className="h-4 w-4 text-blue-600" />
                    <span className="font-medium text-sm">{tool.title}</span>
                  </div>
                  <p className="text-xs text-gray-600 mb-2">{tool.description}</p>
                  <p className="text-xs text-blue-600 italic">{tool.example}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-lg p-4 ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.type === 'system'
                  ? 'bg-gray-100 text-gray-800'
                  : message.type === 'tool'
                  ? 'bg-purple-50 text-purple-900 border border-purple-200'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
              
              {/* Ethics Score */}
              {message.ethics_score !== undefined && (
                <div className={`text-xs mt-2 ${getEthicsColor(message.ethics_score)}`}>
                  Ethics Score: {(message.ethics_score * 100).toFixed(0)}%
                </div>
              )}
              
              {/* Intervention Alert */}
              {message.intervention?.needed && (
                <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded">
                  <div className="flex items-center text-amber-800">
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    <span className="font-medium">Academic Integrity Reminder</span>
                  </div>
                  <p className="text-sm text-amber-700 mt-1">{message.intervention.message}</p>
                </div>
              )}
              
              {/* Tool Results */}
              {formatToolResult(message.tool_result)}
              
              <div className="text-xs opacity-70 mt-2">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg p-4 max-w-xs">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-gray-600">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-4">
        {/* Tool Selection and File Upload Row */}
        <div className="flex space-x-4 mb-3">
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Select Tool (Optional)
            </label>
            <select
              value={selectedTool}
              onChange={(e) => setSelectedTool(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">💬 General Chat (AI Assistant)</option>
              {availableTools.map((tool) => (
                <option key={tool.name} value={tool.name}>
                  {getToolIcon(tool.name) && '🔧'} {tool.title}
                </option>
              ))}
            </select>
          </div>
          
          {(selectedTool === 'pdf_summary' || selectedTool === 'ai_detection') && (
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Upload File (Optional)
              </label>
              <input
                type="file"
                accept={selectedTool === 'pdf_summary' ? '.pdf' : '.txt,.doc,.docx,.pdf'}
                onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          )}
        </div>

        {/* Selected Tool Info */}
        {selectedTool && (
          <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center space-x-2">
              {React.createElement(getToolIcon(selectedTool), { className: "h-4 w-4 text-blue-600" })}
              <span className="text-sm font-medium text-blue-900">
                Using: {getToolDisplayName(selectedTool)}
              </span>
            </div>
            <p className="text-xs text-blue-700 mt-1">
              {availableTools.find(t => t.name === selectedTool)?.description}
            </p>
          </div>
        )}

        {/* Message Input Row */}
        <div className="flex space-x-4">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              selectedTool 
                ? `Enter your ${selectedTool === 'web_search' ? 'search query' : selectedTool === 'grammar_check' ? 'text to check' : 'input'} for ${getToolDisplayName(selectedTool)}...`
                : "Ask for help, request research, or use tools to work on your task..."
            }
            className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="btn-primary flex items-center space-x-2 px-6"
          >
            <Send className="h-4 w-4" />
            <span>{selectedTool ? 'Use Tool' : 'Send'}</span>
          </button>
        </div>

        {/* File Upload Status */}
        {uploadedFile && (
          <div className="mt-2 text-xs text-green-600">
            📎 File selected: {uploadedFile.name}
          </div>
        )}
      </div>

      {/* Deliverable Modal */}
      {showDeliverableModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Complete Task</h2>
              <p className="text-gray-600 mb-4">
                Please provide your final deliverable for this task. This will be saved and you can revisit it later.
              </p>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Deliverable Content
                </label>
                <textarea
                  value={deliverableText}
                  onChange={(e) => setDeliverableText(e.target.value)}
                  placeholder="Enter your completed work, analysis, or findings for this task..."
                  className="w-full h-64 border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div className="flex justify-end space-x-4">
                <button
                  onClick={() => setShowDeliverableModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={completeTask}
                  disabled={!deliverableText.trim() || isLoading}
                  className="btn-primary"
                >
                  {isLoading ? 'Completing...' : 'Complete Task'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskChat; 