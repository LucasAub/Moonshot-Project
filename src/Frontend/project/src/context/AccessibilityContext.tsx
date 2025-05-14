import React, { createContext, useState, useContext, ReactNode } from 'react';

// Define the types for our context
type AccessibilityContextType = {
  announceMessage: (message: string, politeness?: 'polite' | 'assertive') => void;
  clearAnnouncements: () => void;
  politeAnnouncement: string;
  assertiveAnnouncement: string;
};

// Create the context with default values
const AccessibilityContext = createContext<AccessibilityContextType>({
  announceMessage: () => {},
  clearAnnouncements: () => {},
  politeAnnouncement: '',
  assertiveAnnouncement: '',
});

// Custom hook to use the accessibility context
export const useAccessibility = () => useContext(AccessibilityContext);

// Provider component
type AccessibilityProviderProps = {
  children: ReactNode;
};

export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({ children }) => {
  const [politeAnnouncement, setPoliteAnnouncement] = useState('');
  const [assertiveAnnouncement, setAssertiveAnnouncement] = useState('');

  // Function to announce messages to screen readers
  const announceMessage = (message: string, politeness: 'polite' | 'assertive' = 'polite') => {
    if (politeness === 'assertive') {
      setAssertiveAnnouncement(message);
    } else {
      setPoliteAnnouncement(message);
    }
    
    // Clear announcements after a delay to prevent repeated announcements
    setTimeout(() => {
      if (politeness === 'assertive') {
        setAssertiveAnnouncement('');
      } else {
        setPoliteAnnouncement('');
      }
    }, 3000);
  };

  // Function to clear all announcements
  const clearAnnouncements = () => {
    setPoliteAnnouncement('');
    setAssertiveAnnouncement('');
  };

  return (
    <AccessibilityContext.Provider
      value={{
        announceMessage,
        clearAnnouncements,
        politeAnnouncement,
        assertiveAnnouncement,
      }}
    >
      {children}
      {/* These hidden divs will be read by screen readers */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        data-testid="polite-announcement"
      >
        {politeAnnouncement}
      </div>
      <div
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
        data-testid="assertive-announcement"
      >
        {assertiveAnnouncement}
      </div>
    </AccessibilityContext.Provider>
  );
};