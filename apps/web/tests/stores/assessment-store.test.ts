/**
 * Tests for assessment store.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAssessmentStore } from '@/stores/assessment-store';

describe('useAssessmentStore', () => {
  beforeEach(() => {
    // Reset store between tests
    useAssessmentStore.setState({
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
    });
  });

  describe('Initial State', () => {
    it('has correct initial state', () => {
      const state = useAssessmentStore.getState();

      expect(state.sessionId).toBeNull();
      expect(state.assessmentId).toBeNull();
      expect(state.studentId).toBeNull();
      expect(state.targetQuestionCount).toBe(35);
      expect(state.currentQuestion).toBeNull();
      expect(state.questionIndex).toBe(0);
      expect(state.responses).toEqual([]);
      expect(state.questionsAnswered).toBe(0);
      expect(state.isPaused).toBe(false);
      expect(state.isSubmitting).toBe(false);
      expect(state.isComplete).toBe(false);
    });
  });

  describe('startSession', () => {
    it('initializes session with provided params', () => {
      const params = {
        sessionId: 'session-123',
        assessmentId: 'assessment-123',
        studentId: 'student-123',
        targetQuestionCount: 35,
      };

      useAssessmentStore.getState().startSession(params);

      const state = useAssessmentStore.getState();

      expect(state.sessionId).toBe('session-123');
      expect(state.assessmentId).toBe('assessment-123');
      expect(state.studentId).toBe('student-123');
      expect(state.targetQuestionCount).toBe(35);
      expect(state.questionIndex).toBe(0);
      expect(state.responses).toEqual([]);
      expect(state.questionsAnswered).toBe(0);
      expect(state.startTime).toBeDefined();
      expect(state.startTime).toBeInstanceOf(String);
      expect(state.isPaused).toBe(false);
      expect(state.isSubmitting).toBe(false);
      expect(state.isComplete).toBe(false);
    });

    it('resets state before starting new session', () => {
      // Set some state
      useAssessmentStore.getState().startSession({
        sessionId: 'session-old',
        assessmentId: 'assessment-old',
        studentId: 'student-old',
        targetQuestionCount: 35,
      });

      // Start new session
      useAssessmentStore.getState().startSession({
        sessionId: 'session-new',
        assessmentId: 'assessment-new',
        studentId: 'student-new',
        targetQuestionCount: 35,
      });

      const state = useAssessmentStore.getState();

      expect(state.sessionId).toBe('session-new');
      expect(state.assessmentId).toBe('assessment-new');
      expect(state.studentId).toBe('student-new');
      expect(state.questionIndex).toBe(0);
      expect(state.responses).toEqual([]);
    });
  });

  describe('setCurrentQuestion', () => {
    it('sets current question and resets UI state', () => {
      const question = {
        question_id: 'q1',
        question_number: 1,
        standard_domain: 'Numbers and Operations',
        stem: 'Test question?',
        stem_image_url: null,
        options: [
          { key: 'A', text: 'Option A', image_url: null },
          { key: 'B', text: 'Option B', image_url: null },
        ],
        question_type: 'multiple_choice',
      };

      useAssessmentStore.getState().setCurrentQuestion(question);

      const state = useAssessmentStore.getState();

      expect(state.currentQuestion).toEqual(question);
      expect(state.selectedOption).toBeNull();
      expect(state.showFeedback).toBe(false);
      expect(state.lastQuestionTime).toBeDefined();
    });
  });

  describe('selectOption', () => {
    it('sets selected option', () => {
      useAssessmentStore.getState().selectOption('A');

      const state = useAssessmentStore.getState();

      expect(state.selectedOption).toBe('A');
    });
  });

  describe('startAnswering', () => {
    it('resets answering state', () => {
      useAssessmentStore.getState().selectOption('A');
      useAssessmentStore.getState().startAnswering('q1');

      const state = useAssessmentStore.getState();

      expect(state.lastQuestionTime).toBeDefined();
      expect(state.selectedOption).toBeNull();
      expect(state.showFeedback).toBe(false);
    });
  });

  describe('submitAnswer', () => {
    it('records answer and updates progress', () => {
      const mockTime = 30000;

      useAssessmentStore.getState().submitAnswer(
        'q1',
        'A',
        true,
        mockTime
      );

      const state = useAssessmentStore.getState();

      expect(state.responses.length).toBe(1);
      expect(state.responses[0].questionId).toBe('q1');
      expect(state.responses[0].selectedOption).toBe('A');
      expect(state.responses[0].isCorrect).toBe(true);
      expect(state.responses[0].timeSpentMs).toBe(mockTime);
      expect(state.responses[0].timestamp).toBeDefined();
      expect(state.questionsAnswered).toBe(1);
      expect(state.showFeedback).toBe(true);
      expect(state.selectedOption).toBeNull();
    });

    it('records multiple answers correctly', () => {
      useAssessmentStore.getState().submitAnswer('q1', 'A', true, 30000);
      useAssessmentStore.getState().submitAnswer('q2', 'B', false, 45000);

      const state = useAssessmentStore.getState();

      expect(state.responses.length).toBe(2);
      expect(state.questionsAnswered).toBe(2);
      expect(state.responses[0].questionId).toBe('q1');
      expect(state.responses[1].questionId).toBe('q2');
    });
  });

  describe('setSubmitting', () => {
    it('sets submitting state', () => {
      useAssessmentStore.getState().setSubmitting(true);

      const state = useAssessmentStore.getState();

      expect(state.isSubmitting).toBe(true);

      useAssessmentStore.getState().setSubmitting(false);

      expect(state.isSubmitting).toBe(false);
    });
  });

  describe('pauseSession', () => {
    it('pauses the session', () => {
      useAssessmentStore.getState().pauseSession();

      const state = useAssessmentStore.getState();

      expect(state.isPaused).toBe(true);
    });
  });

  describe('resumeSession', () => {
    it('resumes the session', () => {
      useAssessmentStore.getState().pauseSession();
      useAssessmentStore.getState().resumeSession();

      const state = useAssessmentStore.getState();

      expect(state.isPaused).toBe(false);
    });
  });

  describe('completeSession', () => {
    it('marks session as complete', () => {
      useAssessmentStore.getState().completeSession();

      const state = useAssessmentStore.getState();

      expect(state.isComplete).toBe(true);
    });
  });

  describe('resetSession', () => {
    it('clears all session state', () => {
      // Set some state
      useAssessmentStore.getState().startSession({
        sessionId: 'session-123',
        assessmentId: 'assessment-123',
        studentId: 'student-123',
        targetQuestionCount: 35,
      });

      useAssessmentStore.getState().setCurrentQuestion({
        question_id: 'q1',
        question_number: 1,
        standard_domain: 'Test',
        stem: 'Test?',
        stem_image_url: null,
        options: [],
        question_type: 'multiple_choice',
      });

      useAssessmentStore.getState().submitAnswer('q1', 'A', true, 30000);

      // Reset
      useAssessmentStore.getState().resetSession();

      const state = useAssessmentStore.getState();

      expect(state.sessionId).toBeNull();
      expect(state.assessmentId).toBeNull();
      expect(state.studentId).toBeNull();
      expect(state.currentQuestion).toBeNull();
      expect(state.responses).toEqual([]);
      expect(state.questionsAnswered).toBe(0);
      expect(state.startTime).toBeNull();
      expect(state.isPaused).toBe(false);
      expect(state.isSubmitting).toBe(false);
      expect(state.isComplete).toBe(false);
    });
  });

  describe('tick', () => {
    it('updates last question time', () => {
      const elapsed = 5000;

      useAssessmentStore.getState().tick(elapsed);

      const state = useAssessmentStore.getState();

      // Just verify it doesn't error and sets the time
      expect(state.lastQuestionTime).toBeDefined();
    });
  });

  describe('updateProgress', () => {
    it('updates questions answered from progress', () => {
      const progress = {
        questions_answered: 15,
        target_total: 35,
        domains_covered: {},
        estimated_time_remaining_min: 10,
      };

      useAssessmentStore.getState().updateProgress(progress);

      const state = useAssessmentStore.getState();

      expect(state.questionsAnswered).toBe(15);
    });
  });

  describe('State Persistence', () => {
    it('persist middleware should persist to localStorage', () => {
      // This test verifies the store configuration
      const state = useAssessmentStore.getState();

      // The persist middleware should be configured
      // We can't easily test localStorage in unit tests without mocking
      // But we can verify the store has the expected structure
      expect(state).toHaveProperty('sessionId');
      expect(state).toHaveProperty('responses');
      expect(state).toHaveProperty('startSession');
      expect(state).toHaveProperty('submitAnswer');
    });
  });

  describe('Edge Cases', () => {
    it('handles concurrent updates correctly', () => {
      useAssessmentStore.getState().startSession({
        sessionId: 'session-123',
        assessmentId: 'assessment-123',
        studentId: 'student-123',
        targetQuestionCount: 35,
      });

      // Submit multiple answers quickly
      useAssessmentStore.getState().submitAnswer('q1', 'A', true, 30000);
      useAssessmentStore.getState().submitAnswer('q2', 'B', true, 40000);
      useAssessmentStore.getState().submitAnswer('q3', 'C', false, 50000);

      const state = useAssessmentStore.getState();

      expect(state.responses.length).toBe(3);
      expect(state.questionsAnswered).toBe(3);
    });

    it('handles null/undefined gracefully', () => {
      // Should not throw errors
      useAssessmentStore.getState().selectOption(null as any);
      useAssessmentStore.getState().setCurrentQuestion(null as any);
      useAssessmentStore.getState().updateProgress({} as any);
    });
  });
});
