// Shared TypeScript types for PADI.AI
// Based on ENG-000-foundations.md database schema

// Student types
export interface Student {
  id: string;
  parent_id: string;
  grade_level: number; // 1-5
  first_name: string;
  last_name: string;
  date_of_birth: Date | null;
  created_at: Date;
  updated_at: Date;
}

// Parent types
export interface Parent {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  school_district: string | null;
  created_at: Date;
  updated_at: Date;
}

// COPPA consent types
export interface ConsentRecord {
  id: string;
  parent_id: string;
  student_id: string | null;
  consent_type: 'data_processing' | 'media_sharing' | 'analytics';
  status: 'pending' | 'granted' | 'revoked';
  ip_address: string | null;
  user_agent: string | null;
  consented_at: Date | null;
  created_at: Date;
  updated_at: Date;
}

// Standards types (Oregon math standards)
export interface Standard {
  id: string;
  standard_code: string; // e.g., "OR.Math.4.NBT.A.1"
  grade_level: number; // 1-5
  domain: string; // e.g., "Number and Operations in Base Ten"
  title: string;
  description: string;
  prerequisites: string[]; // Standard IDs
  created_at: Date;
  updated_at: Date;
}

// Question types
export interface Question {
  id: string;
  standard_id: string;
  question_text: string;
  question_type: 'multiple_choice' | 'numeric' | 'multi_step';
  difficulty: number; // 1-5
  points: number;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

// Multiple choice option
export interface QuestionOption {
  id: string;
  question_id: string;
  option_text: string;
  is_correct: boolean;
  explanation: string | null;
  order: number;
}

// Assessment types
export interface Assessment {
  id: string;
  student_id: string;
  assessment_type: 'diagnostic' | 'practice' | 'assessment';
  version: string;
  status: 'in_progress' | 'completed' | 'abandoned';
  started_at: Date | null;
  completed_at: Date | null;
  total_score: number | null;
  max_score: number | null;
  created_at: Date;
  updated_at: Date;
}

// Assessment item response
export interface AssessmentItem {
  id: string;
  assessment_id: string;
  question_id: string;
  standard_id: string;
  student_answer: string | null;
  is_correct: boolean;
  points_earned: number;
  time_spent_seconds: number | null;
  hint_count: number;
  created_at: Date;
  updated_at: Date;
}

// Skill state (BKT knowledge tracing)
export interface SkillState {
  id: string;
  student_id: string;
  standard_id: string;
  mastery_prob: number; // P(mastered) from 0 to 1
  guess_prob: number; // G
  slip_prob: number; // S
  learning_rate: number; // L
  last_practiced_at: Date | null;
  times_practiced: number;
  created_at: Date;
  updated_at: Date;
}

// Learning plan
export interface LearningPlan {
  id: string;
  student_id: string;
  plan_type: 'remediation' | 'enrichment' | 'grade_progression';
  focus_standards: string[]; // Standard IDs
  priority_level: 'low' | 'medium' | 'high';
  status: 'active' | 'completed' | 'archived';
  generated_at: Date;
  expires_at: Date | null;
  created_at: Date;
  updated_at: Date;
}

// Practice session
export interface PracticeSession {
  id: string;
  student_id: string;
  standard_id: string;
  question_id: string;
  session_type: 'tutoring' | 'practice' | 'assessment';
  llm_model_used: string | null; // e.g., "ollama/qwen2.5:72b"
  status: 'in_progress' | 'completed';
  started_at: Date;
  completed_at: Date | null;
  created_at: Date;
  updated_at: Date;
}

// Audit log (compliance)
export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  metadata: Record<string, unknown> | null;
  created_at: Date;
}

// Common API response types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}
