/**
 * Live assessment page.
 * Displays questions one at a time and handles submission.
 */

"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAssessmentStore } from "@/stores/assessment-store";
import { QuestionCard } from "@/components/assessment/question-card";
import { ProgressTracker } from "@/components/assessment/progress-tracker";
import { Button } from "@/packages/ui/button";
import { apiClient } from "@/lib/api-client";

export default function AssessmentPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const {
    currentQuestion,
    selectedOption,
    questionsAnswered,
    startSession,
    setCurrentQuestion,
    selectOption,
    submitAnswer,
    setSubmitting,
    updateProgress,
  } = useAssessmentStore();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmittingState] = useState(false);
  const [progress, setProgressState] = useState({
    questions_answered: 0,
    target_total: 35,
    domains_covered: {},
    estimated_time_remaining_min: 0,
  });
  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [correctAnswer, setCorrectAnswer] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());

  // Start assessment when sessionId is available
  useEffect(() => {
    if (sessionId && !assessmentId) {
      // In a real app, we'd start the assessment here
      // For now, we'll assume the session is already started
      setLoading(false);
    }
  }, [sessionId, assessmentId]);

  // Fetch next question
  const fetchNextQuestion = async () => {
    try {
      if (!sessionId) return;

      setSubmittingState(true);
      const response = await apiClient.getNextQuestion(sessionId);

      if (response.should_end) {
        // Assessment should end - navigate to results
        router.push(`/diagnostic/results?assessment=${sessionId}`);
        return;
      }

      if (response.question) {
        setCurrentQuestion(response.question);
        setProgressState(response.progress);
        updateProgress(response.progress);
        setShowFeedback(false);
        setQuestionStartTime(Date.now());
      }
    } catch (error) {
      console.error("Error fetching question:", error);
      alert("Failed to load question. Please try again.");
      router.push("/dashboard");
    } finally {
      setSubmittingState(false);
    }
  };

  // Handle answer selection
  const handleAnswerSelected = async (optionKey: string) => {
    if (!currentQuestion || showFeedback) return;

    selectOption(optionKey);

    // Auto-submit after a short delay
    setTimeout(async () => {
      await submitAnswerToServer(optionKey);
    }, 500);
  };

  const submitAnswerToServer = async (selectedAnswer: string) => {
    if (!sessionId || !currentQuestion) return;

    setSubmittingState(true);
    const timeSpentMs = Date.now() - questionStartTime;

    try {
      const response = await apiClient.submitResponse(sessionId, {
        question_id: currentQuestion.question_id,
        selected_answer: selectedAnswer,
        time_spent_ms: timeSpentMs,
      });

      // Show feedback
      setShowFeedback(true);
      setIsCorrect(response.is_correct);
      setCorrectAnswer(response.correct_answer);
      setExplanation(response.explanation);
      updateProgress(response.progress);

      // Auto-advance after showing feedback
      setTimeout(() => {
        fetchNextQuestion();
      }, 2000);
    } catch (error) {
      console.error("Error submitting answer:", error);
      alert("Failed to submit answer. Please try again.");
    } finally {
      setSubmittingState(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-lg font-medium">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-lg font-medium">No question available.</p>
          <Button className="mt-4" onClick={() => router.push("/dashboard")}>
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-slate-900">Assessment</h1>
          <div className="text-sm text-slate-600">
            Question {questionsAnswered + 1} of {progress.target_total}
          </div>
        </div>

        {/* Progress tracker */}
        <ProgressTracker
          questionsAnswered={questionsAnswered}
          targetTotal={progress.target_total}
          domainsCovered={progress.domains_covered}
          estimatedTimeRemainingMin={progress.estimated_time_remaining_min}
        />

        {/* Question card */}
        <QuestionCard
          questionNumber={questionsAnswered + 1}
          domain={currentQuestion.standard_domain}
          stem={currentQuestion.stem}
          options={currentQuestion.options}
          questionType={currentQuestion.question_type}
          onAnswerSelected={handleAnswerSelected}
          selectedOption={showFeedback ? null : selectedOption}
          showFeedback={showFeedback}
          isCorrect={isCorrect}
          explanation={explanation}
        />

        {/* Manual submit button (if needed) */}
        {!showFeedback && selectedOption && (
          <div className="flex justify-end">
            <Button
              onClick={() => submitAnswerToServer(selectedOption)}
              disabled={submitting}
            >
              {submitting ? "Submitting..." : "Submit Answer"}
            </Button>
          </div>
        )}

        {/* Loading indicator */}
        {submitting && (
          <div className="text-center text-slate-600">Loading...</div>
        )}
      </div>
    </div>
  );
}
