import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Clock, 
  Target, 
  ChevronDown, 
  ChevronUp, 
  CheckCircle, 
  Circle, 
  AlertCircle, 
  Mail, 
  FileText,
  Play,
  CheckSquare,
  User,
  ArrowLeft
} from 'lucide-react';
import { format, parseISO, isToday, isBefore, isAfter } from 'date-fns';
import { TimelineData, TimelineResponse, TimelineTask, apiService } from '../services/api';
import TaskChat from './TaskChat';

interface TimelineDisplayProps {
  timelineData: TimelineResponse;
  onEmailTest?: () => void;
  userQuestionnaireData?: any;
  onBack?: () => void;
  currentProjectId?: number; // Add project ID prop
  existingNotionWorkspace?: any; // Add existing workspace prop
}

export default function TimelineDisplay({ 
  timelineData, 
  onEmailTest, 
  userQuestionnaireData, 
  onBack, 
  currentProjectId,
  existingNotionWorkspace 
}: TimelineDisplayProps) {
  const [expandedPhases, setExpandedPhases] = useState<Set<number>>(new Set([0]));
  const [notionWorkspace, setNotionWorkspace] = useState<any>(existingNotionWorkspace || null);
  const [loadingNotion, setLoadingNotion] = useState(false);
  const [loadingEmail, setLoadingEmail] = useState(false);
  const [currentTask, setCurrentTask] = useState<TimelineTask | null>(null);
  const [showTaskChat, setShowTaskChat] = useState(false);
  
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
    if (due < today) return 'overdue';
    if (isToday(due)) return 'today';
    if (isBefore(due, today)) return 'upcoming';
    return 'current';
  };

  const getPhaseStatus = (startDate: string, endDate: string) => {
    const start = parseISO(startDate);
    const end = parseISO(endDate);
    
    if (isBefore(today, start)) return 'future';
    if (isAfter(today, end)) return 'completed';
    return 'current';
  };

  const handleCreateAndSyncNotion = async () => {
    if (!userQuestionnaireData) {
      alert('❌ User data required for creating Notion workspace');
      return;
    }

    setLoadingNotion(true);
    try {
      // Create Notion workspace with correct data structure
      const workspaceData = {
        user_name: userQuestionnaireData.name || timelineData.user_info.name,
        thesis_topic: userQuestionnaireData.thesis_topic || timelineData.user_info.thesis_topic,
        thesis_description: userQuestionnaireData.thesis_description || 'AI-generated thesis project',
        project_id: currentProjectId
      };
      
      const workspaceResponse = await apiService.createNotionWorkspace(workspaceData);
      
      if (workspaceResponse.success) {
        setNotionWorkspace(workspaceResponse);
        
        // Automatically sync timeline data
        const syncResponse = await apiService.syncTimelineToNotion(
          timelineData.timeline.timeline,
          workspaceResponse,
          {
            user_name: userQuestionnaireData.name || timelineData.user_info.name,
            thesis_topic: userQuestionnaireData.thesis_topic || timelineData.user_info.thesis_topic,
            project_id: currentProjectId
          }
        );
        
        if (syncResponse.success) {
          alert('✅ Notion workspace created and timeline synced successfully!');
        } else {
          alert('✅ Notion workspace created, but timeline sync failed. You can try syncing again.');
        }
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

  const handleStartWorking = (task: TimelineTask) => {
    setCurrentTask(task);
    setShowTaskChat(true);
  };

  const handleTaskComplete = (deliverable: string) => {
    // Mark task as completed and save deliverable
    console.log('Task completed with deliverable:', deliverable);
    setShowTaskChat(false);
    setCurrentTask(null);
    // TODO: Update task status in backend
  };

  const handleBackFromTask = () => {
    setShowTaskChat(false);
    setCurrentTask(null);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Today's Tasks Section - Prominent at top */}
      {timelineData.timeline.timeline.todays_tasks && timelineData.timeline.timeline.todays_tasks.length > 0 && (
        <div className="card border-l-4 border-l-primary-600 bg-gradient-to-r from-primary-50 to-primary-25">
          <div className="card-header">
            <h2 className="text-xl font-bold text-primary-900 flex items-center">
              <CheckSquare className="h-6 w-6 mr-2 text-primary-600" />
              Today's Tasks ({new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })})
            </h2>
            <p className="text-sm text-primary-700 mt-1">Focus on these tasks today to stay on track</p>
          </div>
          
          <div className="space-y-4">
            {timelineData.timeline.timeline.todays_tasks.map((task: TimelineTask, index: number) => (
              <div key={index} className="p-4 bg-white rounded-lg border border-primary-200 shadow-sm">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="flex-shrink-0 w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                        {index + 1}
                      </div>
                      <h3 className="font-semibold text-secondary-900">{task.title}</h3>
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-primary-100 text-primary-800">
                        Priority {task.priority}
                      </span>
                    </div>
                    
                    <p className="text-sm text-secondary-600 mb-3 ml-11">{task.description}</p>
                    
                    <div className="flex items-center space-x-4 ml-11 text-sm text-secondary-500">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {task.estimated_hours}h ({task.focus_sessions || Math.ceil(task.estimated_hours * 2)} × {Math.floor((task.estimated_hours / (task.focus_sessions || Math.ceil(task.estimated_hours * 2))) * 60)}min sessions)
                      </div>
                      {task.deliverable && (
                        <div className="flex items-center">
                          <Target className="h-4 w-4 mr-1" />
                          {task.deliverable}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => handleStartWorking(task)}
                    className="btn-primary flex items-center space-x-2 ml-4"
                  >
                    <Play className="h-4 w-4" />
                    <span>Start Working</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          {timelineData.timeline.timeline.todays_tasks.length === 0 && (
            <div className="text-center py-8 text-secondary-500">
              <CheckCircle className="h-12 w-12 mx-auto mb-3 text-success-500" />
              <p className="font-medium">No tasks scheduled for today!</p>
              <p className="text-sm">Great job staying on track, or check upcoming tasks.</p>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex items-center space-x-2">
            <User className="h-5 w-5 text-secondary-600" />
            <span className="font-medium text-secondary-900">{timelineData.user_info.name}</span>
            <span className="text-secondary-500">•</span>
            <span className="text-secondary-600">{timelineData.user_info.thesis_topic}</span>
          </div>
          
          <div className="flex flex-wrap gap-3">
            <button 
              onClick={onBack}
              className="btn-secondary flex items-center"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Projects
            </button>
            
            <button 
              onClick={handleCreateAndSyncNotion}
              disabled={loadingNotion}
              className="btn-accent flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileText className="h-4 w-4 mr-2" />
              {loadingNotion ? 'Creating...' : (notionWorkspace ? 'Sync to Notion' : 'Create Notion Workspace')}
            </button>
            
            {timelineData.timeline.timeline.daily_assignments && (
              <button 
                onClick={onEmailTest}
                disabled={loadingEmail}
                className="btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Mail className="h-4 w-4 mr-2" />
                {loadingEmail ? 'Sending...' : 'Send Progress Email'}
              </button>
            )}
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
                  href={notionWorkspace.main_page?.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-success-600 hover:text-success-800 text-sm"
                >
                  📄 Main Page
                </a>
                <a 
                  href={notionWorkspace.task_database?.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-success-600 hover:text-success-800 text-sm"
                >
                  📊 Tasks
                </a>
                <a 
                  href={notionWorkspace.milestone_database?.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-success-600 hover:text-success-800 text-sm"
                >
                  🎯 Milestones
                </a>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Timeline Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card text-center">
          <div className="text-2xl font-bold text-primary-600">{timeline.phases.length}</div>
          <p className="text-sm text-secondary-600">Phases</p>
        </div>
        
        <div className="card text-center">
          <div className="text-2xl font-bold text-accent-600">
            {timeline.phases.reduce((total, phase) => total + phase.tasks.length, 0)}
          </div>
          <p className="text-sm text-secondary-600">Total Tasks</p>
        </div>
        
        <div className="card text-center">
          <div className="text-2xl font-bold text-success-600">
            {Math.round(timeline.phases.reduce((total, phase) => total + phase.estimated_hours, 0))}
          </div>
          <p className="text-sm text-secondary-600">Total Hours</p>
        </div>
        
        <div className="card text-center">
          <div className="text-2xl font-bold text-warning-600">
            {Math.ceil((new Date(timelineData.user_info.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))}
          </div>
          <p className="text-sm text-secondary-600">Days Left</p>
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
                        <div key={taskIndex} className="p-4 bg-secondary-50 rounded-lg border border-secondary-200">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-3 flex-1">
                              <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                                taskStatus === 'overdue' ? 'bg-danger-600' :
                                taskStatus === 'today' ? 'bg-warning-600' :
                                taskStatus === 'upcoming' ? 'bg-primary-600' :
                                'bg-secondary-400'
                              }`}>
                                <div className="w-2 h-2 bg-white rounded-full"></div>
                              </div>
                              
                              <div className="flex-1">
                                <div className="flex items-center space-x-3 mb-2">
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
                                
                                <p className="text-sm text-secondary-600 mb-3">{task.description}</p>
                                
                                <div className="flex flex-wrap items-center gap-4 text-sm text-secondary-500">
                                  <div className="flex items-center">
                                    <Calendar className="h-4 w-4 mr-1" />
                                    Due: {format(parseISO(task.due_date), 'MMM dd, yyyy')}
                                  </div>
                                  <div className="flex items-center">
                                    <Clock className="h-4 w-4 mr-1" />
                                    {task.estimated_hours}h
                                  </div>
                                  {task.focus_sessions && (
                                    <div className="flex items-center">
                                      <Target className="h-4 w-4 mr-1" />
                                      {task.focus_sessions} sessions
                                    </div>
                                  )}
                                  {task.assigned_date && (
                                    <div className="flex items-center">
                                      <Calendar className="h-4 w-4 mr-1" />
                                      Assigned: {format(parseISO(task.assigned_date), 'MMM dd')}
                                    </div>
                                  )}
                                </div>
                                
                                {task.deliverable && (
                                  <div className="mt-2 p-2 bg-primary-50 rounded border border-primary-200">
                                    <span className="text-sm font-medium text-primary-800">Deliverable: </span>
                                    <span className="text-sm text-primary-700">{task.deliverable}</span>
                                  </div>
                                )}
                                
                                {task.dependencies && task.dependencies.length > 0 && (
                                  <div className="mt-2">
                                    <span className="text-sm text-secondary-500">Dependencies: </span>
                                    <span className="text-sm text-secondary-700">
                                      {task.dependencies.join(', ')}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                            
                            <button 
                              onClick={() => handleStartWorking(task)}
                              className={`btn-sm flex items-center space-x-2 ml-4 ${
                                taskStatus === 'today' ? 'btn-primary' : 
                                taskStatus === 'overdue' ? 'btn-danger' : 
                                'btn-secondary'
                              }`}
                            >
                              <Play className="h-3 w-3" />
                              <span>Start</span>
                            </button>
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

      {/* Task Chat Modal */}
      {showTaskChat && currentTask && (
        <div className="fixed inset-0 z-50">
          <TaskChat
            task={currentTask}
            onBack={handleBackFromTask}
            onComplete={handleTaskComplete}
            currentProjectId={currentProjectId}
            userName={timelineData.user_info.name}
          />
        </div>
      )}
    </div>
  );
} 