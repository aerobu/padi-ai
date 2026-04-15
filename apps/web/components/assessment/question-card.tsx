/**
 * Question card component for displaying assessment questions.
 */

"use client";

import React, { useState } from "react";
import { Button } from "@padi/ui/button";
import { Card, CardContent } from "@padi/ui/card";
import { Badge } from "@padi/ui/badge";

interface Option {
  key: string;
  text: string;
  image_url: string | null;
}

interface QuestionCardProps {
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

  // Track time spent on question
  React.useEffect(() => {
    const interval = setInterval(() => {
      setTimeSpent((prev) => prev + 1000);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleOptionClick = (optionKey: string) => {
    onAnswerSelected(optionKey);
  };

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardContent className="p-6">
        {/* Header with question number and domain */}
        <div className="flex items-center justify-between mb-4">
          <Badge variant="outline">Question {questionNumber}</Badge>
          <Badge variant="secondary">{domain}</Badge>
        </div>

        {/* Question text */}
        <div className="mb-6">
          <p className="text-lg font-medium text-slate-900">{stem}</p>
        </div>

        {/* Options */}
        <div className="space-y-3">
          {options.map((option) => {
            const isSelected = selectedOption === option.key;
            let buttonVariant: "default" | "outline" | "secondary" = "outline";

            if (showFeedback) {
              if (option.is_correct) {
                buttonVariant = "default"; // Correct answer highlighted
              } else if (isSelected && !isCorrect) {
                buttonVariant = "secondary"; // Wrong selection
              } else {
                buttonVariant = "outline";
              }
            } else if (isSelected) {
              buttonVariant = "default";
            }

            return (
              <button
                key={option.key}
                onClick={() => !showFeedback && handleOptionClick(option.key)}
                disabled={showFeedback}
                className={`w-full p-4 text-left rounded-lg border-2 transition-all ${
                  isSelected
                    ? "border-blue-500 bg-blue-50"
                    : "border-slate-200 hover:border-blue-300"
                } ${
                  showFeedback && option.is_correct
                    ? "border-green-500 bg-green-50"
                    : ""
                } ${showFeedback && isSelected && !isCorrect ? "border-red-500 bg-red-50" : ""}`}
              >
                <div className="flex items-center">
                  <span className="font-semibold mr-3 text-slate-700">
                    {option.key}.
                  </span>
                  <span className="text-slate-900">{option.text}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Feedback */}
        {showFeedback && (
          <div
            className={`mt-4 p-4 rounded-lg ${
              isCorrect ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"
            }`}
          >
            <p className="font-medium text-slate-900">
              {isCorrect ? "Correct!" : "Not quite right."}
            </p>
            {explanation && (
              <p className="mt-2 text-sm text-slate-600">{explanation}</p>
            )}
          </div>
        )}

        {/* Time indicator */}
        <div className="mt-4 text-sm text-slate-500">
          Time spent: {Math.floor(timeSpent / 1000)}s
        </div>
      </CardContent>
    </Card>
  );
}
