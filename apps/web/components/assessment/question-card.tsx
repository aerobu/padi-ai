"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@padi/ui/card";
import { MathText } from "@/components/math/MathText";

export interface Option {
  key: string;
  text: string;
  image_url: string | null;
  is_correct?: boolean;
}

export interface QuestionCardProps {
  questionNumber: number;
  domain: string;
  stem: string;
  options: Option[];
  questionType: "multiple_choice" | "numeric" | "multi_step";
  onAnswerSelected: (optionKey: string) => void;
  selectedOption: string | null;
  showFeedback?: boolean;
  isCorrect?: boolean;
  explanation?: string | null;
}

export function QuestionCard({
  questionNumber,
  domain,
  stem,
  options,
  questionType,
  onAnswerSelected,
  selectedOption,
  showFeedback = false,
  isCorrect = false,
  explanation = null,
}: QuestionCardProps) {
  const [timeSpent, setTimeSpent] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeSpent((prev) => prev + 1000);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleOptionClick = (optionKey: string) => {
    onAnswerSelected(optionKey);
  };

  return (
    <Card className="w-full max-w-[600px] mx-auto">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-6">
          <span className="text-[12px] font-semibold text-neutral-400 uppercase tracking-[.08em]">Question {questionNumber}</span>
          <span className="text-[12px] font-semibold text-terra-500 bg-terra-50 px-2.5 py-1 rounded-full">{domain}</span>
        </div>

        <p className="text-display-sm text-neutral-900 mb-6">
          <MathText>{stem}</MathText>
        </p>

        <div className="space-y-3">
          {options.map((option) => {
            return (
              <button
                key={option.key}
                onClick={() => !showFeedback && handleOptionClick(option.key)}
                disabled={showFeedback}
                className="w-full text-left p-4 rounded-lg border-[1.5px] bg-surface-cream border-neutral-200 hover:border-green-500 hover:bg-green-50 transition-all duration-200 disabled:opacity-50"
              >
                <span className="font-semibold mr-3 text-neutral-700">{option.key}.</span>
                <span className="text-neutral-900">
                  <MathText>{option.text}</MathText>
                </span>
              </button>
            );
          })}
        </div>

        {showFeedback && (
          <div className="mt-5 p-4 rounded-lg bg-green-50 border border-green-200">
            <p className="font-semibold text-neutral-900">{isCorrect ? "Correct!" : "Not quite right."}</p>
            {explanation && (
              <p className="mt-2 text-[14px] text-neutral-600">
                <MathText>{explanation}</MathText>
              </p>
            )}
          </div>
        )}

        <div className="mt-5 text-[12px] text-neutral-400">Time spent: {Math.floor(timeSpent / 1000)}s</div>
      </CardContent>
    </Card>
  );
}
