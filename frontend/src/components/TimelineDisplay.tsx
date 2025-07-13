import React, { useState } from 'react';
import { format, parseISO, differenceInDays } from 'date-fns';
import { 
  Calendar, 
  Clock, 
  CheckCircle, 
  Circle, 
  AlertCircle, 
  Target,
  ChevronDown,
  ChevronUp,
  Download,
  Edit,
  Mail,
  FileText,
  ExternalLink
} from 'lucide-react';
import { TimelineData, TimelineResponse, apiService } from '../services/api';

interface TimelineDisplayProps {
  timelineData: TimelineResponse;
  onEmailTest?: () => void;
  userQuestionnaireData?: any;
}

export default function TimelineDisplay({ timelineData, onEmailTest, userQuestionnaireData }: TimelineDisplayProps) {
  const [expandedPhases, setExpandedPhases] = useState<Set<number>>(new Set([0]));
  const [notionWorkspace, setNotionWorkspace] = useState<any>(null);
  const [loadingNotion, setLoadingNotion] = useState(false);
  const [loadingEmail, setLoadingEmail] = useState(false);
  
  const togglePhase = (index: number) => {
    const newExpanded = new Set(expandedPhases);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedPhases(newExpanded);
  };

  const timeline = timelineData.timeline.timeline;
  const metadata = timelineData.timeline.metadata;
  
  // Calculate progress (for demo purposes, assuming we're at the beginning)
  const today = new Date();
  const getTaskStatus = (dueDate: string) => {
    const due = parseISO(dueDate);
    const daysDiff = differenceInDays(due, today);
    
    if (daysDiff < 0) return 'overdue';
    if (daysDiff === 0) return 'today';
    if (daysDiff <= 7) return 'upcoming';
    return 'future';
  };

  const getPhaseStatus = (startDate: string, endDate: string) => {
    const start = parseISO(startDate);
    const end = parseISO(endDate);
    
    if (today < start) return 'future';
    if (today > end) return 'completed';
    return 'current';
  };

  const handleCreateNotionWorkspace = async () => {
    if (!userQuestionnaireData) {
      alert('❌ User data required for creating Notion workspace');
      return;
    }

    setLoadingNotion(true);
    try {
      const response = await apiService.createNotionWorkspace(userQuestionnaireData);
      if (response.success) {
        setNotionWorkspace(response.workspace);
        alert('✅ Notion workspace created successfully!');
      } else {
        alert('❌ Failed to create Notion workspace');
      }
    } catch (error) {
      console.error('Notion workspace creation failed:', error);
      alert('❌ Failed to create Notion workspace');
    } finally {
      setLoadingNotion(false);
    }
  };

  const handleSyncToNotion = async () => {
    if (!notionWorkspace) {
      alert('❌ Please create a Notion workspace first');
      return;
    }

    setLoadingNotion(true);
    try {
      const response = await apiService.syncTimelineToNotion(
        timelineData.timeline.timeline,
        notionWorkspace,
        timelineData.user_info
      );
      
      if (response.success) {
        alert(`✅ Timeline synced! ${response.sync_result.milestones_synced} milestones and ${response.sync_result.tasks_synced} tasks synced to Notion.`);
      } else {
        alert('❌ Failed to sync timeline to Notion');
      }
    } catch (error) {
      console.error('Notion sync failed:', error);
      alert('❌ Failed to sync timeline to Notion');
    } finally {
      setLoadingNotion(false);
    }
  };

  const handleEmailTestWithNotion = async () => {
    setLoadingEmail(true);
    try {
      const emailData = {
        email: userQuestionnaireData?.email || 'mouazan99@gmail.com',
        workspace_info: notionWorkspace,
        user_name: userQuestionnaireData?.name || timelineData.user_info.name
      };
      
      const response = await apiService.testEmail(emailData);
      
      if (response.success) {
        const source = response.data_source === 'notion' ? 'real Notion data' : 'test data';
        const tasksInfo = response.tasks_today ? ` (${response.tasks_today} tasks today)` : '';
        alert(`✅ Email sent successfully using ${source}${tasksInfo}!`);
      } else {
        alert('❌ Failed to send test email');
      }
    } catch (error) {
      console.error('Email test failed:', error);
      alert('❌ Failed to send test email');
    } finally {
      setLoadingEmail(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="card">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center">
          <div>
            <h1 className="text-3xl font-bold text-secondary-900 mb-2">
              Your AI-Generated Timeline
            </h1>
            <p className="text-secondary-600 mb-4">
              {timelineData.user_info.thesis_topic} • {timelineData.user_info.name}
            </p>
          </div>
          
          <div className="flex flex-wrap gap-3">
            <button className="btn-secondary flex items-center">
              <Download className="h-4 w-4 mr-2" />
              Export PDF
            </button>
            <button className="btn-secondary flex items-center">
              <Edit className="h-4 w-4 mr-2" />
              Edit Timeline
            </button>
            
            {/* Notion Integration Buttons */}
            {!notionWorkspace ? (
              <button 
                onClick={handleCreateNotionWorkspace}
                disabled={loadingNotion}
                className="btn-outline flex items-center disabled:opacity-50"
              >
                <FileText className="h-4 w-4 mr-2" />
                {loadingNotion ? 'Creating...' : 'Create Notion Workspace'}
              </button>
            ) : (
              <div className="flex gap-2">
                <button 
                  onClick={handleSyncToNotion}
                  disabled={loadingNotion}
                  className="btn-primary flex items-center disabled:opacity-50"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  {loadingNotion ? 'Syncing...' : 'Sync to Notion'}
                </button>
                <a 
                  href={notionWorkspace.main_page.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary flex items-center"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Open in Notion
                </a>
              </div>
            )}
            
                            <button 
                  onClick={handleEmailTestWithNotion} 
                  disabled={loadingEmail}
                  className="btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Mail className="h-4 w-4 mr-2" />
                  {loadingEmail ? 'Sending...' : 'Send Email'}
                </button>
          </div>
        </div>

        {/* Notion Status */}
        {notionWorkspace && (
          <div className="mt-4 p-3 bg-success-50 border border-success-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-success-600" />
                <span className="text-success-800 font-medium">Notion Workspace Active</span>
              </div>
              <div className="flex gap-2">
                <a 
                  href={notionWorkspace.task_database.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-success-600 hover:text-success-800 text-sm"
                >
                  📊 Tasks
                </a>
                <a 
                  href={notionWorkspace.milestone_database.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-success-600 hover:text-success-800 text-sm"
                >
                  🎯 Milestones
                </a>
                <a 
                  href={notionWorkspace.progress_page.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-success-600 hover:text-success-800 text-sm"
                >
                  📈 Progress
                </a>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Timeline Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card text-center">
          <div className="text-2xl font-bold text-primary-600 mb-2">
            {metadata.total_days}
          </div>
          <div className="text-sm text-secondary-600">Total Days</div>
        </div>
        
        <div className="card text-center">
          <div className="text-2xl font-bold text-success-600 mb-2">
            {metadata.working_days}
          </div>
          <div className="text-sm text-secondary-600">Working Days</div>
        </div>
        
        <div className="card text-center">
          <div className="text-2xl font-bold text-warning-600 mb-2">
            {metadata.total_hours}
          </div>
          <div className="text-sm text-secondary-600">Total Hours</div>
        </div>
        
        <div className="card text-center">
          <div className="text-2xl font-bold text-accent-600 mb-2">
            {timeline.phases.length}
          </div>
          <div className="text-sm text-secondary-600">Phases</div>
        </div>
      </div>

      {/* Milestones */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-bold text-secondary-900 flex items-center">
            <Target className="h-5 w-5 mr-2 text-primary-600" />
            Key Milestones
          </h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {timeline.milestones.map((milestone, index) => (
            <div key={index} className="flex items-start space-x-3 p-4 bg-primary-50 rounded-lg border border-primary-200">
              <div className="flex-shrink-0 w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                {index + 1}
              </div>
              <div>
                <h3 className="font-semibold text-secondary-900">{milestone.name}</h3>
                <p className="text-sm text-secondary-600 mb-2">{milestone.description}</p>
                <div className="flex items-center text-sm text-primary-700">
                  <Calendar className="h-4 w-4 mr-1" />
                  {format(parseISO(milestone.target_date), 'MMM dd, yyyy')}
                </div>
                <div className="mt-2">
                  <p className="text-sm text-secondary-600">Deliverables:</p>
                  <ul className="text-sm text-secondary-700 ml-4">
                    {milestone.deliverables.map((deliverable, idx) => (
                      <li key={idx} className="list-disc">{deliverable}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Phases */}
      <div className="space-y-6">
        {timeline.phases.map((phase, phaseIndex) => {
          const phaseStatus = getPhaseStatus(phase.start_date, phase.end_date);
          const isExpanded = expandedPhases.has(phaseIndex);
          
          return (
            <div key={phaseIndex} className="card">
              <div 
                className="cursor-pointer"
                onClick={() => togglePhase(phaseIndex)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-white font-bold ${
                      phaseStatus === 'completed' ? 'bg-success-600' :
                      phaseStatus === 'current' ? 'bg-warning-600' :
                      'bg-secondary-400'
                    }`}>
                      {phaseStatus === 'completed' ? (
                        <CheckCircle className="h-6 w-6" />
                      ) : phaseStatus === 'current' ? (
                        <AlertCircle className="h-6 w-6" />
                      ) : (
                        <Circle className="h-6 w-6" />
                      )}
                    </div>
                    
                    <div>
                      <h3 className="text-lg font-semibold text-secondary-900">
                        Phase {phaseIndex + 1}: {phase.name}
                      </h3>
                      <p className="text-sm text-secondary-600">{phase.description}</p>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-secondary-500">
                        <div className="flex items-center">
                          <Calendar className="h-4 w-4 mr-1" />
                          {format(parseISO(phase.start_date), 'MMM dd')} - {format(parseISO(phase.end_date), 'MMM dd, yyyy')}
                        </div>
                        <div className="flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          {phase.estimated_hours} hours
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      phaseStatus === 'completed' ? 'bg-success-100 text-success-800' :
                      phaseStatus === 'current' ? 'bg-warning-100 text-warning-800' :
                      'bg-secondary-100 text-secondary-800'
                    }`}>
                      {phaseStatus === 'completed' ? 'Completed' :
                       phaseStatus === 'current' ? 'In Progress' :
                       'Upcoming'}
                    </span>
                    
                    {isExpanded ? (
                      <ChevronUp className="h-5 w-5 text-secondary-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-secondary-400" />
                    )}
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="mt-6 pt-6 border-t border-secondary-200">
                  <div className="space-y-4">
                    {phase.tasks.map((task, taskIndex) => {
                      const taskStatus = getTaskStatus(task.due_date);
                      
                      return (
                        <div key={taskIndex} className="flex items-start space-x-3 p-4 bg-secondary-50 rounded-lg">
                          <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                            taskStatus === 'overdue' ? 'bg-danger-600' :
                            taskStatus === 'today' ? 'bg-warning-600' :
                            taskStatus === 'upcoming' ? 'bg-primary-600' :
                            'bg-secondary-400'
                          }`}>
                            <div className="w-2 h-2 bg-white rounded-full"></div>
                          </div>
                          
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <h4 className="font-medium text-secondary-900">{task.title}</h4>
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                taskStatus === 'overdue' ? 'bg-danger-100 text-danger-800' :
                                taskStatus === 'today' ? 'bg-warning-100 text-warning-800' :
                                taskStatus === 'upcoming' ? 'bg-primary-100 text-primary-800' :
                                'bg-secondary-100 text-secondary-800'
                              }`}>
                                Priority {task.priority}
                              </span>
                            </div>
                            
                            <p className="text-sm text-secondary-600 mt-1">{task.description}</p>
                            
                            <div className="flex items-center space-x-4 mt-2 text-sm text-secondary-500">
                              <div className="flex items-center">
                                <Calendar className="h-4 w-4 mr-1" />
                                Due: {format(parseISO(task.due_date), 'MMM dd, yyyy')}
                              </div>
                              <div className="flex items-center">
                                <Clock className="h-4 w-4 mr-1" />
                                {task.estimated_hours} hours
                              </div>
                            </div>
                            
                            {task.dependencies.length > 0 && (
                              <div className="mt-2">
                                <span className="text-sm text-secondary-500">Dependencies: </span>
                                <span className="text-sm text-secondary-700">
                                  {task.dependencies.join(', ')}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="card bg-secondary-50">
        <div className="text-center">
          <p className="text-sm text-secondary-600 mb-2">
            Timeline generated on {format(parseISO(metadata.generated_at), 'MMM dd, yyyy \'at\' h:mm a')}
          </p>
          <p className="text-xs text-secondary-500">
            Buffer time of {Math.round(metadata.buffer_applied * 100)}% applied for flexibility
          </p>
        </div>
      </div>
    </div>
  );
} 