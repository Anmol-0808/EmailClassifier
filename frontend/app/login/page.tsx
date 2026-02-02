"use client";

import NeoButton from "@/app/components/neo/NeoButton";
import NeoCard from "@/app/components/neo/NeoCard";

export default function LoginPage() {
  const handleLogin = () => {
    window.location.href = "http://localhost:8000/auth/google/login";
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <NeoCard className="w-full max-w-md bg-black text-white border-white">
        <div className="flex flex-col gap-6">
          {/* Header */}
          <div className="flex flex-col gap-2">
            <h1 className="text-3xl font-bold text-white">
              MailMind
            </h1>
            <p className="text-sm text-gray-300">
              An AI-powered inbox with trust-based email classification
            </p>
          </div>

          {/* CTA */}
          <NeoButton
            onClick={handleLogin}
            className="w-full py-3 text-base"
          >
            Continue with Google
          </NeoButton>

          {/* Trust line */}
          <p className="text-xs text-gray-400">
            Secure Google authentication. We never read your emails without permission.
          </p>
        </div>
      </NeoCard>
    </div>
  );
}
