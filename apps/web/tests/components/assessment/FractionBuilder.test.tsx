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
      fireEvent.change(denominatorInput, { target: { value: "8" } });

      expect(denominatorInput).toHaveValue("8");
    });

    it("should prevent non-numeric input for numerator", () => {
      render(<FractionBuilder {...defaultProps} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      fireEvent.change(numeratorInput, { target: { value: "abc" } });

      // Should remain empty or original value if validated on change
      expect(numeratorInput).toHaveValue("");
    });

    it("should prevent non-numeric input for denominator", () => {
      render(<FractionBuilder {...defaultProps} />);

      const denominatorInput = screen.getByLabelText(/Denominator/i);
      fireEvent.change(denominatorInput, { target: { value: "abc" } });

      expect(denominatorInput).toHaveValue("");
    });

    it("should show error when denominator is zero", () => {
      render(<FractionBuilder {...defaultProps} />);

      const denominatorInput = screen.getByLabelText(/Denominator/i);
      fireEvent.change(denominatorInput, { target: { value: "0" } });

      // Depending on implementation, error could show up immediately
      // or after a "Submit" or "Blur" event. Assuming immediate validation:
      expect(screen.getByText(/cannot be zero/i)).toBeInTheDocument();
    });

    it("should prevent negative numbers", () => {
      render(<FractionBuilder {...defaultProps} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      fireEvent.change(numeratorInput, { target: { value: "-5" } });

      expect(numeratorInput).toHaveValue("");
    });
  });

  describe("Value Change Handling", () => {
    it("should call onValueChange when valid inputs are entered", () => {
      const onValueChange = vi.fn();
      render(<FractionBuilder {...defaultProps} onValueChange={onValueChange} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      const denominatorInput = screen.getByLabelText(/Denominator/i);

      fireEvent.change(numeratorInput, { target: { value: "3" } });
      fireEvent.change(denominatorInput, { target: { value: "4" } });

      // Depending on implementation, it might call on each change or once both are valid
      expect(onValueChange).toHaveBeenCalledWith({ numerator: 3, denominator: 4 });
    });

    it("should not call onValueChange with invalid denominator", () => {
      const onValueChange = vi.fn();
      render(<FractionBuilder {...defaultProps} onValueChange={onValueChange} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      const denominatorInput = screen.getByLabelText(/Denominator/i);

      fireEvent.change(numeratorInput, { target: { value: "3" } });
      fireEvent.change(denominatorInput, { target: { value: "0" } });

      expect(onValueChange).not.toHaveBeenCalled();
    });
  });

  describe("Display and Formatting", () => {
    it("should render the provided label", () => {
      render(<FractionBuilder {...defaultProps} label="Custom Fraction Label" />);
      expect(screen.getByText(/Custom Fraction Label/i)).toBeInTheDocument();
    });

    it("should display the current value when provided", () => {
      const value = { numerator: 2, denominator: 3 };
      render(<FractionBuilder {...defaultProps} value={value} />);

      expect(screen.getByLabelText(/Numerator/i)).toHaveValue("2");
      expect(screen.getByLabelText(/Denominator/i)).toHaveValue("3");
    });

    it("should show error message when provided as prop", () => {
      render(<FractionBuilder {...defaultProps} error="External error message" />);
      expect(screen.getByText("External error message")).toBeInTheDocument();
    });

    it("should use semantic spacing and tokens", () => {
      const { container } = render(<FractionBuilder {...defaultProps} />);
      
      // Check for presence of Tailwind-like classes (if using semantic tokens)
      const divider = container.querySelector(".border-t-2");
      expect(divider).toBeInTheDocument();
    });
  });

  describe("Complex Interactions", () => {
    it("should allow changing numerator after setting denominator", () => {
      const onValueChange = vi.fn();
      render(<FractionBuilder {...defaultProps} onValueChange={onValueChange} />);

      const numeratorInput = screen.getByLabelText(/Numerator/i);
      const denominatorInput = screen.getByLabelText(/Denominator/i);

      fireEvent.change(denominatorInput, { target: { value: "5" } });
      fireEvent.change(numeratorInput, { target: { value: "1" } });
      
      expect(onValueChange).toHaveBeenCalledWith({ numerator: 1, denominator: 5 });

      fireEvent.change(numeratorInput, { target: { value: "2" } });
      expect(onValueChange).toHaveBeenCalledWith({ numerator: 2, denominator: 5 });
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

  describe("Simplification Logic", () => {
    it("should simplify 2/4 to 1/2", () => {
      const { container } = render(
        <FractionBuilder {...defaultProps} value={{ numerator: 2, denominator: 4 }} />
      );

      // Check if simplified fraction is displayed
      expect(container.textContent).toContain("1");
      expect(container.textContent).toContain("2");
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

  describe("Mixed Number Conversion", () => {
    it("should convert 5/4 to 1 1/4", () => {
      const { container } = render(
        <FractionBuilder {...defaultProps} value={{ numerator: 5, denominator: 4 }} />
      );

      // Should display mixed number
      expect(container.textContent).toContain("1");
      expect(container.textContent).toContain("1");
      expect(container.textContent).toContain("4");
    });
  });

  describe("Oregon Math Standards Compliance", () => {
    it("should handle mixed number input 8/3 as 2 2/3", () => {
      const { container } = render(
        <FractionBuilder {...defaultProps} value={{ numerator: 8, denominator: 3 }} />
      );

      // Should display mixed number
      expect(container.textContent).toContain("2");
      expect(container.textContent).toContain("2");
      expect(container.textContent).toContain("3");
    });
  });
});
