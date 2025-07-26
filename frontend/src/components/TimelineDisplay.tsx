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
    <>
      {/* Task Chat Full Screen View */}
      {showTaskChat && currentTask && (
        <TaskChat
          task={currentTask}
          onBack={handleBackFromTask}
          onComplete={handleTaskComplete}
          currentProjectId={currentProjectId}
          userName={timelineData.user_info.name}
        />
      )}
      
      {/* Timeline View */}
      {!showTaskChat && (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
          <div className="card-modern max-w-6xl mx-auto m-6 p-8 bg-white/95 backdrop-blur-sm">
            {/* Today's Tasks Section - Prominent at top */}
            {timelineData.timeline.timeline.todays_tasks && timelineData.timeline.timeline.todays_tasks.length > 0 && (
              <div className="card-modern border-l-4 border-l-blue-500 bg-gradient-to-r from-blue-50 to-indigo-50 mb-8">
                <div className="p-6">
                  <h2 className="text-2xl font-bold text-gradient mb-2 flex items-center">
                    <CheckSquare className="h-7 w-7 mr-3 text-blue-600" />
                    Today's Tasks ({new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })})
                  </h2>
                  <p className="text-blue-700 mb-6">Focus on these tasks today to stay on track</p>
                  
                  <div className="space-y-4">
                    {timelineData.timeline.timeline.todays_tasks.map((task: TimelineTask, index: number) => (
                      <div key={index} className="card-modern p-6 bg-white border border-blue-200 hover:shadow-lg transition-all duration-200">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-4 mb-3">
                              <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-lg">
                                {index + 1}
                              </div>
                              <div>
                                <h4 className="text-lg font-semibold text-gray-900">{task.title}</h4>
                                <p className="text-gray-600 text-sm">{task.description}</p>
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-6 ml-14 text-sm text-gray-600">
                              <div className="flex items-center">
                                <Clock className="h-4 w-4 mr-2 text-blue-500" />
                                <span>{task.estimated_hours}h ({task.focus_sessions || Math.ceil(task.estimated_hours * 2)} × {Math.floor((task.estimated_hours / (task.focus_sessions || Math.ceil(task.estimated_hours * 2))) * 60)}min sessions)</span>
                              </div>
                              {task.deliverable && (
                                <div className="flex items-center">
                                  <Target className="h-4 w-4 mr-2 text-green-500" />
                                  <span>{task.deliverable}</span>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          <button 
                            onClick={() => handleStartWorking(task)}
                            className="btn-primary flex items-center space-x-2"
                          >
                            <Play className="h-4 w-4" />
                            <span>Start Working</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {timelineData.timeline.timeline.todays_tasks.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-500" />
                      <p className="text-lg font-medium">No tasks scheduled for today!</p>
                      <p className="text-sm">Great job staying on track, or check upcoming tasks.</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="card-modern p-6 mb-8 bg-gradient-to-r from-gray-50 to-blue-50">
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <User className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <span className="font-semibold text-gray-900 text-lg">{timelineData.user_info.name}</span>
                    <p className="text-gray-600 text-sm">{timelineData.user_info.thesis_topic}</p>
                  </div>
                </div>
                
                <div className="flex flex-wrap gap-3">
                  <button 
                    onClick={onBack}
                    className="btn-secondary flex items-center space-x-2"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    <span>Back to Setup</span>
                  </button>
                  
                  {notionWorkspace ? (
                    <button 
                      onClick={handleCreateAndSyncNotion}
                      disabled={loadingNotion}
                      className="btn-success flex items-center space-x-2"
                    >
                      <FileText className="h-4 w-4" />
                      <span>{loadingNotion ? 'Syncing...' : 'Sync to Notion'}</span>
                    </button>
                  ) : (
                    <button 
                      onClick={handleCreateAndSyncNotion}
                      disabled={loadingNotion}
                      className="btn-primary flex items-center space-x-2"
                    >
                      <FileText className="h-4 w-4" />
                      <span>{loadingNotion ? 'Creating...' : 'Create Notion Workspace'}</span>
                    </button>
                  )}
                  
                  {timelineData.timeline.timeline.daily_assignments && (
                    <button 
                      onClick={onEmailTest}
                      disabled={loadingEmail}
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <Mail className="h-4 w-4" />
                      <span>{loadingEmail ? 'Sending...' : 'Send Progress Email'}</span>
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Timeline Phases */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gradient mb-6">📅 Complete Timeline Overview</h2>
              
              {timelineData.timeline.timeline.phases.map((phase, phaseIndex) => {
                const isExpanded = expandedPhases.has(phaseIndex);
                const phaseStatus = getPhaseStatus(phase.start_date, phase.end_date);
                
                return (
                  <div key={phaseIndex} className="card-modern overflow-hidden">
                    <div 
                      className="p-6 cursor-pointer hover:bg-gray-50 transition-colors duration-200"
                      onClick={() => togglePhase(phaseIndex)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${
                            phaseStatus === 'completed' ? 'bg-green-100 text-green-600' :
                            phaseStatus === 'current' ? 'bg-orange-100 text-orange-600' :
                            'bg-gray-100 text-gray-400'
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
                            <h3 className="text-xl font-semibold text-gray-900">
                              Phase {phaseIndex + 1}: {phase.name}
                            </h3>
                            <p className="text-gray-600 mt-1">{phase.description}</p>
                            <div className="flex items-center space-x-6 mt-3 text-sm text-gray-500">
                              <div className="flex items-center">
                                <Calendar className="h-4 w-4 mr-2 text-blue-500" />
                                <span>{format(parseISO(phase.start_date), 'MMM dd')} - {format(parseISO(phase.end_date), 'MMM dd, yyyy')}</span>
                              </div>
                              <div className="flex items-center">
                                <Clock className="h-4 w-4 mr-2 text-green-500" />
                                <span>{phase.estimated_hours} hours</span>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                            phaseStatus === 'completed' ? 'bg-green-100 text-green-800' :
                            phaseStatus === 'current' ? 'bg-orange-100 text-orange-800' :
                            'bg-gray-100 text-gray-600'
                          }`}>
                            {phaseStatus === 'completed' ? 'Completed' :
                             phaseStatus === 'current' ? 'In Progress' :
                             'Upcoming'}
                          </span>
                          
                          {isExpanded ? (
                            <ChevronUp className="h-5 w-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="h-5 w-5 text-gray-400" />
                          )}
                        </div>
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="px-6 pb-6 border-t border-gray-100 bg-gray-50/50">
                        <div className="pt-6 space-y-4">
                                                      {phase.tasks.map((task, taskIndex) => {
                              const taskStatus = getTaskStatus(task.due_date);
                              
                              return (
                                <div key={taskIndex} className="card-modern p-4 bg-white border border-gray-200">
                                  <div className="flex items-start justify-between">
                                    <div className="flex items-start space-x-3 flex-1">
                                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                                        taskStatus === 'today' ? 'bg-blue-100 text-blue-700' :
                                        taskStatus === 'overdue' ? 'bg-red-100 text-red-700' :
                                        taskStatus === 'upcoming' ? 'bg-green-100 text-green-700' :
                                        'bg-gray-100 text-gray-600'
                                      }`}>
                                      {taskIndex + 1}
                                    </div>
                                    
                                    <div className="flex-1 min-w-0">
                                      <h4 className="font-medium text-gray-900">{task.title}</h4>
                                      <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                                      
                                      <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                                        <div className="flex items-center">
                                          <Calendar className="h-4 w-4 mr-1 text-blue-500" />
                                          <span>Due: {format(parseISO(task.due_date), 'MMM dd, yyyy')}</span>
                                        </div>
                                        <div className="flex items-center">
                                          <Clock className="h-4 w-4 mr-1 text-green-500" />
                                          <span>{task.estimated_hours}h</span>
                                        </div>
                                        {task.deliverable && (
                                          <div className="flex items-center">
                                            <Target className="h-4 w-4 mr-1 text-purple-500" />
                                            <span className="truncate max-w-xs">{task.deliverable}</span>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                  
                                  <button 
                                    onClick={() => handleStartWorking(task)}
                                    className="btn-primary ml-4 flex items-center space-x-2"
                                  >
                                    <Play className="h-4 w-4" />
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
          </div>
        </div>
      )}
    </>
  );
} 