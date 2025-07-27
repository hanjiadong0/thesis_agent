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
            ethics_score: response.ethics_score ,
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

  const renderToolResult = (result: any) => {
    if (!result) return null;

    const ToolCard = ({ icon, title, children, bgColor = "bg-blue-50", borderColor = "border-blue-200", iconColor = "text-blue-600" }: any) => (
      <div className={`mt-4 p-4 rounded-xl border-2 ${bgColor} ${borderColor} shadow-sm`}>
        <div className="flex items-center space-x-3 mb-3">
          <div className={`p-2 rounded-lg bg-white shadow-sm ${iconColor}`}>
            {icon}
          </div>
          <h4 className={`font-semibold ${iconColor.replace('text-', 'text-').replace('-600', '-800')}`}>{title}</h4>
        </div>
        {children}
      </div>
    );

    switch (result.tool) {
      case 'research_paper':
        return (
          <ToolCard 
            icon={<BookOpen className="h-5 w-5" />} 
            title="📚 Research Papers Found"
            bgColor="bg-indigo-50" 
            borderColor="border-indigo-200" 
            iconColor="text-indigo-600"
          >
            <div className="space-y-3">
              <p className="text-sm text-indigo-700">
                <strong>Found {result.papers_found || 0} relevant papers</strong>
              </p>
              {result.papers?.slice(0, 3).map((paper: any, index: number) => (
                <div key={index} className="bg-white p-4 rounded-lg border border-indigo-100 shadow-sm">
                  <h5 className="font-medium text-gray-900 mb-2 leading-snug">{paper.title}</h5>
                  <p className="text-xs text-gray-600 mb-2 font-mono">{paper.shortCitation}</p>
                  {paper.abstract && (
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {paper.abstract.substring(0, 250)}...
                    </p>
                  )}
                  {paper.url && (
                    <a href={paper.url} target="_blank" rel="noopener noreferrer" 
                       className="inline-flex items-center mt-2 text-indigo-600 hover:text-indigo-800 text-sm">
                      <ArrowLeft className="h-3 w-3 mr-1 rotate-180" />
                      View Paper
                    </a>
                  )}
                </div>
              ))}
            </div>
          </ToolCard>
        );
      
      case 'generate_citation':
        return (
          <ToolCard 
            icon={<FileText className="h-5 w-5" />} 
            title="📄 BibTeX Citation Generated"
            bgColor="bg-green-50" 
            borderColor="border-green-200" 
            iconColor="text-green-600"
          >
            <div className="bg-gray-900 p-4 rounded-lg overflow-x-auto">
              <pre className="text-green-400 text-sm font-mono whitespace-pre-wrap">
                {result.citation || "No citation generated"}
              </pre>
            </div>
            <button 
              onClick={() => navigator.clipboard?.writeText(result.citation)}
              className="mt-3 btn-secondary text-sm"
            >
              📋 Copy Citation
            </button>
          </ToolCard>
        );
      
      case 'ai_detection':
        const aiProb = result.ai_probability || 0;
        const isHighAI = aiProb > 0.7;
        return (
          <ToolCard 
            icon={<Search className="h-5 w-5" />} 
            title="🔍 AI Content Detection"
            bgColor={isHighAI ? "bg-red-50" : "bg-yellow-50"} 
            borderColor={isHighAI ? "border-red-200" : "border-yellow-200"} 
            iconColor={isHighAI ? "text-red-600" : "text-yellow-600"}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">AI Probability:</span>
                <span className={`font-bold text-lg ${isHighAI ? 'text-red-700' : 'text-yellow-700'}`}>
                  {(aiProb * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full transition-all duration-500 ${
                    isHighAI ? 'bg-red-500' : 'bg-yellow-500'
                  }`}
                  style={{ width: `${aiProb * 100}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">
                {result.explanation || "Analysis completed"}
              </p>
              {isHighAI && (
                <div className="bg-red-100 border border-red-200 rounded-lg p-3">
                  <p className="text-red-800 text-sm font-medium">
                    ⚠️ High probability of AI-generated content detected
                  </p>
                </div>
              )}
            </div>
          </ToolCard>
        );

      case 'grammar_check':
        const issues = result.analysis?.issues || [];
        return (
          <ToolCard 
            icon={<CheckCircle className="h-5 w-5" />} 
            title="✍️ Grammar & Style Analysis"
            bgColor="bg-purple-50" 
            borderColor="border-purple-200" 
            iconColor="text-purple-600"
          >
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white p-3 rounded-lg border border-purple-100">
                  <p className="text-sm text-gray-600">Issues Found</p>
                  <p className="text-xl font-bold text-purple-700">{issues.length}</p>
                </div>
                <div className="bg-white p-3 rounded-lg border border-purple-100">
                  <p className="text-sm text-gray-600">Readability</p>
                  <p className="text-lg font-semibold text-purple-700">
                    {result.analysis?.readability_score?.level || "Good"}
                  </p>
                </div>
              </div>
              {issues.length > 0 && (
                <div className="space-y-2">
                  <h5 className="font-medium text-purple-800">Top Issues:</h5>
                  {issues.slice(0, 3).map((issue: any, index: number) => (
                    <div key={index} className="bg-white p-3 rounded border border-purple-100">
                      <p className="text-sm text-purple-700">{issue.message || issue}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </ToolCard>
        );

      case 'web_search':
        const searchResults = result.search_results || result;
        return (
          <ToolCard 
            icon={<Search className="h-5 w-5" />} 
            title="🌐 Web Search Results"
            bgColor="bg-blue-50" 
            borderColor="border-blue-200" 
            iconColor="text-blue-600"
          >
            <div className="space-y-3">
              <p className="text-sm text-blue-700">
                <strong>Found {searchResults.results?.length || 0} results</strong>
              </p>
              {searchResults.summary && (
                <div className="bg-white p-4 rounded-lg border border-blue-100">
                  <h5 className="font-medium text-blue-800 mb-2">Summary:</h5>
                  <p className="text-sm text-gray-700 leading-relaxed">{searchResults.summary}</p>
                </div>
              )}
              {searchResults.results?.slice(0, 3).map((item: any, index: number) => (
                <div key={index} className="bg-white p-3 rounded-lg border border-blue-100">
                  <h6 className="font-medium text-gray-900 text-sm">{item.title}</h6>
                  <p className="text-xs text-gray-600 mt-1">{item.snippet}</p>
                  {item.url && (
                    <a href={item.url} target="_blank" rel="noopener noreferrer" 
                       className="inline-flex items-center mt-2 text-blue-600 hover:text-blue-800 text-xs">
                      <ArrowLeft className="h-3 w-3 mr-1 rotate-180" />
                      Visit Source
                    </a>
                  )}
                </div>
              ))}
            </div>
          </ToolCard>
        );

      case 'fact_check':
        const assessment = result.assessment || result.fact_check?.assessment || 'Unknown';
        const confidence = result.confidence || result.fact_check?.confidence || 'Low';
        const factSummary = result.summary || result.fact_check?.summary;
        const evidence = result.evidence || [];
        
        const isVerified = assessment.toLowerCase().includes('true') || assessment.toLowerCase().includes('accurate');
        const isDisputed = assessment.toLowerCase().includes('false') || assessment.toLowerCase().includes('inaccurate');
        
        return (
          <ToolCard 
            icon={<CheckCircle className="h-5 w-5" />} 
            title="🔍 Fact Check Results"
            bgColor={isVerified ? "bg-green-50" : isDisputed ? "bg-red-50" : "bg-orange-50"} 
            borderColor={isVerified ? "border-green-200" : isDisputed ? "border-red-200" : "border-orange-200"} 
            iconColor={isVerified ? "text-green-600" : isDisputed ? "text-red-600" : "text-orange-600"}
          >
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white p-3 rounded-lg border">
                  <p className="text-sm text-gray-600">Assessment</p>
                  <p className={`font-semibold ${
                    isVerified ? 'text-green-700' : isDisputed ? 'text-red-700' : 'text-orange-700'
                  }`}>
                    {assessment}
                  </p>
                </div>
                <div className="bg-white p-3 rounded-lg border">
                  <p className="text-sm text-gray-600">Confidence</p>
                  <p className="font-semibold text-gray-700">{confidence}</p>
                </div>
              </div>
              
              {factSummary && (
                <div className="bg-white p-4 rounded-lg border">
                  <h5 className="font-medium text-gray-800 mb-2">Analysis:</h5>
                  <p className="text-sm text-gray-700 leading-relaxed">{factSummary}</p>
                </div>
              )}
              
              {evidence.length > 0 && (
                <div className="bg-white p-4 rounded-lg border">
                  <h5 className="font-medium text-gray-800 mb-2">Sources found: {evidence.length}</h5>
                  <div className="space-y-2">
                    {evidence.slice(0, 2).map((source: any, index: number) => (
                      <div key={index} className="text-sm text-gray-600 border-l-2 border-gray-200 pl-3">
                        <p>{source.snippet || source.title || 'Source available'}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </ToolCard>
        );

      case 'wikipedia_search':
        const wikiResults = result.search_results || result;
        return (
          <ToolCard 
            icon={<BookOpen className="h-5 w-5" />} 
            title="📖 Wikipedia Search"
            bgColor="bg-indigo-50" 
            borderColor="border-indigo-200" 
            iconColor="text-indigo-600"
          >
            <div className="space-y-3">
              <p className="text-sm text-indigo-700">
                <strong>Found {wikiResults.total_found || 0} articles</strong>
              </p>
              {wikiResults.articles?.slice(0, 3).map((article: any, index: number) => (
                <div key={index} className="bg-white p-4 rounded-lg border border-indigo-100">
                  <h5 className="font-medium text-gray-900 mb-2">{article.title}</h5>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {article.summary?.substring(0, 200)}...
                  </p>
                  {article.url && (
                    <a href={article.url} target="_blank" rel="noopener noreferrer" 
                       className="inline-flex items-center mt-2 text-indigo-600 hover:text-indigo-800 text-sm">
                      <ArrowLeft className="h-3 w-3 mr-1 rotate-180" />
                      Read Article
                    </a>
                  )}
                </div>
              ))}
            </div>
          </ToolCard>
        );

      case 'solve_equation':
        const solution = result.solution || result;
        return (
          <ToolCard 
            icon={<Calculator className="h-5 w-5" />} 
            title="🧮 Equation Solution"
            bgColor="bg-emerald-50" 
            borderColor="border-emerald-200" 
            iconColor="text-emerald-600"
          >
            <div className="space-y-3">
              <div className="bg-white p-4 rounded-lg border border-emerald-100">
                <p className="text-sm text-gray-600 mb-2">Solution:</p>
                <p className="text-lg font-mono font-bold text-emerald-700">
                  {solution.solution || "No solution found"}
                </p>
              </div>
              <div className="bg-white p-3 rounded-lg border border-emerald-100">
                <p className="text-sm text-gray-600">Equation Type:</p>
                <p className="font-medium text-emerald-700">{solution.equation_type || "Unknown"}</p>
              </div>
              {solution.steps && solution.steps.length > 0 && (
                <div className="bg-white p-4 rounded-lg border border-emerald-100">
                  <h5 className="font-medium text-emerald-800 mb-2">Solution Steps:</h5>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                    {solution.steps.map((step: string, index: number) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </ToolCard>
        );

      case 'calculate':
        const calculation = result.calculation || result;
        const calcResult = calculation.result;
        return (
          <ToolCard 
            icon={<Calculator className="h-5 w-5" />} 
            title="🧮 Calculation Result"
            bgColor="bg-emerald-50" 
            borderColor="border-emerald-200" 
            iconColor="text-emerald-600"
          >
            <div className="space-y-3">
              <div className="bg-white p-4 rounded-lg border border-emerald-100">
                <p className="text-sm text-gray-600 mb-2">Expression:</p>
                <p className="font-mono text-gray-800">{calculation.expression || "Unknown"}</p>
              </div>
              <div className="bg-emerald-100 p-4 rounded-lg border border-emerald-200">
                <p className="text-sm text-emerald-700 mb-2">Result:</p>
                <p className="text-2xl font-mono font-bold text-emerald-800">
                  {calcResult !== null && calcResult !== undefined ? calcResult : "Error"}
                </p>
              </div>
              {calculation.error && (
                <div className="bg-red-50 p-3 rounded-lg border border-red-200">
                  <p className="text-red-700 text-sm">{calculation.error}</p>
                </div>
              )}
            </div>
          </ToolCard>
        );

      case 'pdf_summary':
        const pdfSummary = result.summary || result;
        return (
          <ToolCard 
            icon={<FileText className="h-5 w-5" />} 
            title="📄 PDF Summary"
            bgColor="bg-cyan-50" 
            borderColor="border-cyan-200" 
            iconColor="text-cyan-600"
          >
            <div className="space-y-3">
              <div className="bg-white p-4 rounded-lg border border-cyan-100">
                <h5 className="font-medium text-cyan-800 mb-2">Summary:</h5>
                <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                  {pdfSummary.content || pdfSummary.summary || "PDF processed successfully"}
                </div>
              </div>
              {pdfSummary.status && (
                <div className="bg-cyan-50 p-3 rounded-lg border border-cyan-200">
                  <p className="text-sm text-cyan-700">
                    <strong>Status:</strong> {pdfSummary.status}
                  </p>
                </div>
              )}
               {pdfSummary.metadata && (
                 <div className="grid grid-cols-2 gap-3">
                   <div className="bg-white p-3 rounded-lg border border-cyan-100">
                     <p className="text-sm text-gray-600">Pages</p>
                     <p className="font-semibold text-cyan-700">{pdfSummary.metadata.pages}</p>
                   </div>
                   <div className="bg-white p-3 rounded-lg border border-cyan-100">
                     <p className="text-sm text-gray-600">Word Count</p>
                     <p className="font-semibold text-cyan-700">{pdfSummary.metadata.word_count}</p>
                   </div>
                 </div>
               )}
            </div>
          </ToolCard>
        );
       
      default:
        return (
          <ToolCard 
            icon={<Settings className="h-5 w-5" />} 
            title="🔧 Tool Result"
            bgColor="bg-gray-50" 
            borderColor="border-gray-200" 
            iconColor="text-gray-600"
          >
            <div className="bg-white p-4 rounded-lg border border-gray-100">
              <p className="text-sm text-gray-700">
                {result.summary || result.result || "Tool executed successfully"}
              </p>
              {result.error && (
                <div className="mt-3 bg-red-50 p-3 rounded border border-red-200">
                  <p className="text-red-700 text-sm">{result.error}</p>
                </div>
              )}
            </div>
          </ToolCard>
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
                        message.ethics_score >= 0.8 
                          ? 'bg-green-100 text-green-700' 
                          : message.ethics_score >= 0.6 
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        Ethics: message.ethics_score}
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