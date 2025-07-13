import React from 'react';
import { GraduationCap, Brain, Calendar, Mail, Settings } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  currentStep?: string;
}

export default function Layout({ children, currentStep }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-secondary-50 to-primary-50">
      {/* Header */}
      <header className="bg-white shadow-soft border-b border-secondary-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <GraduationCap className="h-8 w-8 text-primary-600 mr-3" />
              <div>
                <h1 className="text-xl font-bold text-secondary-900">Thesis Helper</h1>
                <p className="text-sm text-secondary-600">AI-Powered Academic Planning</p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex space-x-8">
              <NavItem 
                icon={<Brain className="h-4 w-4" />} 
                label="AI Planning" 
                active={currentStep === 'questionnaire' || currentStep === 'timeline'}
              />
              <NavItem 
                icon={<Calendar className="h-4 w-4" />} 
                label="Timeline" 
                active={currentStep === 'timeline'}
              />
              <NavItem 
                icon={<Mail className="h-4 w-4" />} 
                label="Email" 
                active={currentStep === 'email'}
              />
              <NavItem 
                icon={<Settings className="h-4 w-4" />} 
                label="Settings" 
                active={currentStep === 'settings'}
              />
            </nav>

            {/* Status Indicator */}
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-success-500 rounded-full"></div>
              <span className="text-sm text-secondary-600">System Online</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-secondary-100 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <GraduationCap className="h-6 w-6 text-primary-600 mr-2" />
              <span className="text-secondary-600">
                © 2024 Thesis Helper. Empowering academic success with AI.
              </span>
            </div>
            <div className="flex space-x-6">
              <a href="#" className="text-secondary-600 hover:text-primary-600 transition-colors">
                About
              </a>
              <a href="#" className="text-secondary-600 hover:text-primary-600 transition-colors">
                Privacy
              </a>
              <a href="#" className="text-secondary-600 hover:text-primary-600 transition-colors">
                Support
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
}

function NavItem({ icon, label, active = false }: NavItemProps) {
  return (
    <div className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-all duration-200 ${
      active 
        ? 'bg-primary-100 text-primary-700' 
        : 'text-secondary-600 hover:text-primary-600 hover:bg-primary-50'
    }`}>
      {icon}
      <span className="font-medium">{label}</span>
    </div>
  );
} 