"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isLoggedIn, getAuthHeader } from "@/app/utils/auth";

import NeoCard from "@/app/components/neo/NeoCard";
import NeoButton from "@/app/components/neo/NeoButton";
import NeoBadge from "@/app/components/neo/NeoBadge";
import { confidenceToTrust } from "@/app/utils/trust";

/* -------------------- Types -------------------- */
type Email = {
  id: number;
  email: string;
  body: string;
  email_type: string;
  confidence_score: number;
  needs_review: boolean;
  created_at: string;
  ai_reason?: string | null;
};

/* -------------------- Helpers -------------------- */
const stripHtml = (html: string) =>
  html.replace(/<[^>]*>?/gm, "");

const getSummary = (email: Email) => {
  if (email.ai_reason && email.ai_reason.trim().length > 0) {
    return email.ai_reason;
  }

  const clean = stripHtml(email.body);
  return clean.split(" ").slice(0, 20).join(" ") + "…";
};

/* -------------------- Page -------------------- */
export default function NeedsReviewPage() {
  const router = useRouter();

  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.push("/login");
      return;
    }

    fetch("http://localhost:8000/emails", {
      headers: {
        ...getAuthHeader(),
      },
    })
      .then((res) => res.json())
      .then((data: Email[]) => {
        setEmails(data.filter((e) => e.needs_review));
      })
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) return <p className="p-10">Loading review queue…</p>;

  return (
    <div className="flex h-screen bg-white text-black overflow-hidden">
      {/* Sidebar */}
      <NeoCard className="m-6 w-[220px] bg-black text-white">
        <h2 className="mb-8 text-lg font-bold">MailMind</h2>

        <nav className="flex flex-col gap-4">
          <button
            className="text-left font-bold text-gray-400 hover:text-white"
            onClick={() => router.push("/dashboard")}
          >
            Inbox
          </button>

          <button className="text-left font-bold text-white">
            Needs Review
          </button>

          <button
            className="text-left text-gray-400 hover:text-white"
            onClick={() => router.push("/dashboard/digest")}
          >
            Digest
          </button>
        </nav>
      </NeoCard>

      {/* Main */}
      <main className="flex-1 p-10 overflow-y-auto">
        <h1 className="mb-6 text-2xl font-bold">
          Needs Review
        </h1>

        {emails.length === 0 && (
          <NeoCard className="bg-black text-gray-400">
            🎉 No emails need review right now.
          </NeoCard>
        )}

        <ul className="list-none p-0">
          {emails.map((email) => {
            const trust = confidenceToTrust(
              email.confidence_score
            );

            return (
              <li key={email.id} className="mb-6">
                <NeoCard className="bg-black text-white">
                  <div className="font-bold mb-2">
                    {email.email}
                  </div>

                  <div className="mb-3 text-gray-300">
                    {getSummary(email)}
                  </div>

                  <div className="flex justify-between items-center text-sm text-gray-400">
                    <span className="border-2 border-gray-500 px-2 py-1">
                      {email.email_type.toUpperCase()}
                    </span>

                    <NeoBadge
                      label={trust.label}
                      tone={trust.tone}
                    />
                  </div>
                </NeoCard>
              </li>
            );
          })}
        </ul>
      </main>
    </div>
  );
}
