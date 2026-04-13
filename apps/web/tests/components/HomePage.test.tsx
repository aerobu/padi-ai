import { render, screen } from '@testing-library/react';
import HomePage from '../../app/(public)/page';

describe('HomePage', () => {
  it('renders navigation with PADI.AI branding', () => {
    render(<HomePage />);

    const branding = screen.getByText('PADI.AI');
    expect(branding).toBeInTheDocument();
    expect(branding).toHaveClass('text-2xl', 'font-bold', 'text-padiGreen-600');
  });

  it('renders Sign In button in navigation', () => {
    render(<HomePage />);

    const signInButton = screen.getByText('Sign In');
    expect(signInButton).toBeInTheDocument();
    expect(signInButton.closest('a')).toHaveAttribute('href', '/(auth)/login');
  });

  it('renders Get Started button in navigation', () => {
    render(<HomePage />);

    const getStartedButton = screen.getByText('Get Started');
    expect(getStartedButton).toBeInTheDocument();
    expect(getStartedButton.closest('a')).toHaveAttribute('href', '/(auth)/login');
  });

  it('renders main headline with correct messaging', () => {
    render(<HomePage />);

    const headline = screen.getByText(/Adaptive Math Learning/);
    expect(headline).toBeInTheDocument();

    const subhead = screen.getByText(/for Oregon Students/);
    expect(subhead).toBeInTheDocument();
  });

  it('renders description text', () => {
    render(<HomePage />);

    const description = screen.getByText(
      /Personalized AI-powered learning that helps 4th graders master math concepts/
    );
    expect(description).toBeInTheDocument();
  });

  it('renders CTA buttons', () => {
    render(<HomePage />);

    const startLearningButton = screen.getByText('Start Learning');
    expect(startLearningButton).toBeInTheDocument();
    expect(startLearningButton.closest('a')).toHaveAttribute('href', '/(auth)/login');

    const learnMoreButton = screen.getByText('Learn More');
    expect(learnMoreButton).toBeInTheDocument();
    expect(learnMoreButton.closest('a')).toHaveAttribute('href', '/(auth)/login');
  });

  it('renders all three feature cards', () => {
    render(<HomePage />);

    const adaptiveFeature = screen.getByText('Adaptive Learning');
    expect(adaptiveFeature).toBeInTheDocument();

    const standardsFeature = screen.getByText('Standards Aligned');
    expect(standardsFeature).toBeInTheDocument();

    const coppaFeature = screen.getByText('COPPA Compliant');
    expect(coppaFeature).toBeInTheDocument();
  });

  it('renders feature descriptions', () => {
    render(<HomePage />);

    const adaptiveDescription = screen.getByText(
      /AI-powered tutoring that adjusts to each student.*needs in real-time/
    );
    expect(adaptiveDescription).toBeInTheDocument();

    const standardsDescription = screen.getByText(
      /Content mapped to Oregon math standards for grades 1-5/
    );
    expect(standardsDescription).toBeInTheDocument();

    const coppaDescription = screen.getByText(
      /Privacy-first design with local LLM processing for student data/
    );
    expect(coppaDescription).toBeInTheDocument();
  });

  it('renders footer with copyright', () => {
    render(<HomePage />);

    const footer = screen.getByText(/© 2026 PADI.AI/);
    expect(footer).toBeInTheDocument();
  });

  it('has correct page structure', () => {
    render(<HomePage />);

    // Check for main layout elements
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();
  });
});
