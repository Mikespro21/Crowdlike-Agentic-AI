import { useState } from 'react';
import { 
  Home, 
  LayoutDashboard, 
  Users, 
  Brain, 
  TrendingUp, 
  BarChart3, 
  Trophy, 
  Shield, 
  UserCircle,
  Search,
  X
} from 'lucide-react';
import confetti from 'canvas-confetti';

interface Page {
  id: string;
  label: string;
  icon: React.ElementType;
  emoji: string;
}

interface DynamicSidebarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  visible: boolean;
}

const pages: Page[] = [
  { id: 'home', label: 'Home', icon: Home, emoji: '🏠' },
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, emoji: '📊' },
  { id: 'agents', label: 'Agents', icon: Users, emoji: '🤖' },
  { id: 'coach', label: 'Coach', icon: Brain, emoji: '🧠' },
  { id: 'market', label: 'Market', icon: TrendingUp, emoji: '📈' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, emoji: '📉' },
  { id: 'leaderboards', label: 'Leaderboards', icon: Trophy, emoji: '🏆' },
  { id: 'safety', label: 'Safety', icon: Shield, emoji: '🛡️' },
  { id: 'profile', label: 'Profile', icon: UserCircle, emoji: '👤' },
];

export const DynamicSidebar = ({ currentPage, onNavigate, visible }: DynamicSidebarProps) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredPages = pages.filter(page =>
    page.label.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handlePageClick = (page: Page) => {
    // Trigger confetti with the button's emoji
    const canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '9999';
    document.body.appendChild(canvas);

    const myConfetti = confetti.create(canvas, {
      resize: true,
      useWorker: true
    });

    // Create confetti burst with emoji-themed colors
    const colors = getEmojiColors(page.emoji);
    
    myConfetti({
      particleCount: 100,
      spread: 70,
      origin: { x: 0.1, y: 0.5 },
      colors: colors,
      shapes: ['circle', 'square'],
      scalar: 1.2,
    });

    // Clean up after animation
    setTimeout(() => {
      document.body.removeChild(canvas);
    }, 3000);

    onNavigate(page.id);
  };

  const getEmojiColors = (emoji: string): string[] => {
    // Map emojis to color schemes
    const colorMap: Record<string, string[]> = {
      '🏠': ['#3B82F6', '#60A5FA', '#93C5FD'],
      '📊': ['#8B5CF6', '#A78BFA', '#C4B5FD'],
      '🤖': ['#06B6D4', '#22D3EE', '#67E8F9'],
      '🧠': ['#EC4899', '#F472B6', '#F9A8D4'],
      '📈': ['#10B981', '#34D399', '#6EE7B7'],
      '📉': ['#F59E0B', '#FBBF24', '#FCD34D'],
      '🏆': ['#EAB308', '#FACC15', '#FDE047'],
      '🛡️': ['#EF4444', '#F87171', '#FCA5A5'],
      '👤': ['#6366F1', '#818CF8', '#A5B4FC'],
    };
    return colorMap[emoji] || ['#3B82F6', '#8B5CF6', '#EC4899'];
  };

  return (
    <aside
      className={`fixed left-0 top-0 h-screen w-72 bg-white/95 backdrop-blur-sm border-r border-gray-200 shadow-lg transition-transform duration-300 ease-in-out z-50 ${
        visible ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Crowdlike
            </h1>
            <span className="text-xs text-gray-500">v1.7.0</span>
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search pages..."
              className="w-full pl-10 pr-10 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2"
              >
                <X className="w-4 h-4 text-gray-400 hover:text-gray-600" />
              </button>
            )}
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {filteredPages.map((page) => {
            const Icon = page.icon;
            const isActive = currentPage === page.id;

            return (
              <button
                key={page.id}
                onClick={() => handlePageClick(page)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <span className="text-xl">{page.emoji}</span>
                <Icon className="w-5 h-5" />
                <span className="font-medium">{page.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
          <p>Hover left edge to show</p>
          <p>Move right to hide</p>
          <p>Scroll down to hide</p>
        </div>
      </div>
    </aside>
  );
};
