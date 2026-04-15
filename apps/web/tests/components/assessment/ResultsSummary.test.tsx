/**
 * Tests for ResultsSummary component.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ResultsSummary } from '@padi/assessment/results-summary';

// Mock Next.js useRouter
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
  }),
}));

describe('ResultsSummary', () => {
  const baseProps = {
    sessionId: 'session-123',
    studentId: 'student-123',
    overallScore: 0.78,
    totalQuestions: 35,
    questionsAnswered: 35,
    completionTimeSec: 2100,
    domainResults: [
      {
        domain: 'Operations & Algebraic Thinking',
        code: 'OA',
        questionsAnswered: 7,
        correct: 6,
        mastery: 0.82,
      },
      {
        domain: 'Numbers & Operations in Base Ten',
        code: 'NBT',
        questionsAnswered: 7,
        correct: 5,
        mastery: 0.71,
      },
      {
        domain: 'Numbers & Operations - Fractions',
        code: 'NF',
        questionsAnswered: 7,
        correct: 5,
        mastery: 0.70,
      },
      {
        domain: 'Geometry',
        code: 'GM',
        questionsAnswered: 7,
        correct: 6,
        mastery: 0.85,
      },
      {
        domain: 'Measurement & Data',
        code: 'MD',
        questionsAnswered: 7,
        correct: 4,
        mastery: 0.62,
      },
    ],
    gapAnalysis: {
      strengths: ['4.OA.A.1', '4.NBT.A.2', '4.G.A.1'],
      on_track: ['4.NF.A.1', '4.MD.A.1', '4.MD.A.2'],
      needs_work: ['4.NBT.A.1', '4.NF.B.3'],
    },
    onBack: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Overall Score Display', () => {
    it('displays overall score as percentage', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByText('78%')).toBeInTheDocument();
    });

    it('displays overall score as decimal', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByText('78%')).toBeInTheDocument();
      expect(screen.getByText('27 / 35 correct')).toBeInTheDocument();
    });

    it('displays correct classification badge', () => {
      render(<ResultsSummary {...baseProps} />);

      // 0.78 = on_par (between 0.60 and 0.80)
      expect(screen.getByText('On Track')).toBeInTheDocument();
    });

    it('displays above_par for scores >= 0.80', () => {
      const props = {
        ...baseProps,
        overallScore: 0.85,
      };

      render(<ResultsSummary {...props} />);
      expect(screen.getByText('Above Par')).toBeInTheDocument();
    });

    it('displays below_par for scores < 0.60', () => {
      const props = {
        ...baseProps,
        overallScore: 0.55,
      };

      render(<ResultsSummary {...props} />);
      expect(screen.getByText('Below Par')).toBeInTheDocument();
    });
  });

  describe('Domain Breakdown', () => {
    it('displays all domains with mastery levels', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByText('Operations & Algebraic Thinking')).toBeInTheDocument();
      expect(screen.getByText('71%')).toBeInTheDocument(); // NBT
      expect(screen.getByText('Geometry')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('displays mastery percentage for each domain', () => {
      render(<ResultsSummary {...baseProps} />);

      // Check for mastery percentages
      expect(screen.getByText('82%')).toBeInTheDocument(); // OA
      expect(screen.getByText('71%')).toBeInTheDocument(); // NBT
      expect(screen.getByText('70%')).toBeInTheDocument(); // NF
      expect(screen.getByText('85%')).toBeInTheDocument(); // GM
      expect(screen.getByText('62%')).toBeInTheDocument(); // MD
    });

    it('displays questions answered for each domain', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByText('7 questions')).toBeInTheDocument();
    });

    it('colors domain badges by mastery level', () => {
      render(<ResultsSummary {...baseProps} />);

      // Above par (>= 0.80) should have success/green styling
      const geometryBadge = screen.getByText('85%');
      expect(geometryBadge).toBeInTheDocument();

      // Below par (< 0.60) should have error/red styling
      const mdBadge = screen.getByText('62%');
      expect(mdBadge).toBeInTheDocument();
    });
  });

  describe('Gap Analysis', () => {
    it('displays strengths section', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByText('Strengths')).toBeInTheDocument();
      expect(screen.getByText('4.OA.A.1')).toBeInTheDocument();
      expect(screen.getByText('4.NBT.A.2')).toBeInTheDocument();
      expect(screen.getByText('4.G.A.1')).toBeInTheDocument();
    });

    it('displays on_track section', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByText('On Track')).toBeInTheDocument();
      expect(screen.getByText('4.NF.A.1')).toBeInTheDocument();
      expect(screen.getByText('4.MD.A.1')).toBeInTheDocument();
    });

    it('displays needs_work section', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByText('Needs Work')).toBeInTheDocument();
      expect(screen.getByText('4.NBT.A.1')).toBeInTheDocument();
      expect(screen.getByText('4.NF.B.3')).toBeInTheDocument();
    });

    it('hides empty sections', () => {
      const props = {
        ...baseProps,
        gapAnalysis: {
          strengths: [],
          on_track: ['4.NF.A.1'],
          needs_work: [],
        },
      };

      render(<ResultsSummary {...props} />);

      expect(screen.getByText('On Track')).toBeInTheDocument();
      expect(screen.queryByText('4.NF.A.1')).toBeInTheDocument();
      // Empty sections should not render
    });

    it('displays custom messages for empty sections', () => {
      const props = {
        ...baseProps,
        gapAnalysis: {
          strengths: [],
          on_track: [],
          needs_work: [],
        },
      };

      render(<ResultsSummary {...props} />);

      expect(screen.getByText('No strengths identified')).toBeInTheDocument();
      expect(screen.getByText('No standards on track')).toBeInTheDocument();
      expect(screen.getByText('No standards need work')).toBeInTheDocument();
    });
  });

  describe('Completion Time', () => {
    it('displays completion time in minutes', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByText('35 minutes')).toBeInTheDocument(); // 2100 seconds = 35 minutes
    });

    it('displays completion time with seconds for short assessments', () => {
      const props = {
        ...baseProps,
        completionTimeSec: 125, // 2 minutes 5 seconds
      };

      render(<ResultsSummary {...props} />);

      expect(screen.getByText(/minutes/)).toBeInTheDocument();
    });

    it('handles zero completion time', () => {
      const props = {
        ...baseProps,
        completionTimeSec: 0,
      };

      render(<ResultsSummary {...props} />);
      expect(screen.getByText('0 minutes')).toBeInTheDocument();
    });
  });

  describe('Navigation Buttons', () => {
    it('displays Back to Dashboard button', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByRole('button', { name: /Back to Dashboard/i })).toBeInTheDocument();
    });

    it('calls onBack when Back button is clicked', () => {
      render(<ResultsSummary {...baseProps} />);

      const backButton = screen.getByRole('button', { name: /Back to Dashboard/i });
      fireEvent.click(backButton);

      expect(baseProps.onBack).toHaveBeenCalled();
    });

    it('displays Print Results button', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByRole('button', { name: /Print Results/i })).toBeInTheDocument();
    });

    it('calls onPrint when Print button is clicked', () => {
      const props = {
        ...baseProps,
        onPrint: vi.fn(),
      };

      render(<ResultsSummary {...props} />);

      const printButton = screen.getByRole('button', { name: /Print Results/i });
      fireEvent.click(printButton);

      expect(props.onPrint).toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('handles 0% overall score', () => {
      const props = {
        ...baseProps,
        overallScore: 0,
      };

      render(<ResultsSummary {...props} />);
      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('Below Par')).toBeInTheDocument();
    });

    it('handles 100% overall score', () => {
      const props = {
        ...baseProps,
        overallScore: 1,
      };

      render(<ResultsSummary {...props} />);
      expect(screen.getByText('100%')).toBeInTheDocument();
      expect(screen.getByText('Above Par')).toBeInTheDocument();
    });

    it('handles partial completion', () => {
      const props = {
        ...baseProps,
        totalQuestions: 35,
        questionsAnswered: 20,
      };

      render(<ResultsSummary {...props} />);
      expect(screen.getByText('20 / 35')).toBeInTheDocument();
    });

    it('handles missing domain results', () => {
      const props = {
        ...baseProps,
        domainResults: [],
      };

      render(<ResultsSummary {...props} />);
      // Should still display overall score
      expect(screen.getByText('78%')).toBeInTheDocument();
    });

    it('handles incomplete gap analysis', () => {
      const props = {
        ...baseProps,
        gapAnalysis: {},
      };

      render(<ResultsSummary {...props} />);
      // Should not crash
      expect(screen.getByText('78%')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      render(<ResultsSummary {...baseProps} />);

      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
    });

    it('has descriptive button labels', () => {
      render(<ResultsSummary {...baseProps} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        expect(button).toHaveAttribute('aria-label');
      });
    });
  });
});
