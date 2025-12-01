
export interface PlanningItem {
  id?: string; // Unique identifier for tracking/editing
  title: string;
  description: string;
  materialsNeeded: string[];
  steps: string[];
  scriptureReference: string;
  suggestedDuration: string;
  difficultyLevel: 'Low' | 'Medium' | 'High';
  estimatedCost: 'Free' | 'Low' | 'Medium' | 'High';
  roles?: string[]; // For execution plans
  assignedTeamMembers?: string[]; // Specific people assigned
  assignedDate?: string; // YYYY-MM-DD
  savedAt?: number; // Timestamp when saved
  notes?: string; // User notes
  recurrence?: 'None' | 'Weekly' | 'Monthly';
}

export enum AppView {
  DASHBOARD = 'DASHBOARD',
  PLANNING = 'PLANNING',
  IDEAS = 'IDEAS',
  SPIRITUAL = 'SPIRITUAL',
  EXECUTION = 'EXECUTION',
  COMMUNITY = 'COMMUNITY',
  SAVED = 'SAVED',
  CALENDAR = 'CALENDAR',
  PROMOTION = 'PROMOTION',
  MEDIA = 'MEDIA',
}

export interface GeneratedResponse {
  items: PlanningItem[];
}

export interface MediaItem {
  id: string;
  title: string;
  content: string;
  type: 'Poster' | 'Script' | 'Caption' | 'WhatsApp' | string;
  category?: string; // For folder/theme organization
  createdAt: number;
}
