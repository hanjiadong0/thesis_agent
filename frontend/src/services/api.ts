import axios from 'axios';

// Types for API responses
export interface UserQuestionnaireData {
  name: string;
  email: string;
  thesis_topic: string;
  thesis_field: string;
  thesis_deadline: string;
  thesis_description: string;
  daily_hours_available: number;
  preferred_start_time: string;
  preferred_end_time: string;
  work_days_per_week: number;
  procrastination_level: string;
  focus_duration: number;
  writing_style: string;
  email_notifications: boolean;
  daily_email_time: string;
  timezone: string;
  ai_provider: string;
}

export interface TimelineTask {
  title: string;
  description: string;
  estimated_hours: number;
  priority: number;
  due_date: string;
  dependencies: string[];
  focus_sessions?: number;
  deliverable?: string;
  assigned_date?: string;
}

export interface TimelinePhase {
  name: string;
  description: string;
  start_date: string;
  end_date: string;
  estimated_hours: number;
  tasks: TimelineTask[];
}

export interface TimelineMilestone {
  name: string;
  description: string;
  target_date: string;
  deliverables: string[];
}

export interface TimelineData {
  phases: TimelinePhase[];
  milestones: TimelineMilestone[];
  todays_tasks?: TimelineTask[];
  daily_assignments?: { [date: string]: TimelineTask[] };
}

export interface TimelineResponse {
  success: boolean;
  timeline: {
    timeline: TimelineData;
    metadata: {
      total_days: number;
      working_days: number;
      total_hours: number;
      field: string;
      generated_at: string;
      buffer_applied: number;
    };
  };
  user_info: {
    name: string;
    thesis_topic: string;
    deadline: string;
  };
}

export interface HealthCheck {
  status: string;
  timestamp: string;
  services: {
    ai_service: boolean;
    email_service: boolean;
    config: boolean;
  };
}

