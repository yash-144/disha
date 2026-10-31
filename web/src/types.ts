export type ViewMode = 
  | 'landing' 
  | 'courses' 
  | 'live-classes' 
  | 'blogs' 
  | 'about' 
  | 'contact' 
  | 'dashboard';

export type DashboardTab = 
  | 'overview' 
  | 'courses-list' 
  | 'all-courses' 
  | 'add-course' 
  | 'management' 
  | 'all-classes' 
  | 'add-class' 
  | 'schedule' 
  | 'cases'
  | 'roster' 
  | 'quizzes' 
  | 'gradebook' 
  | 'resources' 
  | 'settings';

export interface Course {
  id: string;
  title: string;
  category: 'web' | 'data' | 'design' | 'cloud' | 'business';
  categoryLabel: string;
  level: 'Beginner' | 'Intermediate' | 'Advanced' | 'All Levels';
  duration: string;
  lecturesCount: number;
  desc: string;
  price: string;
  originalPrice: string;
  rating: number;
  reviewsCount: string;
  badge?: string;
  badgeColor?: string;
  instructorName: string;
  instructorTitle: string;
  instructorAvatar: string;
  iconName: string;
  accentBg: string;
  modules: {
    title: string;
    duration: string;
    lessons: string[];
  }[];
  prerequisites: string[];
}

export interface LiveSession {
  id: string;
  title: string;
  instructor: string;
  topic: string;
  timeString: string;
  isLiveNow: boolean;
  viewersCount: number;
  duration: string;
  zoomUrl?: string;
}

export interface ClassItem {
  id: string;
  name: string;
  code: string;
  instructor: string;
  accessCode: string;
  term: string;
  activeStudents: number;
  createdAt: string;
  subject: string;
  color: string;
}

export interface StudentRecord {
  id: string;
  name: string;
  email: string;
  avatar: string;
  status: 'Present' | 'Late' | 'Absent';
  attendanceRate: number;
  quizScore: number;
  lastActive: string;
}

export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

export interface BlogPost {
  id: string;
  title: string;
  excerpt: string;
  content: string[];
  tag: string;
  tagBg: string;
  date: string;
  readTime: string;
  img: string;
  author: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  time: string;
  type: 'alert' | 'success' | 'info';
  read: boolean;
}

export interface ToastMessage {
  id: string;
  title: string;
  message?: string;
  type: 'success' | 'info' | 'warning' | 'error';
}
