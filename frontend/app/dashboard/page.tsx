"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isLoggedIn, clearToken, getAuthHeader } from "@/app/utils/auth";

import NeoCard from "@/app/components/neo/NeoCard";
import NeoButton from "@/app/components/neo/NeoButton";
import NeoBadge from "@/app/components/neo/NeoBadge";
import { confidenceToTrust } from "@/app/utils/trust";


type Email = {
  id: number;
  email: string;
  body: string;
  email_type: string;
  confidence_score: number;
  needs_review: boolean;
  has_structured_data?: boolean;
  created_at: string;
  ai_reason?: string | null;
};


const stripHtml = (html: string) =>
  html.replace(/<[^>]*>?/gm, "");

const confidenceColor = (score: number) => {
  if (score >= 0.85) return "#00ff88";
  if (score >= 0.7) return "#ffd700";
  return "#ff4d4d";
};

const getSummary = (email: Email) => {
  if (email.ai_reason && email.ai_reason.trim().length > 0) {
    return email.ai_reason;
  }

  const clean = stripHtml(email.body);
  return clean.split(" ").slice(0, 20).join(" ") + "…";
};


export default function DashboardPage() {
  const router = useRouter();

  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [overrideCategory, setOverrideCategory] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  const [nextPageToken, setNextPageToken] = useState<string | null>(null);

  const [trustFilter, setTrustFilter] = useState<
    "Auto" | "Suggested" | "Required" | null
  >(null);

  const [categoryFilter, setCategoryFilter] = useState<
    "marketing" | "support" | "newsletter" | null
  >(null);

 
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
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch emails");
        return res.json();
      })
      .then((data) => {
       
        if (Array.isArray(data)) {
          setEmails(data);
          setNextPageToken(null);
        } else {
          setEmails(data.emails ?? []);
          setNextPageToken(data.nextPageToken ?? null);
        }
      })
      .catch(() => {
        setError("Could not load emails");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [router]);

  
  const loadMoreEmails = async () => {
    if (!nextPageToken || loadingMore) return;

    setLoadingMore(true);

    try {
      const res = await fetch(
        `http://localhost:8000/emails?pageToken=${nextPageToken}`,
        {
          headers: {
            ...getAuthHeader(),
          },
        }
      );

      if (!res.ok) throw new Error("Failed");

      const data = await res.json();

      if (!Array.isArray(data?.emails)) {
        throw new Error("Invalid pagination response");
      }

      setEmails((prev) => [...prev, ...data.emails]);
      setNextPageToken(data.nextPageToken ?? null);
    } catch {
      alert("Failed to load more emails");
    } finally {
      setLoadingMore(false);
    }
  };

  
  const filteredEmails = emails.filter((email) => {
    const trust = confidenceToTrust(email.confidence_score);

    if (trustFilter && trust.label !== trustFilter) return false;
    if (categoryFilter && email.email_type !== categoryFilter) return false;

    return true;
  });

  
  const saveOverride = async () => {
    if (!selectedEmail || !overrideCategory) return;

    try {
      const res = await fetch(
        `http://localhost:8000/emails/${selectedEmail.id}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeader(),
          },
          body: JSON.stringify({
            email_type: overrideCategory,
          }),
        }
      );

      if (!res.ok) throw new Error("Failed");

      setEmails((prev) =>
        prev.map((email) =>
          email.id === selectedEmail.id
            ? {
                ...email,
                email_type: overrideCategory,
                needs_review: false,
              }
            : email
        )
      );

      setSelectedEmail(null);
    } catch {
      alert("Failed to save override");
    }
  };

  const logout = () => {
    clearToken();
    router.push("/login");
  };

  if (loading) return <p className="p-10">Loading emails…</p>;
  if (error) return <p className="p-10">{error}</p>;

  
  return (
    <div className="flex h-screen bg-white text-black overflow-hidden">
     
      <NeoCard className="m-6 w-[220px] bg-black text-white">
        <h2 className="mb-8 text-lg font-bold">MailMind</h2>

        <nav className="flex flex-col gap-4">
          <button
            className="text-left font-bold text-white"
            onClick={() => router.push("/dashboard")}
          >
            Inbox
          </button>

          <button
            className="text-left font-bold text-gray-400 hover:text-white"
            onClick={() => router.push("/dashboard/review")}
          >
            Needs Review
          </button>

          <button
            className="text-left text-gray-400 hover:text-white"
            onClick={() => router.push("/dashboard/digest")}
          >
            Digest
          </button>

          <NeoButton onClick={logout} className="mt-4">
            Logout
          </NeoButton>
        </nav>
      </NeoCard>

      
      <main className="flex-1 p-10 overflow-y-auto">
        <h1 className="mb-6 text-2xl font-bold">Inbox</h1>

        <ul className="list-none p-0">
          {filteredEmails.map((email) => {
            const trust = confidenceToTrust(email.confidence_score);

            return (
              <li
                key={email.id}
                onClick={() => {
                  setSelectedEmail(email);
                  setOverrideCategory(email.email_type);
                }}
                className="mb-6 cursor-pointer"
              >
                <NeoCard
                  className="bg-black text-white"
                  style={{
                    borderColor: confidenceColor(email.confidence_score),
                  }}
                >
                  <div className="font-bold mb-2">{email.email}</div>

                  <div className="mb-3 text-gray-300">
                    {getSummary(email)}
                  </div>

                  <div className="flex justify-between items-center text-sm text-gray-400">
                    <span className="border-2 border-gray-500 px-2 py-1">
                      {email.email_type.toUpperCase()}
                    </span>

                    <NeoBadge label={trust.label} tone={trust.tone} />
                  </div>
                </NeoCard>
              </li>
            );
          })}
        </ul>

        
        {nextPageToken && (
          <div className="mt-8 flex justify-center">
            <NeoButton onClick={loadMoreEmails} disabled={loadingMore}>
              {loadingMore ? "Loading…" : "Load More"}
            </NeoButton>
          </div>
        )}
      </main>

    
      {selectedEmail && (() => {
        const trust = confidenceToTrust(selectedEmail.confidence_score);

        return (
          <div className="fixed top-0 right-0 w-[420px] h-screen bg-black border-l-4 border-gray-700 p-6 overflow-y-auto z-50 text-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">Email Review</h3>
              <NeoBadge label={trust.label} tone={trust.tone} />
            </div>

            <NeoCard className="bg-black text-gray-300 mb-4">
              <strong>AI Summary</strong>
              <p className="mt-2">{getSummary(selectedEmail)}</p>
            </NeoCard>

            <label className="block mb-1 text-sm">
              Override Category
            </label>

            <select
              value={overrideCategory ?? ""}
              onChange={(e) => setOverrideCategory(e.target.value)}
              className="w-full p-2 bg-black text-white border-2 border-gray-500"
            >
              <option value="marketing">Marketing</option>
              <option value="support">Support</option>
              <option value="newsletter">Newsletter</option>
            </select>

            <NeoButton
              onClick={saveOverride}
              disabled={overrideCategory === selectedEmail.email_type}
              className="mt-4 w-full"
            >
              Save Override
            </NeoButton>
          </div>
        );
      })()}
    </div>
  );
}
