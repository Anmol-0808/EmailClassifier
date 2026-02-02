"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import NeoCard from "@/app/components/neo/NeoCard";
import NeoButton from "@/app/components/neo/NeoButton";

/* -------------------- Types -------------------- */
type DigestResponse = {
  summary: string;
  email_count: number;
  model?: string | null;
};

type DigestHistoryItem = {
  id: number;
  range: "7d" | "15d" | "30d";
  summary: string;
  email_count: number;
  model?: string | null;
  created_at: string;
};

export default function DigestPage() {
  const router = useRouter();

  const [range, setRange] = useState<"7d" | "15d" | "30d">("7d");
  const [loading, setLoading] = useState(false);
  const [digest, setDigest] = useState<DigestResponse | null>(null);
  const [error, setError] = useState("");

  const [history, setHistory] = useState<DigestHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);


  useEffect(() => {
    const fetchHistory = async () => {
      setHistoryLoading(true);
      try {
        const token = localStorage.getItem("token");

        const res = await fetch("http://localhost:8000/digests", {
          headers: {
            Authorization: token ? `Bearer ${token}` : "",
          },
        });

        if (!res.ok) throw new Error("Failed");

        const data = await res.json();
        setHistory(data);
      } catch {

      } finally {
        setHistoryLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const generateDigest = async () => {
    setLoading(true);
    setError("");
    setDigest(null);

    try {
      const token = localStorage.getItem("token");

      const res = await fetch(
        `http://localhost:8000/emails/digest?range=${range}`,
        {
          headers: {
            Authorization: token ? `Bearer ${token}` : "",
          },
        }
      );

      if (!res.ok) throw new Error("Failed");

      const data: DigestResponse = await res.json();
      setDigest(data);
    } catch {
      setError("Could not generate digest. Please try again.");
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="p-10 bg-white text-black min-h-screen">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <NeoButton
          onClick={() => router.push("/dashboard")}
          className="px-4 py-2"
        >
          ← Inbox
        </NeoButton>

        <h1 className="text-2xl font-bold">AI Digest</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
  
        <NeoCard className="bg-black text-white md:col-span-2">
          {/* Range Selector */}
          <div className="flex gap-3 mb-4">
            {(["7d", "15d", "30d"] as const).map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={`px-4 py-1 border-2 text-sm font-bold ${
                  range === r
                    ? "border-white bg-white text-black"
                    : "border-gray-500 bg-black text-white hover:border-gray-300"
                }`}
              >
                {r}
              </button>
            ))}
          </div>

  
          <div className="border-2 border-dashed border-gray-600 p-5 mb-5 min-h-[200px]">
            {loading && (
              <p className="text-gray-400">Generating digest…</p>
            )}

            {error && (
              <p className="text-red-400">{error}</p>
            )}

            {digest && !loading && (
              <div className="space-y-5 text-gray-200">
                <div>
                  <strong className="block mb-2">AI Summary</strong>
                  {digest.summary?.trim() ? (
                    <p className="leading-relaxed">
                      {digest.summary}
                    </p>
                  ) : (
                    <p className="text-gray-500 italic">
                      No summary content was generated.
                    </p>
                  )}
                </div>

                <div className="text-sm text-gray-400">
                  <span>{digest.email_count} emails analyzed</span>
                  {digest.model && (
                    <>
                      {" · "}
                      <span>Model: {digest.model}</span>
                    </>
                  )}
                </div>
              </div>
            )}

            {!loading && !digest && !error && (
              <p className="text-gray-500">
                Select a range and generate an AI summary of your inbox.
              </p>
            )}
          </div>

          <NeoButton onClick={generateDigest} disabled={loading}>
            Generate Digest
          </NeoButton>
        </NeoCard>


        <NeoCard className="bg-black text-white">
          <h2 className="font-bold mb-4">Digest History</h2>

          {historyLoading && (
            <p className="text-gray-500 text-sm">Loading history…</p>
          )}

          {!historyLoading && history.length === 0 && (
            <p className="text-gray-500 text-sm">
              No digests generated yet.
            </p>
          )}

          <ul className="space-y-3">
            {history.map((item) => (
              <li
                key={item.id}
                onClick={() =>
                  setDigest({
                    summary: item.summary,
                    email_count: item.email_count,
                    model: item.model,
                  })
                }
                className="cursor-pointer border-2 border-gray-600 p-3 hover:border-white transition"
              >
                <div className="text-sm font-bold">
                  {item.range.toUpperCase()} Digest
                </div>
                <div className="text-xs text-gray-400">
                  {new Date(item.created_at).toLocaleString()}
                </div>
                <div className="text-xs text-gray-500">
                  {item.email_count} emails
                </div>
              </li>
            ))}
          </ul>
        </NeoCard>
      </div>
    </div>
  );
}
