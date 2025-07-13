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
}

export interface TimelineTask {
  title: string;
  description: string;
  estimated_hours: number;
  priority: number;
  due_date: string;
  dependencies: string[];
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

// Create axios instance
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
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

// API functions
export const apiService = {
  // Health check
  async healthCheck(): Promise<HealthCheck> {
    const response = await api.get('/health');
    return response.data;
  },

  // Generate timeline
  async generateTimeline(userData: UserQuestionnaireData): Promise<TimelineResponse> {
    const response = await api.post('/api/generate-timeline', userData);
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
  async createNotionWorkspace(userData: UserQuestionnaireData): Promise<NotionWorkspaceResponse> {
    const response = await api.post('/api/create-notion-workspace', userData);
    return response.data;
  },

  async syncTimelineToNotion(timelineData: any, workspaceInfo: any, userInfo: any): Promise<NotionSyncResponse> {
    const response = await api.post('/api/sync-timeline-to-notion', {
      timeline_data: timelineData,
      workspace_info: workspaceInfo,
      user_info: userInfo
    });
    return response.data;
  },

  async testNotionConnection(): Promise<{success: boolean; message: string; timestamp: string}> {
    const response = await api.post('/api/test-notion-connection');
    return response.data;
  },
};

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

export default api; 