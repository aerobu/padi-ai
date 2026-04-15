/**
 * Zustand store for assessment session state.
 * Persists to localStorage for crash recovery.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { devtools } from "zustand/middleware";

export interface QuestionPresentation {
  question_id: string;
  question_number: number;
  standard_domain: string;
  stem: string;
  stem_image_url: string | null;
  options: { key: string; text: string; image_url: string | null }[];
  question_type: "multiple_choice" | "numeric" | "multi_step";
}

export interface OptionPresentation {
  key: string;
  text: string;
  image_url: string | null;
}

export interface AssessmentProgress {
  questions_answered: number;
  target_total: number;
  domains_covered: Record<string, number>;
  estimated_time_remaining_min: number;
}

export interface ResponseRecord {
  questionId: string;
  selectedOption: string;
  isCorrect: boolean;
  timeSpentMs: number;
  timestamp: string;
}

interface AssessmentState {
  // Session metadata
  sessionId: string | null;
  assessmentId: string | null;
  studentId: string | null;
  targetQuestionCount: number;

  // Current question
  currentQuestion: QuestionPresentation | null;
  questionIndex: number;

  // Responses tracking
  responses: ResponseRecord[];
  questionsAnswered: number;

  // Timing
  startTime: string | null;
  lastQuestionTime: number | null;

  // UI state
  isPaused: boolean;
  isSubmitting: boolean;
  isComplete: boolean;
  selectedOption: string | null;
  showFeedback: boolean;

  // Actions
  startSession: (params: {
    sessionId: string;
    assessmentId: string;
    studentId: string;
    targetQuestionCount: number;
  }) => void;
  setCurrentQuestion: (question: QuestionPresentation) => void;
  selectOption: (optionKey: string) => void;
  startAnswering: (questionId: string) => void;
  submitAnswer: (
    questionId: string,
    selectedAnswer: string,
    isCorrect: boolean,
    timeSpentMs: number
  ) => void;
  setSubmitting: (isSubmitting: boolean) => void;
  pauseSession: () => void;
  resumeSession: () => void;
  completeSession: () => void;
  resetSession: () => void;
  tick: (elapsedMs: number) => void;
  updateProgress: (progress: AssessmentProgress) => void;
}

export const useAssessmentStore = create<AssessmentState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        sessionId: null,
        assessmentId: null,
        studentId: null,
        targetQuestionCount: 35,
        currentQuestion: null,
        questionIndex: 0,
        responses: [],
        questionsAnswered: 0,
        startTime: null,
        lastQuestionTime: null,
        isPaused: false,
        isSubmitting: false,
        isComplete: false,
        selectedOption: null,
        showFeedback: false,

        // Action implementations
        startSession: (params) =>
          set({
            sessionId: params.sessionId,
            assessmentId: params.assessmentId,
            studentId: params.studentId,
            targetQuestionCount: params.targetQuestionCount,
            questionIndex: 0,
            responses: [],
            questionsAnswered: 0,
            startTime: new Date().toISOString(),
            lastQuestionTime: null,
            isPaused: false,
            isSubmitting: false,
            isComplete: false,
            selectedOption: null,
            showFeedback: false,
            currentQuestion: null,
          }),

        setCurrentQuestion: (question) =>
          set((state) => ({
            currentQuestion: question,
            selectedOption: null,
            showFeedback: false,
            lastQuestionTime: Date.now(),
          })),

        selectOption: (optionKey) =>
          set({ selectedOption: optionKey }),

        startAnswering: (questionId) =>
          set({
            lastQuestionTime: Date.now(),
            selectedOption: null,
            showFeedback: false,
          }),

        submitAnswer: (questionId, selectedAnswer, isCorrect, timeSpentMs) =>
          set((state) => ({
            responses: [
              ...state.responses,
              {
                questionId,
                selectedOption: selectedAnswer,
                isCorrect,
                timeSpentMs,
                timestamp: new Date().toISOString(),
              },
            ],
            questionsAnswered: state.questionsAnswered + 1,
            showFeedback: true,
            selectedOption: null,
            lastQuestionTime: null,
          })),

        setSubmitting: (isSubmitting) => set({ isSubmitting }),

        pauseSession: () => set({ isPaused: true }),

        resumeSession: () => set({ isPaused: false }),

        completeSession: () => set({ isComplete: true }),

        resetSession: () =>
          set({
            sessionId: null,
            assessmentId: null,
            studentId: null,
            targetQuestionCount: 35,
            currentQuestion: null,
            questionIndex: 0,
            responses: [],
            questionsAnswered: 0,
            startTime: null,
            lastQuestionTime: null,
            isPaused: false,
            isSubmitting: false,
            isComplete: false,
            selectedOption: null,
            showFeedback: false,
          }),

        tick: (elapsedMs) => set({ lastQuestionTime: Date.now() }),

        updateProgress: (progress) =>
          set({ questionsAnswered: progress.questions_answered }),
      }),
      {
        name: "padi-assessment-store",
        partialize: (state) => ({
          sessionId: state.sessionId,
          assessmentId: state.assessmentId,
          studentId: state.studentId,
          currentQuestion: state.currentQuestion,
          responses: state.responses,
          questionsAnswered: state.questionsAnswered,
          startTime: state.startTime,
          lastQuestionTime: state.lastQuestionTime,
          isPaused: state.isPaused,
          isSubmitting: state.isSubmitting,
          isComplete: state.isComplete,
          selectedOption: state.selectedOption,
          showFeedback: state.showFeedback,
        }),
      }
    )
  )
);
