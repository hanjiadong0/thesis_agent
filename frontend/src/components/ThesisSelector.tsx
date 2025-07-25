import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Calendar, 
  User, 
  Clock, 
  Plus, 
  ArrowRight, 
  Trash2, 
  AlertCircle,
  CheckCircle 
} from 'lucide-react';
import { getThesisProjects, deactivateThesisProject, type ThesisProject } from '../services/api';

interface ThesisSelectorProps {
  onContinueThesis: (project: ThesisProject) => void;
  onStartNew: () => void;
  loading?: boolean;
}

export default function ThesisSelector({ onContinueThesis, onStartNew, loading = false }: ThesisSelectorProps) {
  const [projects, setProjects] = useState<ThesisProject[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingProject, setDeletingProject] = useState<number | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      const response = await getThesisProjects();
      if (response.success) {
        setProjects(response.projects);
      } else {
        setError('Failed to load thesis projects');
      }
    } catch (err) {
      console.error('Error loading projects:', err);
      setError('Failed to load thesis projects');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteProject = async (projectId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this thesis project? This action cannot be undone.')) {
      return;
    }

    try {
      setDeletingProject(projectId);
      const response = await deactivateThesisProject(projectId);
      if (response.success) {
        setProjects(projects.filter(p => p.id !== projectId));
      } else {
        alert('Failed to delete project');
      }
    } catch (err) {
      console.error('Error deleting project:', err);
      alert('Failed to delete project');
    } finally {
      setDeletingProject(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getDaysRemaining = (deadline: string) => {
    const days = Math.ceil((new Date(deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
    return days;
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your thesis projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <BookOpen className="h-16 w-16 text-blue-600 mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Thesis Helper</h1>
          <p className="text-xl text-gray-600">Welcome back! Choose how you'd like to proceed</p>
        </div>

        {error && (
          <div className="mb-8 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-8">
          {/* Start New Thesis */}
          <div className="bg-white rounded-lg shadow-lg p-8 border-2 border-transparent hover:border-blue-500 transition-all duration-200">
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <Plus className="h-8 w-8 text-blue-600" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Start New Thesis</h2>
              <p className="text-gray-600 mb-6">Begin a fresh thesis project with AI-powered planning and timeline generation</p>
              <button
                onClick={onStartNew}
                disabled={loading}
                className="btn-primary w-full flex items-center justify-center"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <>
                    Get Started
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Continue Existing */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="text-center mb-6">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Continue Existing</h2>
              <p className="text-gray-600">Pick up where you left off with your saved thesis projects</p>
            </div>

            {projects.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">No saved thesis projects found.</p>
                <p className="text-sm text-gray-400 mt-2">Start your first thesis project above!</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {projects.map((project) => {
                  const daysRemaining = getDaysRemaining(project.thesis_deadline);
                  const progressColor = getProgressColor(project.completion_percentage);
                  
                  return (
                    <div
                      key={project.id}
                      className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors relative group"
                      onClick={() => onContinueThesis(project)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                            {project.thesis_topic}
                          </h3>
                          
                          <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 mb-3">
                            <div className="flex items-center">
                              <User className="h-4 w-4 mr-1" />
                              {project.user_name}
                            </div>
                            <div className="flex items-center">
                              <BookOpen className="h-4 w-4 mr-1" />
                              {project.thesis_field}
                            </div>
                            <div className="flex items-center">
                              <Calendar className="h-4 w-4 mr-1" />
                              Due {formatDate(project.thesis_deadline)}
                            </div>
                            <div className="flex items-center">
                              <Clock className="h-4 w-4 mr-1" />
                              {daysRemaining > 0 ? `${daysRemaining} days left` : 'Overdue'}
                            </div>
                          </div>

                          {/* Progress Bar */}
                          <div className="mb-2">
                            <div className="flex justify-between text-xs text-gray-600 mb-1">
                              <span>Progress</span>
                              <span className={progressColor}>{project.completion_percentage}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${project.completion_percentage}%` }}
                              ></div>
                            </div>
                          </div>

                          <div className="text-xs text-gray-500">
                            Created {formatDate(project.created_at)}
                            {project.notion_workspace_url && (
                              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-800">
                                Notion Connected
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Delete Button */}
                        <button
                          onClick={(e) => handleDeleteProject(project.id, e)}
                          disabled={deletingProject === project.id}
                          className="ml-4 p-2 text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-all duration-200"
                          title="Delete thesis project"
                        >
                          {deletingProject === project.id ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <div className="text-center mt-12 text-sm text-gray-500">
          <p>Your thesis projects are saved locally and can be resumed anytime</p>
        </div>
      </div>
    </div>
  );
} 