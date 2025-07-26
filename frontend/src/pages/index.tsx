import React, { useState, useEffect } from 'react';
import ThesisSelector from '../components/ThesisSelector';
import QuestionnaireForm from '../components/QuestionnaireForm';
import TimelineDisplay from '../components/TimelineDisplay';
import BrainstormingChat from '../components/BrainstormingChat';
import { 
  UserQuestionnaireData, 
  TimelineData, 
  TimelineResponse, 
  ThesisProject,
  apiService,
  getThesisProject 
} from '../services/api';

type ViewType = 'selector' | 'brainstorming' | 'questionnaire' | 'timeline';

interface NotionWorkspaceInfo {
  workspace_url: string;
  task_db_id: string;
  milestone_db_id: string;
  main_page_id: string;
  progress_page_id?: string;
}

export default function Home() {
  const [currentView, setCurrentView] = useState<ViewType>('selector');
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [userQuestionnaireData, setUserQuestionnaireData] = useState<UserQuestionnaireData | null>(null);
  const [currentProjectId, setCurrentProjectId] = useState<number | null>(null);
  const [existingNotionWorkspace, setExistingNotionWorkspace] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleContinueThesis = async (project: ThesisProject) => {
    try {
      setLoading(true);
      
      // Fetch full project details
      const response = await getThesisProject(project.id);
      if (response.success && response.project) {
        const projectData = response.project;
        
        // Set current project
        setCurrentProjectId(projectData.id);
        
        // Restore Notion workspace data if it exists
        if (projectData.notion_workspace_url) {
          const workspaceData = {
            success: true,
            main_page: {
              url: projectData.notion_workspace_url,
              id: projectData.notion_main_page_id
            },
            task_database: {
              id: projectData.notion_task_db_id
            },
            milestone_database: {
              id: projectData.notion_milestone_db_id
            },
            progress_page: {
              id: projectData.notion_progress_page_id || projectData.notion_main_page_id
            }
          };
          setExistingNotionWorkspace(workspaceData);
        } else {
          setExistingNotionWorkspace(null);
        }
        
        // Convert project data back to timeline format
        const timelineData: TimelineResponse = {
          success: true,
          timeline: {
            timeline: {
              phases: projectData.timeline_data?.phases || [],
              milestones: projectData.timeline_data?.milestones || []
            },
            metadata: {
              total_days: 0,
              working_days: 0,
              total_hours: 0,
              field: projectData.thesis_field,
              generated_at: projectData.created_at,
              buffer_applied: 0
            }
          },
          user_info: {
            name: projectData.user_name,
            thesis_topic: projectData.thesis_topic,
            deadline: projectData.thesis_deadline
          }
        };
        
        // Convert project data back to questionnaire format
        const questionnaireData: UserQuestionnaireData = {
          name: projectData.user_name,
          email: projectData.email,
          thesis_topic: projectData.thesis_topic,
          thesis_description: projectData.thesis_description,
          thesis_field: projectData.thesis_field as any,
          thesis_deadline: projectData.thesis_deadline,
          daily_hours_available: projectData.daily_hours_available,
          work_days_per_week: projectData.work_days_per_week,
          focus_duration: projectData.focus_duration,
          procrastination_level: projectData.procrastination_level as any,
          writing_style: projectData.writing_style as any,
          ai_provider: projectData.ai_provider as any,
          email_notifications: true,
          preferred_start_time: "09:00",
          preferred_end_time: "17:00",
          daily_email_time: "08:00",
          timezone: "UTC"
        };
        
        setTimelineData(timelineData);
        setUserQuestionnaireData(questionnaireData);
        setCurrentView('timeline');
      } else {
        alert('Failed to load project details');
      }
    } catch (error) {
      console.error('Error loading thesis project:', error);
      alert('Failed to load thesis project');
    } finally {
      setLoading(false);
    }
  };

  const handleStartNew = () => {
    setCurrentView('brainstorming');
    setTimelineData(null);
    setUserQuestionnaireData(null);
    setCurrentProjectId(null);
    setExistingNotionWorkspace(null);
  };

  const handleTopicFinalized = (topic: string, description: string) => {
    setCurrentView('questionnaire');
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem('brainstormed_topic', topic);
      window.sessionStorage.setItem('brainstormed_description', description);
    }
  };

  const handleQuestionnaireSubmit = async (data: UserQuestionnaireData) => {
    setLoading(true);
    try {
      const brainstormedTopic = typeof window !== 'undefined' ? window.sessionStorage.getItem('brainstormed_topic') : null;
      const brainstormedDescription = typeof window !== 'undefined' ? window.sessionStorage.getItem('brainstormed_description') : null;
      
      const finalData = {
        ...data,
        thesis_topic: brainstormedTopic || data.thesis_topic,
        thesis_description: brainstormedDescription || data.thesis_description
      };

      const result = await apiService.generateTimeline(finalData);
      
      if (result.success) {
        setTimelineData(result);
        setUserQuestionnaireData(finalData);
        setCurrentProjectId((result as any)?.project_id || null);
        setCurrentView('timeline');
        
        if (typeof window !== 'undefined') {
          window.sessionStorage.removeItem('brainstormed_topic');
          window.sessionStorage.removeItem('brainstormed_description');
        }
      } else {
        alert('Failed to generate timeline');
      }
    } catch (error) {
      console.error('Timeline generation error:', error);
      alert('Error generating timeline');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailTestWithNotion = async () => {
    if (!timelineData || !userQuestionnaireData) return;
    
    try {
      setLoading(true);
      await apiService.testEmail({
        email: userQuestionnaireData.email,
        user_name: userQuestionnaireData.name,
        workspace_info: (timelineData as any)?.workspace_info || null
      });
      alert('Email sent successfully!');
    } catch (error) {
      console.error('Email test error:', error);
      alert('Failed to send email');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToSelector = () => {
    setCurrentView('selector');
    setTimelineData(null);
    setUserQuestionnaireData(null);
    setCurrentProjectId(null);
  };

  const handleBackToBrainstorming = () => {
    setCurrentView('brainstorming');
  };

  const handleBackToQuestionnaire = () => {
    setCurrentView('questionnaire');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'selector':
        return (
          <div className="animate-fade-in-up">
            <ThesisSelector
              onContinueThesis={handleContinueThesis}
              onStartNew={handleStartNew}
              loading={loading}
            />
          </div>
        );
      
      case 'brainstorming':
        return (
          <div className="animate-fade-in-up">
            <BrainstormingChat 
              onTopicFinalized={handleTopicFinalized}
              onBack={handleBackToSelector}
            />
          </div>
        );
      
      case 'questionnaire':
        return (
          <div className="animate-fade-in-up">
            <QuestionnaireForm 
              onSubmit={handleQuestionnaireSubmit} 
              loading={loading}
              onBack={handleBackToBrainstorming}
            />
          </div>
        );
      
      case 'timeline':
        return timelineData ? (
          <div className="animate-fade-in-up">
            <TimelineDisplay 
              timelineData={timelineData}
              onEmailTest={handleEmailTestWithNotion}
              userQuestionnaireData={userQuestionnaireData}
              onBack={handleBackToSelector}
              currentProjectId={currentProjectId || undefined}
              existingNotionWorkspace={existingNotionWorkspace}
            />
          </div>
        ) : null;
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-10 left-10 w-32 h-32 bg-white/10 rounded-full blur-xl animate-float"></div>
        <div className="absolute top-1/2 right-20 w-48 h-48 bg-blue-400/10 rounded-full blur-2xl animate-float" style={{animationDelay: '1s'}}></div>
        <div className="absolute bottom-20 left-1/4 w-24 h-24 bg-purple-400/10 rounded-full blur-xl animate-float" style={{animationDelay: '2s'}}></div>
        <div className="absolute top-1/4 left-1/2 w-16 h-16 bg-emerald-400/10 rounded-full blur-lg animate-float" style={{animationDelay: '0.5s'}}></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10">
        {renderCurrentView()}
      </div>

      {/* Educational Pattern Overlay */}
      <div className="absolute inset-0 opacity-5 pointer-events-none">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000000' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          backgroundSize: '30px 30px'
        }}></div>
      </div>
    </div>
  );
} 