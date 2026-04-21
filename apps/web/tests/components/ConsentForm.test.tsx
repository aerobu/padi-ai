import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ConsentForm } from "@/components/assessment/ConsentForm";

// Defensive mock: prevents real network calls if any test is extended to click submit
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    initiateConsent: vi.fn().mockResolvedValue({}),
    post: vi.fn(),
  },
}));

describe("ConsentForm COPPA compliance", () => {
  it("does NOT contain an 'over 13' self-attestation", () => {
    render(<ConsentForm onConsentGranted={vi.fn()} />);
    expect(screen.queryByText(/over 13/i)).toBeNull();
    expect(screen.queryByText(/am 13/i)).toBeNull();
  });

  it("requires parent/guardian attestation", () => {
    render(<ConsentForm onConsentGranted={vi.fn()} />);
    expect(
      screen.getByLabelText(/parent or legal guardian/i)
    ).toBeInTheDocument();
  });

  it("requires explicit data-collection consent", () => {
    render(<ConsentForm onConsentGranted={vi.fn()} />);
    expect(
      screen.getByLabelText(/consent to the collection/i)
    ).toBeInTheDocument();
  });

  it("disables submit until both boxes are checked", () => {
    const onConsentGranted = vi.fn();
    render(<ConsentForm onConsentGranted={onConsentGranted} />);
    const submit = screen.getByRole("button", { name: /consent/i });
    expect(submit).toBeDisabled();

    fireEvent.click(screen.getByLabelText(/parent or legal guardian/i));
    expect(submit).toBeDisabled();

    fireEvent.click(screen.getByLabelText(/consent to the collection/i));
    expect(submit).not.toBeDisabled();
  });
});
