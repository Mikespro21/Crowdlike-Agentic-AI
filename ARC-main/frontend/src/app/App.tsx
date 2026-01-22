import { useState, useEffect } from 'react';
import { DynamicSidebar } from '@/app/components/DynamicSidebar';
import { Home } from '@/app/pages/Home';
import { Dashboard } from '@/app/pages/Dashboard';
import { Agents } from '@/app/pages/Agents';
import { Coach } from '@/app/pages/Coach';
import { Market } from '@/app/pages/Market';
import { Analytics } from '@/app/pages/Analytics';
import { Leaderboards } from '@/app/pages/Leaderboards';
import { Safety } from '@/app/pages/Safety';
import { Profile } from '@/app/pages/Profile';

const App = () => {
  const [currentPage, setCurrentPage] = useState('home');
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [mouseX, setMouseX] = useState(0);
  const [prevScrollY, setPrevScrollY] = useState(0);

  // Mouse tracking for left/right edge reveal
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      
      // Show sidebar when mouse is near left edge
      if (e.clientX < 50) {
        setSidebarVisible(true);
      }
      // Hide sidebar when mouse moves right
      else if (e.clientX > 300 && sidebarVisible) {
        setSidebarVisible(false);
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [sidebarVisible]);

  // Auto-hide on scroll
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > prevScrollY && currentScrollY > 100) {
        // Scrolling down - hide sidebar
        setSidebarVisible(false);
      } else if (currentScrollY < prevScrollY) {
        // Scrolling up - show sidebar
        setSidebarVisible(true);
      }
      
      setPrevScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [prevScrollY]);

  const renderPage = () => {
    switch (currentPage) {
      case 'home': return <Home />;
      case 'dashboard': return <Dashboard />;
      case 'agents': return <Agents />;
      case 'coach': return <Coach />;
      case 'market': return <Market />;
      case 'analytics': return <Analytics />;
      case 'leaderboards': return <Leaderboards />;
      case 'safety': return <Safety />;
      case 'profile': return <Profile />;
      default: return <Home />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <DynamicSidebar 
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        visible={sidebarVisible}
      />
      
      <main 
        className="transition-all duration-300 ease-in-out"
        style={{
          marginLeft: sidebarVisible ? '280px' : '0px'
        }}
      >
        <div className="max-w-7xl mx-auto px-6 py-8">
          {renderPage()}
        </div>
      </main>
    </div>
  );
};

export default App;
