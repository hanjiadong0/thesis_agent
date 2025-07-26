import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { ChevronRight, ChevronLeft, User, BookOpen, Clock, Settings, Mail, Loader2, CheckCircle } from 'lucide-react';
import { 
  UserQuestionnaireData, 
  THESIS_FIELDS, 
  PROCRASTINATION_LEVELS, 
  WRITING_STYLES, 
  TIMEZONES,
  AI_PROVIDERS
} from '../services/api';

interface QuestionnaireFormProps {
  onSubmit: (data: UserQuestionnaireData) => void;
  loading?: boolean;
  onBack?: () => void;
}

interface FormData extends UserQuestionnaireData {}

export default function QuestionnaireForm({ onSubmit, loading = false, onBack }: QuestionnaireFormProps) {
  const [currentStep, setCurrentStep] = useState(0);
  
  // Read brainstormed data from session storage
  const getBrainstormedData = () => {
    if (typeof window !== 'undefined') {
      const topic = window.sessionStorage.getItem('brainstormed_topic');
      const description = window.sessionStorage.getItem('brainstormed_description');
      const field = window.sessionStorage.getItem('brainstormed_field') || 'Computer Science';
      
      return {
        thesis_topic: topic || '',
        thesis_description: description || '',
        thesis_field: field
      };
    }
    return {
      thesis_topic: '',
      thesis_description: '',
      thesis_field: 'Computer Science'
    };
  };

  const brainstormedData = getBrainstormedData();
  
  const { register, handleSubmit, formState: { errors }, watch, trigger } = useForm<FormData>({
    defaultValues: {
      // Email and notifications
      email_notifications: true,
      daily_email_time: "08:00",
      timezone: "UTC",
      ai_provider: "ollama",
      
      // Pre-fill with brainstormed data
      thesis_topic: brainstormedData.thesis_topic,
      thesis_description: brainstormedData.thesis_description,
      thesis_field: brainstormedData.thesis_field,
      
      // Schedule defaults
      daily_hours_available: 4,
      preferred_start_time: "09:00",
      preferred_end_time: "17:00", 
      work_days_per_week: 5,
      
      // Work style defaults
      procrastination_level: "medium",
      focus_duration: 60, // 60 minutes (meets >= 15 requirement)
      writing_style: "draft_then_revise"
    }
  });

  const steps = [
    { id: 'personal', title: 'Personal Information', icon: User },
    { id: 'thesis', title: 'Thesis Details', icon: BookOpen },
    { id: 'schedule', title: 'Schedule Preferences', icon: Clock },
    { id: 'settings', title: 'Work Style', icon: Settings },
    { id: 'notifications', title: 'Notifications', icon: Mail }
  ];

  const nextStep = async () => {
    const isValid = await trigger();
    if (isValid && currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const onFormSubmit = (data: FormData) => {
    onSubmit(data);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-300 ${
                index <= currentStep 
                  ? 'bg-primary-600 border-primary-600 text-white' 
                  : 'border-secondary-300 text-secondary-400'
              }`}>
                <step.icon className="h-5 w-5" />
              </div>
              <span className={`ml-3 text-sm font-medium ${
                index <= currentStep ? 'text-primary-600' : 'text-secondary-400'
              }`}>
                {step.title}
              </span>
              {index < steps.length - 1 && (
                <ChevronRight className="h-4 w-4 text-secondary-400 ml-4" />
              )}
            </div>
          ))}
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
        <div className="card-clean">
          {/* Step 1: Personal Information */}
          {currentStep === 0 && (
            <div className="animate-fadeInUp">
              <div className="card-header">
                <h2 className="text-2xl font-bold text-secondary-900">Personal Information</h2>
                <p className="text-secondary-600 mt-1">Let's start with some basic information about you.</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    {...register('name', { required: 'Name is required' })}
                    className="form-input"
                    placeholder="Enter your full name"
                  />
                  {errors.name && <p className="text-danger-600 text-sm mt-1">{errors.name.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Email Address *
                  </label>
                  <input
                    type="email"
                    {...register('email', { 
                      required: 'Email is required',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Invalid email address'
                      }
                    })}
                    className="form-input"
                    placeholder="your.email@university.edu"
                  />
                  {errors.email && <p className="text-danger-600 text-sm mt-1">{errors.email.message}</p>}
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Timezone *
                  </label>
                  <select
                    {...register('timezone', { required: 'Timezone is required' })}
                    className="form-select"
                  >
                    <option value="">Select your timezone</option>
                    {TIMEZONES.map(tz => (
                      <option key={tz} value={tz}>{tz}</option>
                    ))}
                  </select>
                  {errors.timezone && <p className="text-danger-600 text-sm mt-1">{errors.timezone.message}</p>}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Thesis Details */}
          {currentStep === 1 && (
            <div className="animate-fadeInUp">
              <div className="card-header">
                <h2 className="text-2xl font-bold text-secondary-900">Thesis Details</h2>
                <p className="text-secondary-600 mt-1">Tell us about your thesis project.</p>
                {brainstormedData.thesis_topic && (
                  <div className="mt-3 p-3 bg-success-50 border border-success-200 rounded-lg">
                    <div className="flex items-center">
                      <CheckCircle className="h-5 w-5 text-success-600 mr-2" />
                      <p className="text-success-800 text-sm">
                        <strong>Great!</strong> We've pre-filled your thesis details from your brainstorming session. 
                        You can review and edit them below.
                      </p>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Thesis Topic *
                    {brainstormedData.thesis_topic && (
                      <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success-100 text-success-800">
                        Auto-filled from brainstorming
                      </span>
                    )}
                  </label>
                  <input
                    type="text"
                    {...register('thesis_topic', { required: 'Thesis topic is required' })}
                    className={`form-input ${brainstormedData.thesis_topic ? 'border-success-300 bg-success-50' : ''}`}
                    placeholder="e.g., Machine Learning Applications in Climate Change Prediction"
                  />
                  {errors.thesis_topic && <p className="text-danger-600 text-sm mt-1">{errors.thesis_topic.message}</p>}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-2">
                      Academic Field *
                      {brainstormedData.thesis_field && brainstormedData.thesis_field !== 'Computer Science' && (
                        <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success-100 text-success-800">
                          From brainstorming
                        </span>
                      )}
                    </label>
                    <select
                      {...register('thesis_field', { required: 'Academic field is required' })}
                      className={`form-select ${brainstormedData.thesis_field && brainstormedData.thesis_field !== 'Computer Science' ? 'border-success-300 bg-success-50' : ''}`}
                    >
                      <option value="">Select your field</option>
                      {THESIS_FIELDS.map(field => (
                        <option key={field} value={field}>{field}</option>
                      ))}
                    </select>
                    {errors.thesis_field && <p className="text-danger-600 text-sm mt-1">{errors.thesis_field.message}</p>}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-2">
                      Deadline *
                    </label>
                    <input
                      type="date"
                      {...register('thesis_deadline', { required: 'Deadline is required' })}
                      className="form-input"
                    />
                    {errors.thesis_deadline && <p className="text-danger-600 text-sm mt-1">{errors.thesis_deadline.message}</p>}
                  </div>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Thesis Description *
                    {brainstormedData.thesis_description && (
                      <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success-100 text-success-800">
                        Auto-filled from brainstorming
                      </span>
                    )}
                  </label>
                  <textarea
                    rows={6}
                    {...register('thesis_description', { required: 'Description is required' })}
                    className={`form-textarea w-full ${brainstormedData.thesis_description ? 'border-success-300 bg-success-50' : ''}`}
                    placeholder="Provide a detailed description of your thesis project, including objectives, methodology, and expected outcomes..."
                  />
                  {errors.thesis_description && <p className="text-danger-600 text-sm mt-1">{errors.thesis_description.message}</p>}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Schedule Preferences */}
          {currentStep === 2 && (
            <div className="animate-fadeInUp">
              <div className="card-header">
                <h2 className="text-2xl font-bold text-secondary-900">Schedule Preferences</h2>
                <p className="text-secondary-600 mt-1">Help us understand your availability and work schedule.</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Daily Hours Available *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="16"
                    {...register('daily_hours_available', { 
                      required: 'Daily hours is required',
                      min: { value: 1, message: 'At least 1 hour required' },
                      max: { value: 16, message: 'Maximum 16 hours allowed' }
                    })}
                    className="form-input"
                    placeholder="8"
                  />
                  {errors.daily_hours_available && <p className="text-danger-600 text-sm mt-1">{errors.daily_hours_available.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Work Days per Week *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="7"
                    {...register('work_days_per_week', { 
                      required: 'Work days is required',
                      min: { value: 1, message: 'At least 1 day required' },
                      max: { value: 7, message: 'Maximum 7 days allowed' }
                    })}
                    className="form-input"
                    placeholder="5"
                  />
                  {errors.work_days_per_week && <p className="text-danger-600 text-sm mt-1">{errors.work_days_per_week.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Preferred Start Time *
                  </label>
                  <input
                    type="time"
                    {...register('preferred_start_time', { required: 'Start time is required' })}
                    className="form-input"
                  />
                  {errors.preferred_start_time && <p className="text-danger-600 text-sm mt-1">{errors.preferred_start_time.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Preferred End Time *
                  </label>
                  <input
                    type="time"
                    {...register('preferred_end_time', { required: 'End time is required' })}
                    className="form-input"
                  />
                  {errors.preferred_end_time && <p className="text-danger-600 text-sm mt-1">{errors.preferred_end_time.message}</p>}
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Work Style */}
          {currentStep === 3 && (
            <div className="animate-fadeInUp">
              <div className="card-header">
                <h2 className="text-2xl font-bold text-secondary-900">Work Style</h2>
                <p className="text-secondary-600 mt-1">Tell us about your working preferences and habits.</p>
              </div>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Focus Duration (minutes) *
                  </label>
                  <input
                    type="number"
                    min="15"
                    max="240"
                    {...register('focus_duration', { 
                      required: 'Focus duration is required',
                      min: { value: 15, message: 'Minimum 15 minutes' },
                      max: { value: 240, message: 'Maximum 240 minutes' }
                    })}
                    className="form-input"
                    placeholder="120"
                  />
                  <p className="text-sm text-secondary-500 mt-1">How long can you focus on a task without a break?</p>
                  {errors.focus_duration && <p className="text-danger-600 text-sm mt-1">{errors.focus_duration.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Procrastination Level *
                  </label>
                  <select
                    {...register('procrastination_level', { required: 'Procrastination level is required' })}
                    className="form-select"
                  >
                    <option value="">Select your level</option>
                    {PROCRASTINATION_LEVELS.map(level => (
                      <option key={level.value} value={level.value}>{level.label}</option>
                    ))}
                  </select>
                  {errors.procrastination_level && <p className="text-danger-600 text-sm mt-1">{errors.procrastination_level.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Writing Style *
                  </label>
                  <select
                    {...register('writing_style', { required: 'Writing style is required' })}
                    className="form-select"
                  >
                    <option value="">Select your style</option>
                    {WRITING_STYLES.map(style => (
                      <option key={style.value} value={style.value}>{style.label}</option>
                    ))}
                  </select>
                  {errors.writing_style && <p className="text-danger-600 text-sm mt-1">{errors.writing_style.message}</p>}
                </div>
              </div>
            </div>
          )}

          {/* Step 5: Notifications & AI Settings */}
          {currentStep === 4 && (
            <div className="animate-fadeInUp">
              <div className="card-header">
                <h2 className="text-2xl font-bold text-secondary-900">Notifications & AI Settings</h2>
                <p className="text-secondary-600 mt-1">Configure your email preferences and choose your AI assistant.</p>
              </div>
              
              <div className="space-y-8">
                {/* AI Provider Selection */}
                <div>
                  <label className="block text-lg font-medium text-secondary-900 mb-4">
                    Choose Your AI Assistant *
                  </label>
                  <div className="space-y-4">
                    {AI_PROVIDERS.map((provider) => (
                      <div key={provider.value} className="relative">
                        <input
                          type="radio"
                          id={`ai_provider_${provider.value}`}
                          value={provider.value}
                          {...register('ai_provider', { required: 'Please select an AI provider' })}
                          className="sr-only"
                        />
                        <label
                          htmlFor={`ai_provider_${provider.value}`}
                          className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                            watch('ai_provider') === provider.value
                              ? 'border-primary-500 bg-primary-50'
                              : 'border-secondary-200 hover:border-secondary-300'
                          }`}
                        >
                          <div className={`flex-shrink-0 w-4 h-4 rounded-full border-2 mt-1 mr-3 ${
                            watch('ai_provider') === provider.value
                              ? 'border-primary-500 bg-primary-500'
                              : 'border-secondary-300'
                          }`}>
                            {watch('ai_provider') === provider.value && (
                              <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                            )}
                          </div>
                          <div>
                            <h4 className="font-medium text-secondary-900">{provider.label}</h4>
                            <p className="text-sm text-secondary-600 mt-1">{provider.description}</p>
                            {provider.value === 'ollama' && (
                              <p className="text-xs text-primary-600 mt-2 font-medium">
                                ✨ Recommended: Free, private, and no API keys required!
                              </p>
                            )}
                          </div>
                        </label>
                      </div>
                    ))}
                  </div>
                  {errors.ai_provider && <p className="text-danger-600 text-sm mt-2">{errors.ai_provider.message}</p>}
                </div>

                {/* Email Notifications */}
                <div className="border-t border-secondary-200 pt-6">
                  <h3 className="text-lg font-medium text-secondary-900 mb-4">Email Notifications</h3>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="email_notifications"
                      {...register('email_notifications')}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
                    />
                    <label htmlFor="email_notifications" className="ml-3 block text-sm font-medium text-secondary-700">
                      Enable daily email notifications
                    </label>
                  </div>

                  {watch('email_notifications') && (
                    <div className="ml-7 mt-4 space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-secondary-700 mb-2">
                          Daily Email Time *
                        </label>
                        <input
                          type="time"
                          {...register('daily_email_time', { 
                            required: watch('email_notifications') ? 'Email time is required' : false 
                          })}
                          className="form-input"
                        />
                        {errors.daily_email_time && <p className="text-danger-600 text-sm mt-1">{errors.daily_email_time.message}</p>}
                      </div>
                    </div>
                  )}

                  <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 mt-4">
                    <h4 className="font-medium text-primary-900 mb-2">What you'll receive:</h4>
                    <ul className="text-sm text-primary-800 space-y-1">
                      <li>• Daily progress updates and motivational messages</li>
                      <li>• Task reminders and deadline alerts</li>
                      <li>• Weekly progress summaries</li>
                      <li>• Productivity tips and academic advice</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t border-secondary-200">
            <div className="flex gap-3">
              {onBack && currentStep === 0 && (
                <button
                  type="button"
                  onClick={onBack}
                  className="btn-secondary flex items-center"
                >
                  <ChevronLeft className="h-4 w-4 mr-2" />
                  Back to Brainstorming
                </button>
              )}
              
              <button
                type="button"
                onClick={prevStep}
                disabled={currentStep === 0}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                style={{ display: currentStep === 0 ? 'none' : 'flex' }}
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                Previous
              </button>
            </div>

            {currentStep < steps.length - 1 ? (
              <button
                type="button"
                onClick={nextStep}
                className="btn-primary flex items-center"
              >
                Next
                <ChevronRight className="h-4 w-4 ml-2" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={loading}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating Timeline...
                  </>
                ) : (
                  <>
                    Generate Timeline
                    <ChevronRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
} 