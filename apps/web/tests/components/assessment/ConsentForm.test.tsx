/**
 * Tests for ConsentForm component
 *
 * COPPA compliance requires explicit parental consent with:
 * - Two checkboxes (age verification + consent acknowledgment)
 * - Both must be checked to submit
 * - Consent token generated and sent via email
 * - Consent record created in database
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import React from "react";
import { ConsentForm } from "@/components/assessment/ConsentForm";
import { apiClient } from "@/lib/api-client";

// Mock the API client
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

describe("ConsentForm", () => {
  const defaultProps = {
    parentId: "parent-123",
    onConsentGranted: vi.fn(),
    onConsentDenied: vi.fn(),
    onError: vi.fn(),
  };

  describe("Form Validation", () => {
    it("should not submit when age checkbox is unchecked", () => {
      render(<ConsentForm {...defaultProps} />);

      // Check consent checkbox only
      const consentCheckbox = screen.getByRole("checkbox", {
        name: /I agree to the terms/i,
      });
      fireEvent.click(consentCheckbox);

      const submitButton = screen.getByRole("button", { name: /Submit/i });
      fireEvent.click(submitButton);

      // Submit should be blocked
      expect(apiClient.post).not.toHaveBeenCalled();
    });

    it("should not submit when consent checkbox is unchecked", () => {
      render(<ConsentForm {...defaultProps} />);

      // Check age checkbox only
      const ageCheckbox = screen.getByRole("checkbox", {
        name: /I am over 13 or have parental permission/i,
      });
      fireEvent.click(ageCheckbox);

      const submitButton = screen.getByRole("button", {
        name: /Submit/i,
      });
      fireEvent.click(submitButton);

      // Submit should be blocked
      expect(apiClient.post).not.toHaveBeenCalled();
    });

    it("should submit when both checkboxes are checked", async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        success: true,
        data: { consentToken: "test-token-123" },
      });

      render(<ConsentForm {...defaultProps} />);

      // Check both checkboxes
      const ageCheckbox = screen.getByRole("checkbox", {
        name: /I am over 13 or have parental permission/i,
      });
      const consentCheckbox = screen.getByRole("checkbox", {
        name: /I agree to the terms/i,
      });

      fireEvent.click(ageCheckbox);
      fireEvent.click(consentCheckbox);

      // Submit
      const submitButton = screen.getByRole("button", { name: /Submit/i });
      fireEvent.click(submitButton);

      // API should be called
      expect(apiClient.post).toHaveBeenCalledWith("/api/v1/coppa/consent", {
        parent_id: "parent-123",
        consent_status: "granted",
      });
    });

    it("should show error when both checkboxes are unchecked", () => {
      render(<ConsentForm {...defaultProps} />);

      const submitButton = screen.getByRole("button", { name: /Submit/i });
      fireEvent.click(submitButton);

      // Should show validation error
      expect(
        screen.getByText(/Please check both boxes to continue/i)
      ).toBeInTheDocument();
    });
  });

  describe("Consent Status Display", () => {
    it("should show granted status when consent is granted", () => {
      render(<ConsentForm {...defaultProps} consentStatus="granted" />);

      expect(
        screen.getByText(/Consent granted/i)
      ).toBeInTheDocument();
    });

    it("should show denied status when consent is denied", () => {
      render(<ConsentForm {...defaultProps} consentStatus="denied" />);

      expect(
        screen.getByText(/Consent denied/i)
      ).toBeInTheDocument();
    });

    it("should show pending status when consent is pending", () => {
      render(<ConsentForm {...defaultProps} consentStatus="pending" />);

      expect(
        screen.getByText(/Consent pending/i)
      ).toBeInTheDocument();
    });
  });

  describe("Loading State", () => {
    it("should show loading state while processing consent", () => {
      render(<ConsentForm {...defaultProps} isLoading={true} />);

      expect(screen.getByText(/Processing.../i)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Submit/i })
      ).toBeDisabled();
    });

    it("should show loading spinner", () => {
      render(<ConsentForm {...defaultProps} isLoading={true} />);

      expect(screen.getByRole("status")).toBeInTheDocument();
    });
  });

  describe("Error Handling", () => {
    it("should show error message when API call fails", () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error("Network error"));

      render(<ConsentForm {...defaultProps} />);

      // Check both checkboxes
      const ageCheckbox = screen.getByRole("checkbox", {
        name: /I am over 13 or have parental permission/i,
      });
      const consentCheckbox = screen.getByRole("checkbox", {
        name: /I agree to the terms/i,
      });

      fireEvent.click(ageCheckbox);
      fireEvent.click(consentCheckbox);

      // Submit
      const submitButton = screen.getByRole("button", { name: /Submit/i });
      fireEvent.click(submitButton);

      // Should show error
      expect(
        screen.getByText(/Failed to submit consent. Please try again/i)
      ).toBeInTheDocument();
    });

    it("should call onError callback when error occurs", async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error("Network error"));

      render(<ConsentForm {...defaultProps} />);

      // Check both checkboxes
      const ageCheckbox = screen.getByRole("checkbox", {
        name: /I am over 13 or have parental permission/i,
      });
      const consentCheckbox = screen.getByRole("checkbox", {
        name: /I agree to the terms/i,
      });

      fireEvent.click(ageCheckbox);
      fireEvent.click(consentCheckbox);

      // Submit
      const submitButton = screen.getByRole("button", { name: /Submit/i });
      fireEvent.click(submitButton);

      // Wait for error to be handled
      await vi.waitFor(() => {
        expect(defaultProps.onError).toHaveBeenCalled();
      });
    });
  });

  describe("Success Handling", () => {
    it("should call onConsentGranted when consent is granted", async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        success: true,
        data: { consentToken: "test-token-123" },
      });

      render(<ConsentForm {...defaultProps} />);

      // Check both checkboxes
      const ageCheckbox = screen.getByRole("checkbox", {
        name: /I am over 13 or have parental permission/i,
      });
      const consentCheckbox = screen.getByRole("checkbox", {
        name: /I agree to the terms/i,
      });

      fireEvent.click(ageCheckbox);
      fireEvent.click(consentCheckbox);

      // Submit
      const submitButton = screen.getByRole("button", { name: /Submit/i });
      fireEvent.click(submitButton);

      // Wait for success
      await vi.waitFor(() => {
        expect(defaultProps.onConsentGranted).toHaveBeenCalled();
      });
    });
  });

  describe("Accessibility", () => {
    it("should have proper labels for checkboxes", () => {
      render(<ConsentForm {...defaultProps} />);

      // Age checkbox should have accessible name
      expect(
        screen.getByRole("checkbox", {
          name: /I am over 13 or have parental permission/i,
        })
      ).toBeInTheDocument();

      // Consent checkbox should have accessible name
      expect(
        screen.getByRole("checkbox", {
          name: /I agree to the terms/i,
        })
      ).toBeInTheDocument();
    });

    it("should have descriptive heading", () => {
      render(<ConsentForm {...defaultProps} />);

      expect(
        screen.getByRole("heading", { name: /Parental Consent/i })
      ).toBeInTheDocument();
    });

    it("should have descriptive error messages", () => {
      render(<ConsentForm {...defaultProps} />);

      const submitButton = screen.getByRole("button", { name: /Submit/i });
      fireEvent.click(submitButton);

      // Error message should be descriptive
      expect(
        screen.getByText(/Please check both boxes to continue/i)
      ).toBeInTheDocument();
    });
  });

  describe("Terms and Privacy Links", () => {
    it("should have link to terms of service", () => {
      render(<ConsentForm {...defaultProps} />);

      expect(
        screen.getByRole("link", { name: /Terms of Service/i })
      ).toBeInTheDocument();
    });

    it("should have link to privacy policy", () => {
      render(<ConsentForm {...defaultProps} />);

      expect(
        screen.getByRole("link", { name: /Privacy Policy/i })
      ).toBeInTheDocument();
    });
  });

  describe("COPPA Compliance", () => {
    it("should require explicit consent (not pre-checked)", () => {
      render(<ConsentForm {...defaultProps} />);

      // Consent checkbox should NOT be pre-checked
      const consentCheckbox = screen.getByRole("checkbox", {
        name: /I agree to the terms/i,
      });

      expect(consentCheckbox).not.toBeChecked();
    });

    it("should require age verification checkbox", () => {
      render(<ConsentForm {...defaultProps} />);

      // Age checkbox should be present
      expect(
        screen.getByRole("checkbox", {
          name: /I am over 13 or have parental permission/i,
        })
      ).toBeInTheDocument();
    });

    it("should generate consent token on submission", async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        success: true,
        data: { consentToken: "test-token-123" },
      });

      render(<ConsentForm {...defaultProps} />);

      // Check both checkboxes
      const ageCheckbox = screen.getByRole("checkbox", {
        name: /I am over 13 or have parental permission/i,
      });
      const consentCheckbox = screen.getByRole("checkbox", {
        name: /I agree to the terms/i,
      });

      fireEvent.click(ageCheckbox);
      fireEvent.click(consentCheckbox);

      // Submit
      const submitButton = screen.getByRole("button", { name: /Submit/i });
      fireEvent.click(submitButton);

      // Should include consent status in request
      expect(apiClient.post).toHaveBeenCalledWith(
        "/api/v1/coppa/consent",
        expect.objectContaining({
          consent_status: "granted",
        })
      );
    });
  });
});
