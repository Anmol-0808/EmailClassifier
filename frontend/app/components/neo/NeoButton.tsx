"use client";

type NeoButtonProps = {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
};

export default function NeoButton({
  children,
  onClick,
  disabled = false,
  className = "",
}: NeoButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        border-3 border-black px-4 py-2 font-semibold
        bg-white text-black
        shadow-[4px_4px_0px_#9ca3af] /* soft gray shadow */
        active:translate-x-[2px] active:translate-y-[2px] active:shadow-none
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-transform
        ${className}
      `}
    >
      {children}
    </button>
  );
}
