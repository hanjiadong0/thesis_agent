import React, { useState, useEffect, useRef } from 'react';
import { Send, ArrowLeft, AlertTriangle, CheckCircle, Settings, FileText, Search, Download, Image, Calculator, Upload, Clock, Calendar, BookOpen, User } from 'lucide-react';
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
  const [deliverable, setDeliverable] = useState('');
  const [showDeliverableModal, setShowDeliverableModal] = useState(false);
  const [ethicsAlerts, setEthicsAlerts] = useState<number>(0);
  const [isTyping, setIsTyping] = useState(false);
  
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
    if (!deliverable.trim()) return;

    try {
      setIsLoading(true);
      const response = await apiService.completeTask({
        task_id: taskId,
        deliverable: deliverable
      });

      if (response.success) {
        onComplete(deliverable);
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

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      if (selectedTool) {
        await handleToolExecution(selectedTool, inputMessage);
      } else {
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
      setSelectedTool('');
      setUploadedFile(null);
    }
  };

  const clearSelectedTool = () => {
    setSelectedTool('');
    setUploadedFile(null);
  };

  const handleCompleteTask = async () => {
    if (!deliverable.trim()) return;
    setIsLoading(true);
    try {
      const response = await apiService.completeTask({
        task_id: taskId,
        deliverable: deliverable
      });
      if (response.success) {
        onComplete(deliverable);
      }
    } catch (error) {
      console.error('Failed to complete task:', error);
    } finally {
      setIsLoading(false);
      setShowTaskComplete(false);
    }
  };

  const renderToolResult = (result: any) => {
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

  const [showTaskComplete, setShowTaskComplete] = useState(false);

  const handleToolUse = (toolName: string) => {
    setSelectedTool(toolName);
    setShowTools(false);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="card-modern border-b-0 rounded-b-none p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <button
              onClick={onBack}
              className="flex items-center text-gray-600 hover:text-blue-600 transition-all duration-200 
                         hover:bg-blue-50 px-3 py-2 rounded-lg group"
            >
              <ArrowLeft className="h-5 w-5 mr-2 group-hover:-translate-x-1 transition-transform duration-200" />
              <span className="font-medium">Back to Timeline</span>
            </button>
            <div className="border-l border-gray-200 pl-6">
              <h1 className="text-2xl font-bold text-gradient mb-1">{task.title}</h1>
              <p className="text-gray-600 text-sm leading-relaxed">{task.description}</p>
              <div className="flex items-center space-x-4 mt-2">
                <span className="badge-modern">
                  <Clock className="h-3 w-3 mr-1" />
                  {task.estimated_hours}h estimated
                </span>
                                 <span className="badge-modern">
                   <Calendar className="h-3 w-3 mr-1" />
                   Due: {new Date(task.due_date).toLocaleDateString()}
                 </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {ethicsAlerts > 0 && (
              <div className="flex items-center text-amber-600 bg-amber-50 px-3 py-2 rounded-lg border border-amber-200">
                <AlertTriangle className="h-5 w-5 mr-2" />
                <span className="text-sm font-medium">{ethicsAlerts} ethics alerts</span>
              </div>
            )}
            
            <button
              onClick={() => setShowTools(!showTools)}
              className={`btn-secondary transition-all duration-200 ${showTools ? 'bg-blue-50 border-blue-300' : ''}`}
            >
              <Settings className="h-4 w-4 mr-2" />
              {showTools ? 'Hide Tools' : 'Show Tools'}
            </button>
            
            <button
              onClick={() => setShowTaskComplete(true)}
              disabled={!deliverable.trim()}
              className="btn-success disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Complete Task
            </button>
          </div>
        </div>
      </div>

      {/* Tools Panel */}
      {showTools && (
        <div className="card-modern border-t-0 border-b-0 rounded-none p-6 bg-gradient-to-r from-blue-50 to-purple-50">
          <h3 className="text-lg font-semibold text-gradient mb-4 flex items-center">
            <Search className="h-5 w-5 mr-2" />
            Available Research Tools
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {availableTools.map((tool) => {
              const IconComponent = getToolIcon(tool.name);
              return (
                <div 
                  key={tool.name} 
                  className="card-glass p-4 hover:bg-white/30 cursor-pointer transition-all duration-300 
                             border-white/30 hover:border-white/50 group"
                  onClick={() => handleToolUse(tool.name)}
                >
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="p-2 bg-white/50 rounded-lg group-hover:bg-white/70 transition-colors duration-200">
                      <IconComponent className="h-5 w-5 text-blue-600" />
                    </div>
                    <span className="font-medium text-gray-800">{tool.title}</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2 line-clamp-2">{tool.description}</p>
                  <p className="text-xs text-blue-600 italic font-medium">{tool.example}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* File Upload Section */}
      {(selectedTool === 'pdf_summary' || selectedTool === 'ai_detection') && (
        <div className="card-modern border-t-0 border-b-0 rounded-none px-6 py-4 bg-gradient-to-r from-orange-50 to-yellow-50">
          <div className="flex items-center space-x-4">
            <Upload className="h-5 w-5 text-orange-600" />
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload File (Optional)
              </label>
              <input
                type="file"
                accept=".pdf,.txt,.doc,.docx"
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 
                           file:rounded-lg file:border-0 file:text-sm file:font-medium
                           file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100
                           file:transition-colors file:duration-200"
                onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
              />
            </div>
          </div>
          
          {uploadedFile && (
            <div className="mt-3 p-3 bg-white/70 rounded-lg border border-orange-200">
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-orange-600" />
                <span className="text-sm font-medium text-gray-700">File selected: {uploadedFile.name}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-transparent to-blue-50/30">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="card-glass p-8 max-w-md mx-auto">
              <div className="animate-float mb-4">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full 
                                flex items-center justify-center mx-auto">
                  <BookOpen className="h-8 w-8 text-white" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gradient mb-2">Ready to Get Started!</h3>
              <p className="text-gray-600 text-sm">
                Welcome to your focused work session for <strong>{task.title}</strong>. 
                Ask questions, use research tools, or start working on your deliverable.
              </p>
            </div>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
          >
            <div
              className={`max-w-3xl rounded-2xl p-4 shadow-lg ${
                message.type === 'user'
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                  : message.type === 'system'
                  ? 'bg-gradient-to-r from-orange-100 to-yellow-100 text-orange-800 border border-orange-200'
                  : 'card-modern text-gray-800'
              }`}
            >
              <div className="flex items-start space-x-3">
                {message.type !== 'user' && (
                  <div className={`p-2 rounded-lg ${
                    message.type === 'system' 
                      ? 'bg-orange-200/50' 
                      : 'bg-blue-100'
                  }`}>
                    {message.type === 'system' ? (
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                    ) : (
                      <User className="h-4 w-4 text-blue-600" />
                    )}
                  </div>
                )}
                
                <div className="flex-1 min-w-0">
                                     <div className="prose prose-sm max-w-none">
                     <div className="whitespace-pre-wrap">{message.content}</div>
                   </div>
                   
                   {message.tool_result && renderToolResult(message.tool_result)}
                   
                   <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/20">
                     <span className="text-xs opacity-75">
                       {message.timestamp.toLocaleTimeString()}
                     </span>
                    {message.ethics_score !== undefined && (
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        message.ethics_score >= 8 
                          ? 'bg-green-100 text-green-700' 
                          : message.ethics_score >= 6 
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        Ethics: {message.ethics_score}/10
                      </span>
                    )}
                  </div>
                  
                  {message.intervention?.needed && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="h-4 w-4 text-red-600" />
                        <span className="text-sm font-medium text-red-800">Ethics Intervention</span>
                      </div>
                      <p className="text-sm text-red-700 mt-1">{message.intervention.message}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start animate-fade-in-up">
            <div className="card-modern p-4 max-w-xs">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
                <span className="text-sm text-gray-500">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="card-modern border-t-0 rounded-t-none p-6 bg-white/95 backdrop-blur-sm">
        <form onSubmit={handleSendMessage} className="space-y-4">
          <div className="flex space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask a question, request research help, or describe your progress..."
                className="input-modern min-h-[80px] resize-none"
                rows={3}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(e);
                  }
                }}
              />
            </div>
            <div className="flex flex-col space-y-2">
              <button
                type="submit"
                disabled={!inputMessage.trim() || isLoading}
                className="btn-primary h-fit px-4 py-3 disabled:opacity-50 disabled:cursor-not-allowed
                           disabled:transform-none"
              >
                <Send className="h-4 w-4" />
              </button>
              {selectedTool && (
                <button
                  type="button"
                  onClick={clearSelectedTool}
                  className="btn-secondary h-fit px-4 py-3 text-xs"
                  title="Clear selected tool"
                >
                  Clear Tool
                </button>
              )}
            </div>
          </div>
          
          {selectedTool && (
            <div className="p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
              <div className="flex items-center space-x-2">
                <div className="p-1 bg-blue-100 rounded">
                  {React.createElement(getToolIcon(selectedTool), { className: "h-3 w-3 text-blue-600" })}
                </div>
                <span className="text-sm font-medium text-blue-800">
                  {availableTools.find(t => t.name === selectedTool)?.title} tool selected
                </span>
              </div>
            </div>
          )}
        </form>

        {/* Deliverable Section */}
        <div className="mt-6 border-t pt-6">
          <label className="block text-sm font-semibold text-gradient mb-3">
            📝 Task Deliverable
          </label>
          <textarea
            value={deliverable}
            onChange={(e) => setDeliverable(e.target.value)}
            placeholder="Document your progress, findings, or final deliverable here..."
            className="input-modern min-h-[100px] resize-none"
            rows={4}
          />
          <p className="text-xs text-gray-500 mt-2">
            This will be saved as your task completion deliverable
          </p>
        </div>
      </div>

      {/* Task Completion Modal */}
      {showTaskComplete && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="card-modern max-w-md w-full p-6 animate-fade-in-up">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full 
                              flex items-center justify-center mx-auto mb-4 animate-pulse-glow">
                <CheckCircle className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gradient mb-2">Complete Task</h3>
              <p className="text-gray-600">
                Are you ready to mark <strong>{task.title}</strong> as complete?
              </p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Final Deliverable
                </label>
                <textarea
                  value={deliverable}
                  onChange={(e) => setDeliverable(e.target.value)}
                  placeholder="Summarize what you've accomplished..."
                  className="input-modern min-h-[100px] resize-none"
                  rows={4}
                />
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowTaskComplete(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCompleteTask}
                  disabled={!deliverable.trim()}
                  className="btn-success flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Complete Task
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