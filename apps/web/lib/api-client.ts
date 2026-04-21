/**
 * API client for PADI.AI
 * Typed fetch wrapper with JWT authentication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (response.status === 401) {
      if (typeof window !== "undefined") {
        window.location.assign("/login");
      }
      throw new Error("Unauthenticated");
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: {
          code: "API_ERROR",
          message: "An API error occurred",
        },
      }));
      throw new Error(error.error?.message || "API request failed");
    }

    return response.json();
  }

  // Consent API
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

  // Student API
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

  // Standards API
  async listStandards(grade?: number, domain?: string): Promise<any> {
    const params = new URLSearchParams();
    if (grade) params.append("grade", grade.toString());
    if (domain) params.append("domain", domain);
    return this.request(`/api/v1/standards?${params}`);
  }

  async getStandard(standardCode: string): Promise<any> {
    return this.request(`/api/v1/standards/${standardCode}`);
  }

  // Assessment API
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
    data: {
      question_id: string;
      selected_answer: string;
      time_spent_ms: number;
    }
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
}

// Singleton instance
export const apiClient = new ApiClient();
