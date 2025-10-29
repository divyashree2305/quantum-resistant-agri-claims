'use client';

/**
 * Activity Context - Tracks and displays system operations
 * Used for demonstrating post-quantum security flow and system processes
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface Activity {
  id: string;
  type: 'handshake' | 'claim_submit' | 'fraud_detection' | 'log_entry' | 'checkpoint' | 'verification' | 'general';
  title: string;
  description: string;
  status: 'pending' | 'completed' | 'error';
  timestamp: string;
  details?: string | Record<string, any>;
}

interface ActivityContextType {
  activities: Activity[];
  addActivity: (activity: Omit<Activity, 'id' | 'timestamp'>) => void;
  updateActivity: (id: string, updates: Partial<Activity>) => void;
  clearActivities: () => void;
}

const ActivityContext = createContext<ActivityContextType | undefined>(undefined);

export function ActivityProvider({ children }: { children: ReactNode }) {
  const [activities, setActivities] = useState<Activity[]>([]);

  const addActivity = useCallback((activity: Omit<Activity, 'id' | 'timestamp'>) => {
    const newActivity: Activity = {
      ...activity,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
    };
    
    setActivities((prev) => [newActivity, ...prev].slice(0, 100)); // Keep last 100 activities
  }, []);

  const updateActivity = useCallback((id: string, updates: Partial<Activity>) => {
    setActivities((prev) =>
      prev.map((activity) =>
        activity.id === id
          ? { ...activity, ...updates }
          : activity
      )
    );
  }, []);

  const clearActivities = useCallback(() => {
    setActivities([]);
  }, []);

  return (
    <ActivityContext.Provider
      value={{
        activities,
        addActivity,
        updateActivity,
        clearActivities,
      }}
    >
      {children}
    </ActivityContext.Provider>
  );
}

export function useActivityLog() {
  const context = useContext(ActivityContext);
  if (context === undefined) {
    throw new Error('useActivityLog must be used within an ActivityProvider');
  }
  return context;
}

