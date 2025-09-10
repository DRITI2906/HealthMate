import { 
  Heart, 
  Brain, 
  Shield, 
  Zap, 
  ArrowRight, 
  Activity,
  MessageSquare
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/Button';
import { SimpleThemeToggle } from '../ui/ThemeToggle';

const features = [
  {
    icon: <Brain className="w-8 h-8" />,
    title: 'AI-Powered Health Insights',
    description: 'Get personalized health recommendations powered by advanced machine learning algorithms.',
    color: 'from-purple-500 to-pink-500'
  },
  {
    icon: <MessageSquare className="w-8 h-8" />,
    title: 'Multi-Agent AI Assistant',
    description: 'Chat with specialized AI agents for different health concerns - from symptoms to nutrition.',
    color: 'from-gray-500 to-gray-600'
  },
  {
    icon: <Activity className="w-8 h-8" />,
    title: 'Real-Time Health Monitoring',
    description: 'Track vital signs, medications, and health metrics with intelligent trend analysis.',
    color: 'from-green-500 to-emerald-500'
  },
  {
    icon: <Shield className="w-8 h-8" />,
    title: 'Secure & Private',
    description: 'Your health data is encrypted and protected with enterprise-grade security.',
    color: 'from-red-500 to-orange-500'
  }
];

export function LandingPage() {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 transition-colors duration-200">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm border-b border-gray-100 dark:border-gray-700 z-50 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-green-500 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-800 dark:text-gray-100">HealthAI</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-600 hover:text-gray-800 dark:text-gray-300 dark:hover:text-white transition-colors">Features</a>
            </div>
            
            <div className="flex items-center gap-4">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => navigate('/signin')}
              >
                Sign In
              </Button>
              <SimpleThemeToggle />
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-24 pb-16 bg-gradient-to-br from-blue-100 via-indigo-50 to-emerald-100 dark:from-blue-900 dark:via-indigo-900 dark:to-emerald-900 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-200 text-blue-800 dark:bg-blue-700 dark:text-blue-200 rounded-full text-sm font-medium transition-colors duration-200 shadow-md">
                  <Zap className="w-4 h-4" />
                  Powered by Advanced AI
                </div>
                <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 dark:text-gray-100 leading-tight">
                  Your AI-Powered
                  <span className="bg-gradient-to-r from-blue-600 to-emerald-600 bg-clip-text text-transparent"> Health Companion</span>
                </h1>
                <p className="text-xl text-gray-700 dark:text-gray-200 leading-relaxed">
                  Experience the future of healthcare with our multi-agent AI system. Get personalized health insights, 
                  symptom analysis, and 24/7 medical guidance powered by cutting-edge technology.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Button size="lg" className="group bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-700 hover:to-emerald-700 text-white shadow-lg hover:shadow-xl transition-all duration-300" onClick={() => navigate('/signup')}>
                  Start Your Health Journey
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
              </div>
            </div>
            
            {/* Hero card remains unchanged */}
            <div className="relative">
              {/* ...Hero card code... */}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Revolutionizing Healthcare with AI
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              Our advanced AI system combines multiple specialized agents to provide comprehensive 
              health management tailored to your unique needs.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="group p-8 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 hover:shadow-xl transition-all duration-300">
                <div className={`w-16 h-16 bg-gradient-to-br ${feature.color} rounded-2xl flex items-center justify-center text-white mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  {feature.icon}
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{feature.title}</h3>
                <p className="text-gray-600 dark:text-gray-300 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Technology Showcase */}
      <section className="py-20 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-gray-800 dark:to-blue-900/30">
        {/* ...AI Technology Showcase content remains unchanged... */}
      </section>
    </div>
  );
}


