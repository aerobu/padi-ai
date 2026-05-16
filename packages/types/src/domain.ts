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

// Consent types
export interface ConsentInitiateRequest {
  consent_type: string;
  student_display_name: string;
  acknowledgements: string[];
}

export interface ConsentInitiateResponse {
  consent_id: string;
  status: "pending";
  verification_method: string;
  email_sent_to: string;
  expires_at: Date;
}

export interface ConsentConfirmRequest {
  token: string;
}

export interface ConsentConfirmResponse {
  consent_id: string;
  status: "active";
  confirmed_at: Date;
  expires_at: Date;
}

export interface ConsentStatusResponse {
  has_active_consent: boolean;
  consent_records: ConsentRecordSummary[];
}

export interface ConsentRecordSummary {
  consent_id: string;
  consent_type: string;
  status: "pending" | "active" | "revoked" | "expired";
  initiated_at: Date;
  confirmed_at: Date | null;
  expires_at: Date | null;
}

// Assessment types
export interface AssessmentStartRequest {
  student_id: string;
  assessment_type: "diagnostic";
}

export interface AssessmentStartResponse {
  assessment_id: string;
  session_id: string;
  student_id: string;
  assessment_type: "diagnostic";
  target_question_count: number;
  status: "in_progress";
  started_at: Date;
}

export interface QuestionPresentation {
  question_id: string;
  question_number: number;
  standard_domain: string;
  stem: string;
  stem_image_url: string | null;
  options: OptionPresentation[];
  question_type: "multiple_choice" | "numeric" | "multi_step";
}

export interface OptionPresentation {
  key: string; // A, B, C, D
  text: string;
  image_url: string | null;
}

export interface AssessmentProgress {
  questions_answered: number;
  target_total: number;
  domains_covered: Record<string, number>;
  estimated_time_remaining_min: number;
}

export interface NextQuestionResponse {
  question: QuestionPresentation | null;
  progress: AssessmentProgress;
  should_end: boolean;
  end_reason: "all_standards_covered" | "max_questions_reached" | null;
}

export interface ResponseSubmission {
  question_id: string;
  selected_answer: string;
  time_spent_ms: number;
  client_timestamp: Date;
}

export interface ResponseSubmissionResponse {
  is_correct: boolean;
  correct_answer: string | null;
  explanation: string | null;
  progress: AssessmentProgress;
}

export interface CompleteAssessmentResponse {
  assessment_id: string;
  status: "completed";
  total_questions: number;
  total_correct: number;
  overall_score: number;
  duration_minutes: number;
  completed_at: Date;
  results_url: string;
}

export interface DomainResult {
  domain_code: string;
  domain_name: string;
  questions_count: number;
  correct_count: number;
  score: number;
  classification: "below_par" | "on_par" | "above_par";
}

export interface SkillStateResult {
  standard_code: string;
  standard_title: string;
  p_mastery: number;
  mastery_level: "low" | "medium" | "high";
  questions_attempted: number;
  questions_correct: number;
}

export interface GapAnalysis {
  strengths: string[];
  on_track: string[];
  needs_work: string[];
  recommended_focus_order: string[];
}

export interface AssessmentResultsResponse {
  assessment_id: string;
  student_name: string;
  assessment_type: "diagnostic";
  completed_at: Date;
  duration_minutes: number;
  overall_score: number;
  total_questions: number;
  total_correct: number;
  overall_classification: "below_par" | "on_par" | "above_par";
  domain_results: DomainResult[];
  skill_states: SkillStateResult[];
  gap_analysis: GapAnalysis;
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
