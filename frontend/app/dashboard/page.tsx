"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isLoggedIn, clearToken, getAuthHeader } from "@/app/utils/auth";


type Email = {
  id: number;
  email: string;              // sender
  body: string;               // raw email body (HTML)
  email_type: string;         // marketing | support | newsletter
  confidence_score: number;
  needs_review: boolean;
  created_at: string;
};


const stripHtml = (html: string) =>
  html.replace(/<[^>]*>?/gm, "");


export default function DashboardPage() {
  const router = useRouter();

  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


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
      .then((data: Email[]) => {
        setEmails(data);
      })
      .catch(() => {
        setError("Could not load emails");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [router]);

 
  const logout = () => {
    clearToken();
    router.push("/login");
  };

  
  if (loading) return <p style={{ padding: "40px" }}>Loading emails…</p>;
  if (error) return <p style={{ padding: "40px" }}>{error}</p>;


  return (
    <div style={{ padding: "40px", maxWidth: "900px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h1>Inbox</h1>
        <button onClick={logout}>Logout</button>
      </div>

      {/* Empty State */}
      {emails.length === 0 && (
        <p>No emails ingested yet.</p>
      )}

      {/* Email List */}
      <ul style={{ listStyle: "none", padding: 0 }}>
        {emails.map((email) => (
          <li
            key={email.id}
            style={{
              border: "1px solid #333",
              padding: "16px",
              marginBottom: "16px",
            }}
          >
            {/* Sender */}
            <strong>{email.email}</strong>

            {/* Preview */}
            <p style={{ margin: "8px 0" }}>
              {stripHtml(email.body).slice(0, 150)}…
            </p>

            {/* Meta */}
            <div style={{ fontSize: "14px", opacity: 0.8 }}>
              <span>
                {email.email_type.toUpperCase()}
              </span>
              {" • "}
              <span>
                Confidence: {(email.confidence_score * 100).toFixed(0)}%
              </span>
              {email.needs_review && (
                <span style={{ color: "red" }}> • Needs Review</span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
