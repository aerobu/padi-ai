"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@padi/ui/button";
import { Input } from "@padi/ui/input";
import { Divider } from "@padi/ui/divider";

interface FormData {
  firstName: string;
  gradeLevel: number;
  birthYear: number;
}

const gradeLevels = [
  { value: 1, label: "1st Grade" },
  { value: 2, label: "2nd Grade" },
  { value: 3, label: "3rd Grade" },
  { value: 4, label: "4th Grade" },
  { value: 5, label: "5th Grade" },
];

export default function CreateStudentPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<FormData>({
    firstName: "",
    gradeLevel: 4,
    birthYear: new Date().getFullYear() - 9,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    router.push("/dashboard");
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="font-display text-display-md text-neutral-900">Create Your Child&apos;s Profile</h1>
        <p className="mt-2 text-[16px] text-neutral-500">Please enter your child&apos;s information to get started with PADI.AI.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <Input
          label="First Name"
          placeholder="Enter first name"
          value={formData.firstName}
          onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
        />
        <p className="text-[12px] text-neutral-400 ml-1">We&apos;ll use the first name only to protect your child&apos;s privacy.</p>

        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-[.08em] text-neutral-500 mb-2">Grade Level</label>
          <select
            value={formData.gradeLevel}
            onChange={(e) => setFormData({ ...formData, gradeLevel: parseInt(e.target.value, 10) })}
            className="w-full h-[44px] rounded-md border-[1.5px] border-neutral-300 bg-surface-cream px-3 text-[14px] text-neutral-800 focus:border-green-500 focus:ring-3 focus:ring-green-500/10 outline-none"
          >
            {gradeLevels.map((g) => (
              <option key={g.value} value={g.value}>{g.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-[.08em] text-neutral-500 mb-2">Birth Year</label>
          <select
            value={formData.birthYear}
            onChange={(e) => setFormData({ ...formData, birthYear: parseInt(e.target.value, 10) })}
            className="w-full h-[44px] rounded-md border-[1.5px] border-neutral-300 bg-surface-cream px-3 text-[14px] text-neutral-800 focus:border-green-500 focus:ring-3 focus:ring-green-500/10 outline-none"
          >
            {Array.from({ length: 17 }, (_, i) => new Date().getFullYear() - (6 + i)).map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>

        <Divider />
        <div className="flex gap-3">
          <Button size="sm" variant="outline" onClick={() => router.push("/onboarding/consent")}>
            Back
          </Button>
          <Button size="lg" type="submit" className="flex-1">
            Create Profile
          </Button>
        </div>
      </form>
    </div>
  );
}
