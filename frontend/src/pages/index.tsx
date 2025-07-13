import React, { useState } from 'react';
import { GetServerSideProps } from 'next';
import Layout from '../components/Layout';
import QuestionnaireForm from '../components/QuestionnaireForm';
import TimelineDisplay from '../components/TimelineDisplay';
import { 
  apiService, 
  UserQuestionnaireData, 
  TimelineResponse, 
  HealthCheck 
} from '../services/api';
import { AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

interface HomePageProps {
  initialHealthCheck: HealthCheck;
}

export default function HomePage({ initialHealthCheck }: HomePageProps) {
  const [currentView, setCurrentView] = useState<'questionnaire' | 'timeline'>('questionnaire');
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [userQuestionnaireData, setUserQuestionnaireData] = useState<UserQuestionnaireData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthStatus, setHealthStatus] = useState<HealthCheck>(initialHealthCheck);

  const handleQuestionnaireSubmit = async (data: UserQuestionnaireData) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔄 Submitting questionnaire data:', data);
      
      // Store user questionnaire data for later use
      setUserQuestionnaireData(data);
      
      const response = await apiService.generateTimeline(data);
      console.log('✅ Timeline generated successfully:', response);
      
      setTimelineData(response);
      setCurrentView('timeline');
    } catch (err: any) {
      console.error('❌ Timeline generation failed:', err);
      setError(err.response?.data?.detail || 'Failed to generate timeline. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailTest = async () => {
    try {
      const emailData = {
        email: userQuestionnaireData?.email || 'mouazan99@gmail.com',
        user_name: userQuestionnaireData?.name || timelineData?.user_info?.name
      };
      
      const response = await apiService.testEmail(emailData);
      if (response.success) {
        const source = response.data_source === 'notion' ? 'real Notion data' : 'test data';
        const tasksInfo = response.tasks_today ? ` (${response.tasks_today} tasks today)` : '';
        alert(`✅ Email sent successfully using ${source}${tasksInfo}!`);
      } else {
        alert('❌ Failed to send test email');
      }
    } catch (err) {
      console.error('Email test failed:', err);
      alert('❌ Failed to send test email');
    }
  };

  const refreshHealthStatus = async () => {
    try {
      const health = await apiService.healthCheck();
      setHealthStatus(health);
    } catch (err) {
      console.error('Health check failed:', err);
    }
  };

  const handleStartOver = () => {
    setCurrentView('questionnaire');
    setTimelineData(null);
    setUserQuestionnaireData(null);
    setError(null);
  };

  return (
    <Layout currentStep={currentView}>
      <div className="space-y-8">
        {/* Health Status Banner */}
        <div className={`rounded-lg p-4 flex items-center justify-between ${
          healthStatus.status === 'healthy' 
            ? 'bg-success-50 border border-success-200' 
            : 'bg-warning-50 border border-warning-200'
        }`}>
          <div className="flex items-center space-x-3">
            {healthStatus.status === 'healthy' ? (
              <CheckCircle className="h-5 w-5 text-success-600" />
            ) : (
              <AlertCircle className="h-5 w-5 text-warning-600" />
            )}
            <div>
              <p className={`font-medium ${
                healthStatus.status === 'healthy' ? 'text-success-800' : 'text-warning-800'
              }`}>
                System Status: {healthStatus.status === 'healthy' ? 'All Services Online' : 'Some Services Offline'}
              </p>
              <p className={`text-sm ${
                healthStatus.status === 'healthy' ? 'text-success-600' : 'text-warning-600'
              }`}>
                AI Service: {healthStatus.services.ai_service ? '✅' : '❌'} | 
                Email Service: {healthStatus.services.email_service ? '✅' : '❌'} | 
                Config: {healthStatus.services.config ? '✅' : '❌'}
              </p>
            </div>
          </div>
          <button
            onClick={refreshHealthStatus}
            className="flex items-center space-x-2 text-sm text-secondary-600 hover:text-secondary-900"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-danger-50 border border-danger-200 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <AlertCircle className="h-5 w-5 text-danger-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-danger-800">Error</p>
                <p className="text-danger-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        {currentView === 'questionnaire' && (
          <div>
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-secondary-900 mb-4">
                Welcome to Thesis Helper
              </h1>
              <p className="text-lg text-secondary-600 max-w-2xl mx-auto">
                Get personalized, AI-powered timeline and planning for your thesis project. 
                Answer a few questions to get started with your academic journey.
              </p>
            </div>
            
            <QuestionnaireForm 
              onSubmit={handleQuestionnaireSubmit}
              loading={loading}
            />
          </div>
        )}

        {currentView === 'timeline' && timelineData && (
          <div>
            <div className="mb-6">
              <button
                onClick={handleStartOver}
                className="btn-secondary"
              >
                ← Start Over
              </button>
            </div>
            
            <TimelineDisplay 
              timelineData={timelineData}
              onEmailTest={handleEmailTest}
              userQuestionnaireData={userQuestionnaireData}
            />
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
              <div className="text-center">
                <div className="spinner mx-auto mb-4"></div>
                <h3 className="text-lg font-semibold text-secondary-900 mb-2">
                  Generating Your Timeline
                </h3>
                <p className="text-secondary-600">
                  Our AI is creating a personalized timeline for your thesis. This may take a moment...
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

export const getServerSideProps: GetServerSideProps = async () => {
  try {
    const healthCheck = await apiService.healthCheck();
    
    return {
      props: {
        initialHealthCheck: healthCheck,
      },
    };
  } catch (error) {
    console.error('Failed to fetch health check:', error);
    
    return {
      props: {
        initialHealthCheck: {
          status: 'error',
          timestamp: new Date().toISOString(),
          services: {
            ai_service: false,
            email_service: false,
            config: false,
          },
        },
      },
    };
  }
}; 