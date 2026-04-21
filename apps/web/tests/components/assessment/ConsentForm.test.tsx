/**
 * Tests for ConsentForm component
 *
 * COPPA compliance requires explicit parental consent with:
 * - Two checkboxes (parent/guardian attestation + data-collection consent)
 * - Both must be checked to submit
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
    initiateConsent: vi.fn(),
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
    it("should not submit when parent/guardian checkbox is unchecked", () => {
      render(<ConsentForm {...defaultProps} />);

      // Check data consent checkbox only
      const dataConsentCheckbox = screen.getByLabelText(
        /consent to the collection/i
      );
      fireEvent.click(dataConsentCheckbox);

      const submitButton = screen.getByRole("button", { name: /consent/i });
      expect(submitButton).toBeDisabled();
    });

    it("should not submit when data consent checkbox is unchecked", () => {
      render(<ConsentForm {...defaultProps} />);

      // Check parent/guardian checkbox only
      const parentCheckbox = screen.getByLabelText(
        /parent or legal guardian/i
      );
      fireEvent.click(parentCheckbox);

      const submitButton = screen.getByRole("button", { name: /consent/i });
      expect(submitButton).toBeDisabled();
    });

    it("should enable submit when both checkboxes are checked", async () => {
      vi.mocked(apiClient.initiateConsent).mockResolvedValue({
        success: true,
      } as any);

      render(<ConsentForm {...defaultProps} />);

      const parentCheckbox = screen.getByLabelText(/parent or legal guardian/i);
      const dataConsentCheckbox = screen.getByLabelText(
        /consent to the collection/i
      );

      fireEvent.click(parentCheckbox);
      fireEvent.click(dataConsentCheckbox);

      const submitButton = screen.getByRole("button", { name: /consent/i });
      expect(submitButton).not.toBeDisabled();
    });

    it("should show error when handleSubmit is called with unchecked boxes", () => {
      const { container } = render(<ConsentForm {...defaultProps} />);

      // Bypass the disabled button by submitting the form directly
      const form = container.querySelector("form");
      fireEvent.submit(form!);

      expect(
        screen.getByText(/please check both boxes to continue/i)
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
    });

    it("should show loading spinner", () => {
      render(<ConsentForm {...defaultProps} isLoading={true} />);

      expect(screen.getByRole("status")).toBeInTheDocument();
    });
  });

  describe("Success Handling", () => {
    it("should call onConsentGranted when consent is granted", async () => {
      vi.mocked(apiClient.initiateConsent).mockResolvedValue({
        success: true,
      } as any);

      render(<ConsentForm {...defaultProps} />);

      const parentCheckbox = screen.getByLabelText(/parent or legal guardian/i);
      const dataConsentCheckbox = screen.getByLabelText(
        /consent to the collection/i
      );

      fireEvent.click(parentCheckbox);
      fireEvent.click(dataConsentCheckbox);

      const submitButton = screen.getByRole("button", { name: /consent/i });
      fireEvent.click(submitButton);

      await vi.waitFor(() => {
        expect(defaultProps.onConsentGranted).toHaveBeenCalled();
      });
    });
  });

  describe("Accessibility", () => {
    it("should have proper labels for checkboxes", () => {
      render(<ConsentForm {...defaultProps} />);

      expect(
        screen.getByLabelText(/parent or legal guardian/i)
      ).toBeInTheDocument();

      expect(
        screen.getByLabelText(/consent to the collection/i)
      ).toBeInTheDocument();
    });

    it("should have descriptive heading", () => {
      render(<ConsentForm {...defaultProps} />);

      expect(
        screen.getByRole("heading", { name: /Parental Consent/i })
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

      const privacyLinks = screen.getAllByRole("link", {
        name: /Privacy Policy/i,
      });
      expect(privacyLinks.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("COPPA Compliance", () => {
    it("should NOT contain any 'over 13' self-attestation text", () => {
      render(<ConsentForm {...defaultProps} />);

      expect(screen.queryByText(/over 13/i)).toBeNull();
      expect(screen.queryByText(/am 13/i)).toBeNull();
    });

    it("should require explicit consent (not pre-checked)", () => {
      render(<ConsentForm {...defaultProps} />);

      const parentCheckbox = screen.getByLabelText(/parent or legal guardian/i);
      const dataConsentCheckbox = screen.getByLabelText(
        /consent to the collection/i
      );

      expect(parentCheckbox).not.toBeChecked();
      expect(dataConsentCheckbox).not.toBeChecked();
    });
  });

  describe("Error Handling", () => {
    it("should show error message when API call fails", async () => {
      vi.mocked(apiClient.initiateConsent).mockRejectedValueOnce(
        new Error("Network error")
      );
      render(<ConsentForm parentId="p1" />);
      fireEvent.click(screen.getByLabelText(/parent or legal guardian/i));
      fireEvent.click(screen.getByLabelText(/consent to the collection/i));
      fireEvent.click(screen.getByRole("button", { name: /consent/i }));
      expect(await screen.findByText(/failed to submit consent/i)).toBeInTheDocument();
    });

    it("should call onError callback when error occurs", async () => {
      const onError = vi.fn();
      vi.mocked(apiClient.initiateConsent).mockRejectedValueOnce(
        new Error("Network error")
      );
      render(<ConsentForm parentId="p1" onError={onError} />);
      fireEvent.click(screen.getByLabelText(/parent or legal guardian/i));
      fireEvent.click(screen.getByLabelText(/consent to the collection/i));
      fireEvent.click(screen.getByRole("button", { name: /consent/i }));
      await screen.findByText(/failed to submit consent/i);
      expect(onError).toHaveBeenCalledWith(expect.any(String));
    });
  });
});
