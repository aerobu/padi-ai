/**
 * API client for PADI.AI.
 *
 * Attaches an Authorization: Bearer <token> header to every request. The
 * token is obtained via `getAccessToken()`, which reads from the in-memory
 * session cache populated by the Auth0 callback route. Fix C-11
 * (2026-05-16 review): the previous client relied on cookies + credentials:
 * "include" while the backend uses HTTPBearer auth — so every protected
 * request was 401-ing.
 */

import { getAccessToken } from "./auth-token";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiError {
  code: string;
  message: string;
}

export class ApiRequestError extends Error {
  public readonly status: number;
  public readonly code: string;
  constructor(message: string, status: number, code: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = await getAccessToken();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) ?? {}),
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      if (typeof window !== "undefined") {
        window.location.assign("/login");
      }
      throw new ApiRequestError("Unauthenticated", 401, "UNAUTHENTICATED");
    }

    if (!response.ok) {
      const payload = await response.json().catch(() => ({
        error: { code: "API_ERROR", message: "An API error occurred" },
      }));
      throw new ApiRequestError(
        payload.error?.message ?? "API request failed",
        response.status,
        payload.error?.code ?? "API_ERROR"
      );
    }

    return response.json() as Promise<T>;
  }

  // --- Consent ---
  async initiateConsent(data: {
    student_display_name: string;
    acknowledgements: string[];
  }): Promise<any> {
    return this.request("/api/v1/consent/initiate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async confirmConsent(token: string): Promise<any> {
    return this.request("/api/v1/consent/confirm", {
      method: "POST",
      body: JSON.stringify({ token }),
    });
  }

  async getConsentStatus(): Promise<any> {
    return this.request("/api/v1/consent/status");
  }

  // --- Students ---
  async createStudent(data: {
    display_name: string;
    grade_level: number;
    avatar_id?: string;
    birth_year?: number;
  }): Promise<any> {
    return this.request("/api/v1/students", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getStudent(studentId: string): Promise<any> {
    return this.request(`/api/v1/students/${studentId}`);
  }

  async updateStudent(
    studentId: string,
    data: { display_name?: string; avatar_id?: string; grade_level?: number }
  ): Promise<any> {
    return this.request(`/api/v1/students/${studentId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async listStudents(): Promise<any[]> {
    return this.request("/api/v1/students");
  }

  // --- Standards ---
  async listStandards(grade?: number, domain?: string): Promise<any> {
    const params = new URLSearchParams();
    if (grade) params.append("grade", grade.toString());
    if (domain) params.append("domain", domain);
    return this.request(`/api/v1/standards?${params}`);
  }

  async getStandard(standardCode: string): Promise<any> {
    return this.request(`/api/v1/standards/${standardCode}`);
  }

  // --- Assessment ---
  async startAssessment(
    studentId: string,
    assessmentType: "diagnostic" = "diagnostic"
  ): Promise<any> {
    return this.request("/api/v1/assessments", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, assessment_type: assessmentType }),
    });
  }

  async getNextQuestion(assessmentId: string): Promise<any> {
    return this.request(`/api/v1/assessments/${assessmentId}/next-question`);
  }

  async submitResponse(
    assessmentId: string,
    data: { question_id: string; selected_answer: string; time_spent_ms: number }
  ): Promise<any> {
    return this.request(`/api/v1/assessments/${assessmentId}/responses`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async completeAssessment(assessmentId: string): Promise<any> {
    return this.request(`/api/v1/assessments/${assessmentId}/complete`, {
      method: "PUT",
    });
  }

  async getResults(assessmentId: string): Promise<any> {
    return this.request(`/api/v1/assessments/${assessmentId}/results`);
  }

  // --- Parent dashboard (added P1-T11) ---
  async getParentDashboard(userId: string): Promise<any> {
    return this.request(`/api/v1/parents/${userId}/dashboard`);
  }

  async getDetailedReport(userId: string): Promise<any> {
    return this.request(`/api/v1/parents/${userId}/report`);
  }

  async getNotificationPreferences(userId: string): Promise<any> {
    return this.request(`/api/v1/parents/${userId}/preferences`);
  }

  async updateNotificationPreferences(userId: string, prefs: unknown): Promise<any> {
    return this.request(`/api/v1/parents/${userId}/preferences`, {
      method: "PUT",
      body: JSON.stringify(prefs),
    });
  }

  // --- Learning plan / practice (added P1-T11) ---
  async generateLearningPlan(studentId: string, assessmentId?: string): Promise<any> {
    return this.request("/api/v1/learning-plans/generate", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, assessment_id: assessmentId }),
    });
  }

  async getLearningPlan(studentId: string): Promise<any> {
    return this.request(`/api/v1/learning-plans/${studentId}`);
  }

  async getNextLesson(studentId: string): Promise<any> {
    return this.request(`/api/v1/learning-plans/${studentId}/next-lesson`);
  }

  async completeModule(
    planId: string,
    moduleId: string,
    data: { p_mastered: number; lessons_completed: number; minutes_spent: number }
  ): Promise<any> {
    return this.request(
      `/api/v1/learning-plans/${planId}/modules/${moduleId}/complete`,
      { method: "POST", body: JSON.stringify(data) }
    );
  }

  async getStudentBadges(studentId: string): Promise<any> {
    return this.request(`/api/v1/students/${studentId}/badges`);
  }

  async getStudentStreak(studentId: string): Promise<any> {
    return this.request(`/api/v1/students/${studentId}/streak`);
  }
}

export const apiClient = new ApiClient();