export interface BrainstormingMessage {
  message: string;
  conversation_history: ChatMessage[];
  user_field?: string;
  ai_provider: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface BrainstormingResponse {
  success: boolean;
  response: string;
  topic_clarity: 'low' | 'medium' | 'high';
  suggested_topic?: string;
  suggested_description?: string;
  next_question?: string;
}

export interface TopicFinalization {
  conversation_history: ChatMessage[];
  user_field: string;
  ai_provider: string;
}

export interface TopicFinalizationResponse {
  success: boolean;
  thesis_topic: string;
  thesis_description: string;
}

export interface EmailTestResponse {
  success: boolean;
  message: string;
  recipient: string;
  data_source?: string;
  tasks_today?: number;
  workspace_url?: string;
}

export interface NotionWorkspaceResponse {
  success: boolean;
  workspace: {
    main_page: any;
    task_database: any;
    milestone_database: any;
    progress_page: any;
    resources_page: any;
    created_at: string;
  };
  message: string;
}

export interface NotionSyncResponse {
  success: boolean;
  sync_result: {
    milestones_synced: number;
    tasks_synced: number;
    status: string;
    synced_at: string;
  };
  message: string;
}

export interface ThesisProject {
  id: number;
  thesis_topic: string;
  thesis_field: string;
  user_name: string;
  thesis_deadline: string;
  created_at: string;
  completion_percentage: number;
  notion_workspace_url?: string;
}

export interface ThesisProjectDetails {
  id: number;
  user_name: string;
  email: string;
  thesis_topic: string;
  thesis_description: string;
  thesis_field: string;
  thesis_deadline: string;
  daily_hours_available: number;
  work_days_per_week: number;
  focus_duration: number;
  procrastination_level: string;
  writing_style: string;
  ai_provider: string;
  created_at: string;
  notion_workspace_url?: string;
  notion_task_db_id?: string;
  notion_milestone_db_id?: string;
  notion_main_page_id?: string;
  notion_progress_page_id?: string;
  timeline_data: any;
  progress: any;
}

export interface ThesisProjectsResponse {
  success: boolean;
  projects: ThesisProject[];
}

export interface ThesisProjectResponse {
  success: boolean;
  project: ThesisProjectDetails | null;
}

// File upload interface
export interface FileUploadResponse {
  success: boolean;
  file_path?: string;
  filename?: string;
  size?: number;
  error?: string;
}

// Create axios instance
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create a separate instance for timeline generation with longer timeout
const timelineApi = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 120000, // 2 minutes for complex timeline generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// Add same interceptors to timeline API
timelineApi.interceptors.request.use(
  (config) => {
    console.log(`🔄 Timeline API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Timeline API Request Error:', error);
    return Promise.reject(error);
  }
);

timelineApi.interceptors.response.use(
  (response) => {
    console.log(`✅ Timeline API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ Timeline API Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// API functions
export const apiService = {
  // Health check
  async healthCheck(): Promise<HealthCheck> {
    const response = await api.get('/health');
    return response.data;
  },

  // Generate timeline - use longer timeout
  async generateTimeline(userData: UserQuestionnaireData): Promise<TimelineResponse> {
    const response = await timelineApi.post('/api/generate-timeline', userData);
    return response.data;
  },

  // Test email
  async testEmail(emailData: { email: string; workspace_info?: any; user_name?: string }): Promise<EmailTestResponse> {
    const response = await api.post('/api/test-email', emailData);
    return response.data;
  },

  // Get sample user data
  async getSampleUser(): Promise<UserQuestionnaireData> {
    const response = await api.get('/api/sample-user');
    return response.data;
  },

  // Notion integration functions
  async createNotionWorkspace(workspaceData: {
    user_name: string;
    thesis_topic: string;
    thesis_description: string;
    project_id?: number;
  }): Promise<NotionWorkspaceResponse> {
    const response = await api.post('/api/create-notion-workspace', workspaceData);
    return response.data;
  },

  async syncTimelineToNotion(timelineData: any, workspaceInfo: any, userInfo: any): Promise<NotionSyncResponse> {
    const response = await api.post('/api/sync-timeline-to-notion', {
      timeline_data: timelineData,
      workspace_info: workspaceInfo,
      user_name: userInfo.user_name,
      project_id: userInfo.project_id || null
    });
    return response.data;
  },

  async testNotionConnection(): Promise<{success: boolean; message: string; timestamp: string}> {
    const response = await api.post('/api/test-notion-connection');
    return response.data;
  },

  // File upload for tools
  uploadFile: async (file: File): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/upload-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Task Work API functions
  async startTaskSession(data: {
    task_id: string;
    user_id: string;
    task_info: any;
  }): Promise<{
    success: boolean;
    session_id: string;
    task_info: any;
    available_tools: any[];
    welcome_message: string;
    ethics_summary: any;
  }> {
    const response = await api.post('/api/task/start', data);
    return response.data;
  },

  async sendTaskMessage(data: {
    task_id: string;
    message: string;
    tool_request?: any;
  }): Promise<{
    success: boolean;
    ai_response: string;
    ethics_score: number;
    ethics_reasoning: string;
    intervention?: {
      needed: boolean;
      message: string;
    };
    tool_result?: any;
  }> {
    const response = await api.post('/api/task/chat', data);
    return response.data;
  },

  async useTaskTool(data: {
    task_id: string;
    tool_name: string;
    tool_params: any;
  }): Promise<{
    success: boolean;
    tool: string;
    summary: string;
    [key: string]: any;
  }> {
    const response = await api.post('/api/task/tool', data);
    return response.data;
  },

  async completeTask(data: {
    task_id: string;
    deliverable: string;
  }): Promise<{
    success: boolean;
    task_id: string;
    session_id: string;
    deliverable: string;
    deliverable_analysis: any;
    session_summary: any;
  }> {
    const response = await api.post('/api/task/complete', data);
    return response.data;
  },

  async getTaskStatus(taskId: string): Promise<{
    success: boolean;
    session_id: string;
    task_id: string;
    is_completed: boolean;
    messages: number;
    tools_used: number;
    ethics_summary: any;
    created_at: string;
  }> {
    const response = await api.get(`/api/task/status/${taskId}`);
    return response.data;
  },
};

// Brainstorming API functions
export const brainstormChat = async (data: BrainstormingMessage): Promise<BrainstormingResponse> => {
  const response = await api.post('/api/brainstorm-chat', data);
  return response.data;
};

export const finalizeTopic = async (data: TopicFinalization): Promise<TopicFinalizationResponse> => {
  const response = await api.post('/api/finalize-topic', data);
  return response.data;
};

// Thesis persistence API functions
export const getThesisProjects = async (): Promise<ThesisProjectsResponse> => {
  const response = await api.get('/api/thesis-projects');
  return response.data;
};

export const getThesisProject = async (projectId: number): Promise<ThesisProjectResponse> => {
  const response = await api.get(`/api/thesis-projects/${projectId}`);
  return response.data;
};

export const getLatestThesis = async (): Promise<ThesisProjectResponse> => {
  const response = await api.get('/api/latest-thesis');
  return response.data;
};

export const deactivateThesisProject = async (projectId: number): Promise<{ success: boolean; message: string }> => {
  const response = await api.delete(`/api/thesis-projects/${projectId}`);
  return response.data;
};

export default api;

// Field options
export const THESIS_FIELDS = [
  'Computer Science',
  'Psychology',
  'Biology',
  'Chemistry',
  'Physics',
  'Mathematics',
  'Engineering',
  'Business',
  'Literature',
  'History',
  'Other'
];

export const PROCRASTINATION_LEVELS = [
  { value: 'low', label: 'Low - I rarely procrastinate' },
  { value: 'medium', label: 'Medium - I sometimes procrastinate' },
  { value: 'high', label: 'High - I frequently procrastinate' }
];

export const WRITING_STYLES = [
  { value: 'draft_then_revise', label: 'Draft then Revise - I write quickly then edit' },
  { value: 'polish_as_go', label: 'Polish as I Go - I edit while writing' }
];

export const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Australia/Sydney'
];

export const AI_PROVIDERS = [
  { value: 'ollama', label: 'Ollama (Local Llama) - Free & Private', description: 'Runs locally on your machine, completely free and private' },
  { value: 'gemini', label: 'Google Gemini - Cloud API', description: 'Google\'s AI model, requires API key and internet connection' }
]; 