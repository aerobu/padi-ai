/**
 * Create Student page.
 * Parent creates their child&apos;s profile after consent.
 */

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@padi/ui";

interface FormData {
  firstName: string;
  gradeLevel: number;
  birthYear: number;
}

export default function CreateStudentPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>({
    firstName: "",
    gradeLevel: 4,
    birthYear: new Date().getFullYear() - 9,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Create student via API
      const response = await fetch("/api/v1/students", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          display_name: formData.firstName,
          grade_level: formData.gradeLevel,
          birth_year: formData.birthYear,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to create student");
      }

      // Navigate to dashboard
      router.push("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create student profile"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const gradeLevels = [
    { value: 1, label: "1st Grade" },
    { value: 2, label: "2nd Grade" },
    { value: 3, label: "3rd Grade" },
    { value: 4, label: "4th Grade" },
    { value: 5, label: "5th Grade" },
  ];

  const currentYear = new Date().getFullYear();
  const birthYearOptions = Array.from(
    { length: 17 },
    (_, i) => currentYear - (6 + i)
  );

  return (
    <div className="bg-white rounded-lg shadow-md p-6 md:p-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">
        Create Your Child&apos;s Profile
      </h1>
      <p className="text-slate-600 mb-6">
        Please enter your child&apos;s information to get started with PADI.AI.
      </p>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* First Name */}
        <div>
          <label
            htmlFor="firstName"
            className="block text-sm font-medium text-slate-700 mb-1"
          >
            First Name
          </label>
          <input
            type="text"
            id="firstName"
            required
            value={formData.firstName}
            onChange={(e) =>
              setFormData({ ...formData, firstName: e.target.value })
            }
            className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter first name"
          />
          <p className="mt-1 text-sm text-slate-500">
            We&apos;ll use the first name only to protect your child&apos;s privacy.
          </p>
        </div>

        {/* Grade Level */}
        <div>
          <label
            htmlFor="gradeLevel"
            className="block text-sm font-medium text-slate-700 mb-1"
          >
            Grade Level
          </label>
          <select
            id="gradeLevel"
            required
            value={formData.gradeLevel}
            onChange={(e) =>
              setFormData({
                ...formData,
                gradeLevel: parseInt(e.target.value, 10),
              })
            }
            className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            {gradeLevels.map((grade) => (
              <option key={grade.value} value={grade.value}>
                {grade.label}
              </option>
            ))}
          </select>
        </div>

        {/* Birth Year */}
        <div>
          <label
            htmlFor="birthYear"
            className="block text-sm font-medium text-slate-700 mb-1"
          >
            Birth Year
          </label>
          <select
            id="birthYear"
            required
            value={formData.birthYear}
            onChange={(e) =>
              setFormData({
                ...formData,
                birthYear: parseInt(e.target.value, 10),
              })
            }
            className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            {birthYearOptions.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end space-x-4 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push("/onboarding/consent")}
            disabled={isLoading}
          >
            Back
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? "Creating..." : "Create Profile"}
          </Button>
        </div>
      </form>
    </div>
  );
}
