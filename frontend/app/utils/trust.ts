export function confidenceToTrust(confidence: number) {
  if (confidence >= 0.85) {
    return {
      label: "Auto-accepted",
      tone: "green" as const,
      needsReview: false,
    };
  }

  if (confidence >= 0.7) {
    return {
      label: "Review suggested",
      tone: "yellow" as const,
      needsReview: true,
    };
  }

  return {
    label: "Review required",
    tone: "red" as const,
    needsReview: true,
  };
}
