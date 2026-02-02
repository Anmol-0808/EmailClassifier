type NeoBadgeProps = {
  label: string;
  tone: "green" | "yellow" | "red";
};

const toneStyles: Record<NeoBadgeProps["tone"], string> = {
  green: "border-green-400 text-green-300",
  yellow: "border-yellow-400 text-yellow-300",
  red: "border-red-400 text-red-300",
};

export default function NeoBadge({ label, tone }: NeoBadgeProps) {
  return (
    <span
      className={`
        inline-block text-xs font-semibold px-2 py-1
        border-2 ${toneStyles[tone]}
      `}
    >
      {label}
    </span>
  );
}
