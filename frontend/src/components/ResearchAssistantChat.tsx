import React, { useEffect, useRef, useState } from 'react';
import {
  ArrowLeft,
  Bot,
  ExternalLink,
  Loader2,
  Search,
  Send,
  Sparkles,
  Wrench
} from 'lucide-react';
import {
  AI_PROVIDERS,
  apiService,
  ChatMessage,
  ResearchAgentStatusResponse,
  ResearchAgentToolTrace
} from '../services/api';

interface ResearchAssistantChatProps {
  onBack?: () => void;
}

interface ResearchAssistantMessage extends ChatMessage {
  toolTrace?: ResearchAgentToolTrace[];
  conceptGraphImage?: string | null;
  error?: boolean;
}

const EXAMPLE_PROMPTS = [
  'Find recent arXiv papers on LLM evaluation for academic writing and summarize the best one for a medium-level reader.',
  'Explain retrieval-augmented generation for a beginner, then suggest three related Wikipedia topics to study next.',
  'Generate a concept graph for transformer architecture using Wikipedia as the source.'
];

export default function ResearchAssistantChat({ onBack }: ResearchAssistantChatProps) {
  const [messages, setMessages] = useState<ResearchAssistantMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedAI, setSelectedAI] = useState('ollama');
  const [status, setStatus] = useState<ResearchAgentStatusResponse | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const backendReady = Boolean(status?.available);
  const geminiAvailable = status?.providers?.gemini !== false;
  const selectedProviderUnavailable = selectedAI === 'gemini' && !geminiAvailable;

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const result = await apiService.getResearchAgentStatus();
        setStatus(result);
        if (!result.available) {
          setStatusError(result.error || 'Research assistant is currently unavailable.');
        }
      } catch (error: any) {
        console.error('Failed to load research agent status:', error);
        setStatusError('Could not connect to the research assistant backend.');
      }
    };

    loadStatus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (selectedAI === 'gemini' && !geminiAvailable) {
      setSelectedAI('ollama');
    }
  }, [geminiAvailable, selectedAI]);

  const sendMessage = async (messageText: string) => {
    const trimmed = messageText.trim();
    if (!trimmed || loading || !backendReady || selectedProviderUnavailable) return;

    const nextUserMessage: ResearchAssistantMessage = {
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString()
    };

    const nextHistory = [...messages, nextUserMessage];
    setMessages(nextHistory);
    setInput('');
    setLoading(true);

    try {
      const response = await apiService.researchAgentChat({
        message: trimmed,
        history: messages.map(({ role, content, timestamp }) => ({ role, content, timestamp })),
        ai_provider: selectedAI
      });

      const assistantMessage: ResearchAssistantMessage = {
        role: 'assistant',
        content: response.reply || 'The research assistant finished without returning text.',
        timestamp: new Date().toISOString(),
        toolTrace: response.tool_trace || [],
        conceptGraphImage: response.concept_graph_image
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Research agent chat failed:', error);
      const detail = error?.response?.data?.detail || 'The research assistant request failed.';
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: detail,
          timestamp: new Date().toISOString(),
          error: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await sendMessage(input);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="card-clean overflow-hidden">
        <div className="card-header bg-gradient-to-r from-blue-50 via-white to-emerald-50">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="flex items-start gap-4">
              {onBack && (
                <button onClick={onBack} className="btn-secondary px-4 py-2 flex items-center">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back
                </button>
              )}

              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-r from-blue-500 to-emerald-500 text-white flex items-center justify-center shadow-lg">
                    <Search className="h-6 w-6" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold text-secondary-900">Research Assistant</h1>
                    <p className="text-secondary-600">
                      Integrated deep research mode powered by the cloned `research_agent` repository.
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3 text-sm">
                  <span className={`px-3 py-1 rounded-full border ${status?.available ? 'bg-green-50 border-green-200 text-green-700' : 'bg-amber-50 border-amber-200 text-amber-700'}`}>
                    {status ? (status.available ? 'Backend Ready' : 'Backend Limited') : 'Checking Backend'}
                  </span>
                  <span className={`px-3 py-1 rounded-full border ${status?.search_configured ? 'bg-blue-50 border-blue-200 text-blue-700' : 'bg-slate-50 border-slate-200 text-slate-600'}`}>
                    {status?.search_configured ? 'Google Search Configured' : 'Google Search Limited'}
                  </span>
                  <span className="px-3 py-1 rounded-full border bg-slate-50 border-slate-200 text-slate-600">
                    arXiv + Wikipedia + Summaries + Concept Graphs
                  </span>
                </div>
              </div>
            </div>

            <div className="lg:max-w-sm w-full">
              <p className="text-sm font-medium text-secondary-900 mb-3">Choose your research model</p>
              <div className="space-y-3">
                {AI_PROVIDERS.map((provider) => {
                  const isProviderUnavailable = provider.value === 'gemini' && !geminiAvailable;

                  return (
                  <label
                    key={provider.value}
                    className={`flex items-start p-3 border rounded-xl cursor-pointer transition-colors ${
                      selectedAI === provider.value
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-secondary-200 hover:border-secondary-300 bg-white'
                    } ${isProviderUnavailable ? 'opacity-60 cursor-not-allowed' : ''}`}
                  >
                    <input
                      type="radio"
                      className="sr-only"
                      checked={selectedAI === provider.value}
                      disabled={isProviderUnavailable}
                      onChange={() => setSelectedAI(provider.value)}
                    />
                    <div className="pt-1 pr-3">
                      <div className={`w-4 h-4 rounded-full border-2 ${selectedAI === provider.value ? 'border-primary-500 bg-primary-500' : 'border-secondary-300'}`}>
                        {selectedAI === provider.value && <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5" />}
                      </div>
                    </div>
                    <div>
                      <p className="font-medium text-secondary-900">{provider.label}</p>
                      <p className="text-sm text-secondary-600 mt-1">
                        {isProviderUnavailable ? 'Gemini is disabled until a valid GEMINI_API_KEY is configured.' : provider.description}
                      </p>
                    </div>
                  </label>
                  );
                })}
              </div>
            </div>
          </div>

          {statusError && (
            <div className="mt-6 notification-warning">
              <p className="font-medium">Research assistant status</p>
              <p className="text-sm mt-1">{statusError}</p>
            </div>
          )}
        </div>

        <div className="p-6 border-b border-secondary-200 bg-secondary-50">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-4 w-4 text-blue-600" />
            <p className="text-sm font-medium text-secondary-900">Try one of these prompts</p>
          </div>
          <div className="grid gap-3 lg:grid-cols-3">
            {EXAMPLE_PROMPTS.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => sendMessage(example)}
                disabled={loading || !backendReady}
                className="text-left p-4 rounded-xl border border-secondary-200 bg-white hover:border-primary-300 hover:bg-primary-50 transition-colors disabled:opacity-50"
              >
                <p className="text-sm text-secondary-800">{example}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="h-[520px] overflow-y-auto p-6 space-y-6 bg-white">
          {messages.length === 0 && (
            <div className="card-glass bg-gradient-to-r from-blue-50 to-emerald-50 border border-blue-100 p-8 text-center">
              <Bot className="h-10 w-10 mx-auto text-blue-600 mb-3" />
              <h2 className="text-xl font-semibold text-secondary-900 mb-2">Ready for literature search and explanation</h2>
              <p className="text-secondary-600 max-w-2xl mx-auto">
                Ask for arXiv papers, Wikipedia context, summaries, query refinement, or a concept graph.
                The assistant can chain tools together and return a final answer in one turn.
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={`${message.role}-${index}-${message.timestamp || ''}`} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-4xl rounded-2xl p-5 shadow-md ${
                message.role === 'user'
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                  : message.error
                    ? 'bg-red-50 border border-red-200 text-red-800'
                    : 'bg-white border border-secondary-200 text-secondary-900'
              }`}>
                <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>

                {message.toolTrace && message.toolTrace.length > 0 && (
                  <div className="mt-5 pt-4 border-t border-secondary-200">
                    <div className="flex items-center gap-2 mb-3">
                      <Wrench className="h-4 w-4 text-blue-600" />
                      <p className="text-sm font-medium">Tools used in this answer</p>
                    </div>
                    <div className="space-y-3">
                      {message.toolTrace.map((tool, toolIndex) => (
                        <div key={`${tool.name}-${toolIndex}`} className="rounded-xl border border-secondary-200 bg-secondary-50 p-3">
                          <div className="flex items-center justify-between gap-3 mb-2">
                            <span className="font-medium text-secondary-900">{tool.name}</span>
                            <span className="text-xs text-secondary-500">
                              {Object.keys(tool.args || {}).length > 0 ? JSON.stringify(tool.args) : 'no args'}
                            </span>
                          </div>
                          <p className="text-sm text-secondary-700 whitespace-pre-wrap line-clamp-6">{tool.output}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {message.conceptGraphImage && (
                  <div className="mt-5 pt-4 border-t border-secondary-200">
                    <div className="flex items-center gap-2 mb-3">
                      <ExternalLink className="h-4 w-4 text-emerald-600" />
                      <p className="text-sm font-medium">Concept graph</p>
                    </div>
                    <img
                      src={`data:image/png;base64,${message.conceptGraphImage}`}
                      alt="Generated concept graph"
                      className="rounded-xl border border-secondary-200 shadow-sm bg-white"
                    />
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-secondary-50 border border-secondary-200 rounded-2xl p-4 flex items-center gap-3 text-secondary-700">
                <Loader2 className="h-4 w-4 animate-spin" />
                Research assistant is working through the next step...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="p-6 border-t border-secondary-200 bg-white">
          <form onSubmit={handleSubmit} className="flex gap-4">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask for papers, summaries, explanations, or a concept graph..."
              rows={3}
              disabled={loading || !backendReady || selectedProviderUnavailable}
              className="input-modern resize-none flex-1"
            />
            <button
              type="submit"
              disabled={loading || !input.trim() || !backendReady || selectedProviderUnavailable}
              className="btn-primary self-end disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
