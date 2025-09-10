import { useState } from 'react';
import { User } from 'lucide-react';
import { Button } from '../ui/Button';
import { ThemeToggle } from '../ui/ThemeToggle';
import { SettingsModal } from './SettingsModal';

interface ProfileData {
  name: string;
  email: string;
  dateOfBirth: string;
}

export function Header() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [profileData, setProfileData] = useState<ProfileData>({
    name: 'John Doe',
    email: 'john.doe@example.com',
    dateOfBirth: '1990-01-01'
  });

  const handleProfileUpdate = (updatedProfile: ProfileData) => {
    setProfileData(updatedProfile);
  };

  return (
    <>
      {/* Floating container in top-right */}
      <div className="fixed top-3 right-3 flex items-center gap-2 z-50">
        {/* Theme Toggle - smaller */}
        <div className="scale-90">
          <ThemeToggle />
        </div>

        {/* User Profile - smaller */}
        <Button 
          variant="ghost" 
          className="flex items-center"
          onClick={() => setIsSettingsOpen(true)}
        >
          <div className="w-7 h-7 bg-blue-600 dark:bg-blue-500 rounded-full flex items-center justify-center shadow-md">
            <User className="w-3.5 h-3.5 text-white" />
          </div>
        </Button>
      </div>

      {/* Settings Modal */}
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)}
        profileData={profileData}
        onProfileUpdate={handleProfileUpdate}
      />
    </>
  );
}
