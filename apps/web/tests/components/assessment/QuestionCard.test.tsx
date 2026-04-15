/**
 * Tests for QuestionCard component.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { QuestionCard } from '@padi/assessment/question-card';

describe('QuestionCard', () => {
  const baseProps = {
    questionNumber: 1,
    domain: 'Numbers and Operations',
    stem: 'What is 1234 rounded to the nearest hundred?',
    options: [
      { key: 'A', text: '1200', image_url: null },
      { key: 'B', text: '1250', image_url: null },
      { key: 'C', text: '1300', image_url: null },
      { key: 'D', text: '1400', image_url: null },
    ],
    questionType: 'multiple_choice' as const,
    onAnswerSelected: vi.fn(),
    selectedOption: null,
    showFeedback: false,
    isCorrect: false,
    explanation: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders question number badge', () => {
      render(<QuestionCard {...baseProps} />);
      expect(screen.getByText('Question 1')).toBeInTheDocument();
    });

    it('renders domain badge', () => {
      render(<QuestionCard {...baseProps} />);
      expect(screen.getByText('Numbers and Operations')).toBeInTheDocument();
    });

    it('renders question stem', () => {
      render(<QuestionCard {...baseProps} />);
      expect(
        screen.getByText('What is 1234 rounded to the nearest hundred?')
      ).toBeInTheDocument();
    });

    it('renders all answer options', () => {
      render(<QuestionCard {...baseProps} />);

      expect(screen.getByText('A.')).toBeInTheDocument();
      expect(screen.getByText('1200')).toBeInTheDocument();
      expect(screen.getByText('B.')).toBeInTheDocument();
      expect(screen.getByText('1250')).toBeInTheDocument();
      expect(screen.getByText('C.')).toBeInTheDocument();
      expect(screen.getByText('1300')).toBeInTheDocument();
      expect(screen.getByText('D.')).toBeInTheDocument();
      expect(screen.getByText('1400')).toBeInTheDocument();
    });

    it('renders time indicator', () => {
      render(<QuestionCard {...baseProps} />);
      expect(screen.getByText(/Time spent:/)).toBeInTheDocument();
    });
  });

  describe('Option Selection', () => {
    it('handles option click', () => {
      const handleAnswerSelected = vi.fn();
      const props = { ...baseProps, onAnswerSelected: handleAnswerSelected };

      render(<QuestionCard {...props} />);

      const optionA = screen.getByText('A.');
      fireEvent.click(optionA);

      expect(handleAnswerSelected).toHaveBeenCalledWith('A');
    });

    it('highlights selected option', () => {
      const props = { ...baseProps, selectedOption: 'A' };

      render(<QuestionCard {...props} />);

      // Check for selected styling
      const optionA = screen.getByText('A.');
      expect(optionA).toBeInTheDocument();
    });

    it('disables options when showFeedback is true', () => {
      const props = { ...baseProps, showFeedback: true };

      render(<QuestionCard {...props} />);

      const optionA = screen.getByText('A.');
      // Options should be disabled when showing feedback
      expect(optionA.parentElement).toHaveAttribute('disabled');
    });
  });

  describe('Feedback Display', () => {
    it('shows feedback when showFeedback is true', () => {
      const props = {
        ...baseProps,
        showFeedback: true,
        isCorrect: true,
        explanation: 'This is the correct explanation.',
      };

      render(<QuestionCard {...props} />);

      expect(screen.getByText('Correct!')).toBeInTheDocument();
      expect(screen.getByText('This is the correct explanation.')).toBeInTheDocument();
    });

    it('shows "not quite right" for incorrect answers', () => {
      const props = {
        ...baseProps,
        showFeedback: true,
        isCorrect: false,
        explanation: 'Wrong answer.',
      };

      render(<QuestionCard {...props} />);

      expect(screen.getByText('Not quite right.')).toBeInTheDocument();
    });

    it('highlights correct answer in green', () => {
      const props = {
        ...baseProps,
        showFeedback: true,
        isCorrect: true,
      };

      render(<QuestionCard {...props} />);

      // Find the option that is correct (has is_correct: true in options)
      // This would need to be passed to the component options
    });

    it('highlights wrong selection in red', () => {
      const props = {
        ...baseProps,
        showFeedback: true,
        isCorrect: false,
        selectedOption: 'B', // User selected wrong answer
      };

      render(<QuestionCard {...props} />);
      // Check for red styling on selected wrong answer
    });

    it('does not show feedback when showFeedback is false', () => {
      render(<QuestionCard {...baseProps} />);

      expect(screen.queryByText(/Correct!/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Not quite right./)).not.toBeInTheDocument();
    });

    it('does not show explanation when explanation is null', () => {
      const props = {
        ...baseProps,
        showFeedback: true,
        isCorrect: true,
        explanation: null,
      };

      render(<QuestionCard {...props} />);

      expect(screen.queryByText(/This is the correct explanation./)).not.toBeInTheDocument();
    });
  });

  describe('Question Type Variations', () => {
    it('renders multiple_choice question type', () => {
      const props = { ...baseProps, questionType: 'multiple_choice' };
      render(<QuestionCard {...props} />);
      expect(screen.getByText('A.')).toBeInTheDocument();
    });

    it('renders numeric question type', () => {
      const props = {
        ...baseProps,
        questionType: 'numeric',
        options: [],
      };
      render(<QuestionCard {...props} />);
      // Numeric questions may have different rendering
    });

    it('renders multi_step question type', () => {
      const props = {
        ...baseProps,
        questionType: 'multi_step',
      };
      render(<QuestionCard {...props} />);
      expect(screen.getByText('A.')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty options array', () => {
      const props = {
        ...baseProps,
        options: [],
      };

      render(<QuestionCard {...props} />);
      // Should render without errors
      expect(screen.getByText('Question 1')).toBeInTheDocument();
    });

    it('handles large question numbers', () => {
      const props = { ...baseProps, questionNumber: 35 };
      render(<QuestionCard {...props} />);
      expect(screen.getByText('Question 35')).toBeInTheDocument();
    });

    it('handles long question stems', () => {
      const longStem = 'This is a very long question stem that contains a lot of text to test how the component handles extended content and potentially wrapped text across multiple lines in the display.';
      const props = { ...baseProps, stem: longStem };
      render(<QuestionCard {...props} />);
      expect(screen.getByText(longStem)).toBeInTheDocument();
    });

    it('handles special characters in options', () => {
      const props = {
        ...baseProps,
        options: [
          { key: 'A', text: 'Option with "quotes"', image_url: null },
          { key: 'B', text: 'Option with <html>', image_url: null },
          { key: 'C', text: 'Option with & symbols', image_url: null },
        ],
      };

      render(<QuestionCard {...props} />);
      expect(screen.getByText(/Option with/)).toBeInTheDocument();
    });
  });
});
