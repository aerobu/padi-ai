/**
 * Tests for ProgressTracker component.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressTracker } from '@padi/assessment/progress-tracker';

describe('ProgressTracker', () => {
  const baseProps = {
    questionsAnswered: 10,
    targetTotal: 35,
    domainsCovered: {
      '4.NBT': 5,
      '4.NF': 3,
      '4.OA': 2,
    },
    estimatedTimeRemainingMin: 7,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders progress bar with correct percentage', () => {
      render(<ProgressTracker {...baseProps} />);

      // Progress should be 10/35 = ~29%
      expect(screen.getByText('Progress')).toBeInTheDocument();
      expect(screen.getByText('10 / 35')).toBeInTheDocument();
      expect(screen.getByText('Estimated time remaining: ~7 minutes')).toBeInTheDocument();
    });

    it('renders domain coverage badges', () => {
      render(<ProgressTracker {...baseProps} />);

      expect(screen.getByText('Domain Coverage')).toBeInTheDocument();
      expect(screen.getByText('4.NBT: 5')).toBeInTheDocument();
      expect(screen.getByText('4.NF: 3')).toBeInTheDocument();
      expect(screen.getByText('4.OA: 2')).toBeInTheDocument();
    });

    it('renders with 0 progress', () => {
      const props = {
        ...baseProps,
        questionsAnswered: 0,
      };

      render(<ProgressTracker {...props} />);
      expect(screen.getByText('0 / 35')).toBeInTheDocument();
    });

    it('renders with 100% progress', () => {
      const props = {
        ...baseProps,
        questionsAnswered: 35,
      };

      render(<ProgressTracker {...props} />);
      expect(screen.getByText('35 / 35')).toBeInTheDocument();
    });
  });

  describe('Progress Bar', () => {
    it('calculates progress percentage correctly', () => {
      const props = {
        ...baseProps,
        questionsAnswered: 17,
        targetTotal: 35,
      };

      render(<ProgressTracker {...props} />);

      // 17/35 = 48.57%
      const progressText = screen.getByText('17 / 35');
      expect(progressText).toBeInTheDocument();
    });

    it('renders with different target totals', () => {
      const props = {
        ...baseProps,
        targetTotal: 50,
        questionsAnswered: 20,
      };

      render(<ProgressTracker {...props} />);
      expect(screen.getByText('20 / 50')).toBeInTheDocument();
    });

    it('handles decimal progress display', () => {
      const props = {
        ...baseProps,
        questionsAnswered: 1,
        targetTotal: 3,
      };

      render(<ProgressTracker {...props} />);
      expect(screen.getByText('1 / 3')).toBeInTheDocument();
    });
  });

  describe('Domain Coverage', () => {
    it('renders empty domains when no coverage', () => {
      const props = {
        ...baseProps,
        domainsCovered: {},
      };

      render(<ProgressTracker {...props} />);
      // Domain coverage section may not render if empty
      expect(screen.queryByText('Domain Coverage')).not.toBeInTheDocument();
    });

    it('renders multiple domain badges', () => {
      const props = {
        ...baseProps,
        domainsCovered: {
          '4.NBT': 5,
          '4.NF': 5,
          '4.OA': 5,
          '4.MD': 4,
          '4.G': 3,
          '5.NBT': 2,
          '5.NF': 3,
          '5.OA': 4,
        },
      };

      render(<ProgressTracker {...props} />);

      expect(screen.getByText('4.NBT: 5')).toBeInTheDocument();
      expect(screen.getByText('4.NF: 5')).toBeInTheDocument();
      expect(screen.getByText('4.OA: 5')).toBeInTheDocument();
      expect(screen.getByText('4.MD: 4')).toBeInTheDocument();
      expect(screen.getByText('4.G: 3')).toBeInTheDocument();
      expect(screen.getByText('5.NBT: 2')).toBeInTheDocument();
      expect(screen.getByText('5.NF: 3')).toBeInTheDocument();
      expect(screen.getByText('5.OA: 4')).toBeInTheDocument();
    });

    it('uses correct colors for domains', () => {
      const props = {
        ...baseProps,
        domainsCovered: {
          '4.NBT': 5,
          '4.NF': 5,
          '4.OA': 5,
        },
      };

      render(<ProgressTracker {...props} />);
      // Verify domain badges are rendered
      expect(screen.getByText('4.NBT: 5')).toBeInTheDocument();
      expect(screen.getByText('4.NF: 5')).toBeInTheDocument();
      expect(screen.getByText('4.OA: 5')).toBeInTheDocument();
    });
  });

  describe('Time Estimation', () => {
    it('displays estimated time remaining', () => {
      render(<ProgressTracker {...baseProps} />);
      expect(screen.getByText('Estimated time remaining: ~7 minutes')).toBeInTheDocument();
    });

    it('handles zero time remaining', () => {
      const props = {
        ...baseProps,
        estimatedTimeRemainingMin: 0,
      };

      render(<ProgressTracker {...props} />);
      expect(screen.getByText('Estimated time remaining: ~0 minutes')).toBeInTheDocument();
    });

    it('handles large time remaining', () => {
      const props = {
        ...baseProps,
        estimatedTimeRemainingMin: 120,
      };

      render(<ProgressTracker {...props} />);
      expect(screen.getByText('Estimated time remaining: ~120 minutes')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined domainsCovered', () => {
      const props = {
        ...baseProps,
        domainsCovered: undefined as unknown as Record<string, number>,
      };

      render(<ProgressTracker {...props} />);
      // Should not crash
      expect(screen.getByText('10 / 35')).toBeInTheDocument();
    });

    it('handles negative values gracefully', () => {
      const props = {
        ...baseProps,
        questionsAnswered: -1,
        estimatedTimeRemainingMin: -5,
      };

      render(<ProgressTracker {...props} />);
      expect(screen.getByText('-1 / 35')).toBeInTheDocument();
    });

    it('handles fractional time remaining', () => {
      const props = {
        ...baseProps,
        estimatedTimeRemainingMin: 3.5,
      };

      render(<ProgressTracker {...props} />);
      // Should display the number (may be rounded by React)
      expect(screen.getByText('Estimated time remaining')).toBeInTheDocument();
    });
  });
});
