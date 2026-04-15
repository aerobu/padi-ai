/**
 * Tests for FractionBuilder component
 *
 * Oregon math standards require students to demonstrate fraction understanding
 * through interactive fraction builder UI that:
 * - Validates numerator input (positive integers only)
 * - Validates denominator input (positive integers, cannot be zero)
 * - Prevents invalid fractions (denominator = 0)
 * - Supports numeric and decimal inputs
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import React from "react";
import { FractionBuilder } from "@/components/assessment/FractionBuilder";

// Mock component props
const defaultProps = {
  onValueChange: vi.fn(),
  value: null,
  error: null,
  label: "Enter your answer",
};

describe("FractionBuilder", () => {
  describe("Input Validation", () => {
    it("should allow positive integer numerator input", () => {
      render(<FractionBuilder {...defaultProps} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      fireEvent.change(numeratorInput, { target: { value: "5" } });

      expect(numeratorInput).toHaveValue("5");
    });

    it("should allow positive integer denominator input", () => {
      render(<FractionBuilder {...defaultProps} />);

      const denominatorInput = screen.getByLabelText(/Denominator/i);
      fireEvent.change(denominatorInput, { target: { value: "3" } });

      expect(denominatorInput).toHaveValue("3");
    });

    it("should prevent zero denominator", () => {
      render(<FractionBuilder {...defaultProps} />);

      const denominatorInput = screen.getByLabelText(/Denominator/i);
      fireEvent.change(denominatorInput, { target: { value: "0" } });

      // Should show error or prevent submission
      expect(
        screen.getByText(/Denominator cannot be zero/i)
      ).toBeInTheDocument();
    });

    it("should prevent negative numbers", () => {
      render(<FractionBuilder {...defaultProps} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      fireEvent.change(numeratorInput, { target: { value: "-5" } });

      // Should show error or be prevented
      expect(
        screen.getByText(/Please enter a positive number/i)
      ).toBeInTheDocument();
    });

    it("should prevent non-numeric input", () => {
      render(<FractionBuilder {...defaultProps} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      fireEvent.change(numeratorInput, { target: { value: "abc" } });

      // Should show error or be prevented
      expect(
        screen.getByText(/Please enter a valid number/i)
      ).toBeInTheDocument();
    });

    it("should allow empty input (no default value)", () => {
      render(<FractionBuilder {...defaultProps} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      const denominatorInput = screen.getByLabelText(/Denominator/i);

      // Should allow empty inputs
      expect(numeratorInput).toHaveValue("");
      expect(denominatorInput).toHaveValue("");
    });
  });

  describe("Fraction Display", () => {
    it("should display fraction in standard notation", () => {
      render(<FractionBuilder {...defaultProps} value={{ numerator: 3, denominator: 4 }} />);

      expect(screen.getByText(/3/i)).toBeInTheDocument();
      expect(screen.getByText(/4/i)).toBeInTheDocument();
    });

    it("should display simplified fraction", () => {
      render(<FractionBuilder {...defaultProps} value={{ numerator: 2, denominator: 4 }} />);

      // Should show simplified form (1/2)
      expect(screen.getByText(/1/i)).toBeInTheDocument();
      expect(screen.getByText(/2/i)).toBeInTheDocument();
    });

    it("should display mixed number when numerator > denominator", () => {
      render(<FractionBuilder {...defaultProps} value={{ numerator: 5, denominator: 4 }} />);

      // Should show 1 1/4
      expect(screen.getByText(/1/i)).toBeInTheDocument();
      expect(screen.getByText(/1/i)).toBeInTheDocument();
      expect(screen.getByText(/4/i)).toBeInTheDocument();
    });

    it("should display whole number when denominator = 1", () => {
      render(<FractionBuilder {...defaultProps} value={{ numerator: 5, denominator: 1 }} />);

      // Should show just 5
      expect(screen.getByText(/5/i)).toBeInTheDocument();
    });
  });

  describe("Submit Button", () => {
    it("should be disabled when no value entered", () => {
      render(<FractionBuilder {...defaultProps} />);

      const submitButton = screen.getByRole("button", { name: /Submit/i });
      expect(submitButton).toBeDisabled();
    });

    it("should be disabled when denominator is zero", () => {
      render(<FractionBuilder {...defaultProps} value={{ numerator: 5, denominator: 0 }} />);

      const submitButton = screen.getByRole("button", { name: /Submit/i });
      expect(submitButton).toBeDisabled();
    });

    it("should be disabled when numerator is negative", () => {
      render(<FractionBuilder {...defaultProps} value={{ numerator: -5, denominator: 3 }} />);

      const submitButton = screen.getByRole("button", { name: /Submit/i });
      expect(submitButton).toBeDisabled();
    });

    it("should be enabled when valid fraction entered", () => {
      render(
        <FractionBuilder {...defaultProps} value={{ numerator: 3, denominator: 4 }} />
      );

      const submitButton = screen.getByRole("button", { name: /Submit/i });
      expect(submitButton).not.toBeDisabled();
    });

    it("should call onValueChange when submit clicked", () => {
      render(
        <FractionBuilder {...defaultProps} value={{ numerator: 3, denominator: 4 }} />
      );

      const submitButton = screen.getByRole("button", { name: /Submit/i });
      fireEvent.click(submitButton);

      expect(defaultProps.onValueChange).toHaveBeenCalledWith({
        numerator: 3,
        denominator: 4,
      });
    });
  });

  describe("Error Handling", () => {
    it("should display validation error when denominator is zero", () => {
      render(
        <FractionBuilder {...defaultProps} value={{ numerator: 5, denominator: 0 }} />
      );

      expect(
        screen.getByText(/Denominator cannot be zero/i)
      ).toBeInTheDocument();
    });

    it("should display validation error for negative numerator", () => {
      render(
        <FractionBuilder {...defaultProps} value={{ numerator: -5, denominator: 4 }} />
      );

      expect(
        screen.getByText(/Numerator must be positive/i)
      ).toBeInTheDocument();
    });

    it("should display validation error for negative denominator", () => {
      render(
        <FractionBuilder {...defaultProps} value={{ numerator: 5, denominator: -4 }} />
      );

      expect(
        screen.getByText(/Denominator must be positive/i)
      ).toBeInTheDocument();
    });

    it("should display custom error prop when provided", () => {
      render(<FractionBuilder {...defaultProps} error="Custom error message" />);

      expect(screen.getByText(/Custom error message/i)).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("should have accessible labels for numerator input", () => {
      render(<FractionBuilder {...defaultProps} />);

      expect(screen.getByLabelText(/Numerator/i)).toBeInTheDocument();
    });

    it("should have accessible labels for denominator input", () => {
      render(<FractionBuilder {...defaultProps} />);

      expect(screen.getByLabelText(/Denominator/i)).toBeInTheDocument();
    });

    it("should have descriptive heading", () => {
      render(<FractionBuilder {...defaultProps} />);

      expect(screen.getByRole("heading", { name: /Fraction Builder/i })).toBeInTheDocument();
    });

    it("should have accessible error messages", () => {
      render(<FractionBuilder {...defaultProps} value={{ numerator: 5, denominator: 0 }} />);

      const errorElement = screen.getByText(/Denominator cannot be zero/i);
      expect(errorElement).toHaveAttribute("role", "alert");
    });
  });

  describe("Input Types", () => {
    it("should accept numeric input for numerator", () => {
      render(<FractionBuilder {...defaultProps} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      fireEvent.change(numeratorInput, { target: { value: "100" } });

      expect(numeratorInput).toHaveValue("100");
    });

    it("should accept numeric input for denominator", () => {
      render(<FractionBuilder {...defaultProps} />);

      const denominatorInput = screen.getByLabelText(/Denominator/i);
      fireEvent.change(denominatorInput, { target: { value: "1000" } });

      expect(denominatorInput).toHaveValue("1000");
    });

    it("should handle large numbers", () => {
      render(<FractionBuilder {...defaultProps} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      const denominatorInput = screen.getByLabelText(/Denominator/i);

      fireEvent.change(numeratorInput, { target: { value: "999999" } });
      fireEvent.change(denominatorInput, { target: { value: "999999" } });

      expect(numeratorInput).toHaveValue("999999");
      expect(denominatorInput).toHaveValue("999999");
    });
  });

  describe "Simplification Logic", () => {
    it("should simplify 2/4 to 1/2", () => {
      const { container } = render(
        <FractionBuilder {...defaultProps} value={{ numerator: 2, denominator: 4 }} />
      );

      // Check if simplified fraction is displayed
      expect(container.textContent).toContain("1");
      expect(container.textContent).toContain("2");
    });

    it("should simplify 6/8 to 3/4", () => {
      const { container } = render(
        <FractionBuilder {...defaultProps} value={{ numerator: 6, denominator: 8 }} />
      );

      // Check if simplified fraction is displayed
      expect(container.textContent).toContain("3");
      expect(container.textContent).toContain("4");
    });

    it("should handle already simplified fractions", () => {
      const { container } = render(
        <FractionBuilder {...defaultProps} value={{ numerator: 3, denominator: 5 }} />
      );

      // Should display 3/5 unchanged
      expect(container.textContent).toContain("3");
      expect(container.textContent).toContain("5");
    });
  });

  describe "Mixed Number Conversion", () => {
    it("should convert 5/4 to 1 1/4", () => {
      const { container } = render(
        <FractionBuilder {...defaultProps} value={{ numerator: 5, denominator: 4 }} />
      );

      // Should display mixed number
      expect(container.textContent).toContain("1");
      expect(container.textContent).toContain("1");
      expect(container.textContent).toContain("4");
    });

    it("should convert 8/3 to 2 2/3", () => {
      const { container } = render(
        <FractionBuilder {...defaultProps} value={{ numerator: 8, denominator: 3 }} />
      );

      // Should display mixed number
      expect(container.textContent).toContain("2");
      expect(container.textContent).toContain("2");
      expect(container.textContent).toContain("3");
    });
  });

  describe "Oregon Math Standards Compliance", () => {
    it("should support Grade 4 fraction standards (4.NF.A.1)", () => {
      // Test explains equivalent fractions
      render(
        <FractionBuilder {...defaultProps} value={{ numerator: 1, denominator: 2 }} />
      );

      // Should allow entering 2/4 as equivalent to 1/2
      const numeratorInput = screen.getByLabelText(/Numerator/i);
      const denominatorInput = screen.getByLabelText(/Denominator/i);

      fireEvent.change(numeratorInput, { target: { value: "2" } });
      fireEvent.change(denominatorInput, { target: { value: "4" } });

      expect(numeratorInput).toHaveValue("2");
      expect(denominatorInput).toHaveValue("4");
    });

    it("should support Grade 4 fraction comparison (4.NF.A.2)", () => {
      // Test comparison of fractions with different denominators
      render(
        <FractionBuilder {...defaultProps} value={{ numerator: 3, denominator: 4 }} />
      );

      // Should display 3/4 correctly
      expect(screen.getByText(/3/i)).toBeInTheDocument();
      expect(screen.getByText(/4/i)).toBeInTheDocument();
    });
  });
});
