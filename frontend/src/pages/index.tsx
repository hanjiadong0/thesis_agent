import { useState } from 'react';
import BrainstormingChat from '../components/BrainstormingChat';
import QuestionnaireForm from '../components/QuestionnaireForm';
import TimelineDisplay from '../components/TimelineDisplay';
import ThesisSelector from '../components/ThesisSelector';
import { 
  apiService, 
  type UserQuestionnaireData, 
  type TimelineResponse,
  type ThesisProject,
  getThesisProject
} from '../services/api';

type CurrentView = 'selector' | 'brainstorming' | 'questionnaire' | 'timeline';

export default function Home() {
  const [currentView, setCurrentView] = useState<CurrentView>('selector');
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [userQuestionnaireData, setUserQuestionnaireData] = useState<UserQuestionnaireData | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentProjectId, setCurrentProjectId] = useState<number | null>(null);
  const [existingNotionWorkspace, setExistingNotionWorkspace] = useState<any>(null);

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
              id: projectData.notion_progress_page_id || projectData.notion_main_page_id // Use actual progress page ID or fallback to main page
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
          email_notifications: true, // Default value
          preferred_start_time: "09:00", // Default value
          preferred_end_time: "17:00", // Default value
          daily_email_time: "08:00", // Default value
          timezone: "UTC" // Default value
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
    // Clear any existing data
    setTimelineData(null);
    setUserQuestionnaireData(null);
    setCurrentProjectId(null);
    setExistingNotionWorkspace(null);
    
    // Clear any brainstorming data
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem('brainstormed_topic');
      window.sessionStorage.removeItem('brainstormed_description');
      window.sessionStorage.removeItem('brainstormed_field');
    }
    
    setCurrentView('brainstorming');
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
      // Get brainstormed data if available
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
        // Set project ID from response if available
        setCurrentProjectId((result as any)?.project_id || null);
        setCurrentView('timeline');
        
        // Clear brainstorming data
        if (typeof window !== 'undefined') {
          window.sessionStorage.removeItem('brainstormed_topic');
          window.sessionStorage.removeItem('brainstormed_description');
          window.sessionStorage.removeItem('brainstormed_field');
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
          <ThesisSelector
            onContinueThesis={handleContinueThesis}
            onStartNew={handleStartNew}
            loading={loading}
          />
        );
      
      case 'brainstorming':
        return (
          <BrainstormingChat 
            onTopicFinalized={handleTopicFinalized}
            onBack={handleBackToSelector}
          />
        );
      
      case 'questionnaire':
        return (
          <QuestionnaireForm 
            onSubmit={handleQuestionnaireSubmit} 
            loading={loading}
            onBack={handleBackToBrainstorming}
          />
        );
      
      case 'timeline':
        return timelineData ? (
          <TimelineDisplay 
            timelineData={timelineData}
            onEmailTest={handleEmailTestWithNotion}
            userQuestionnaireData={userQuestionnaireData}
            onBack={handleBackToSelector}
            currentProjectId={currentProjectId || undefined}
            existingNotionWorkspace={existingNotionWorkspace}
          />
        ) : null;
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen">
      {renderCurrentView()}
    </div>
  );
} 