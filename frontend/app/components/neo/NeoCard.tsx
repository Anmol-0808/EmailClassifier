import React from "react";

type NeoCardProps = React.HTMLAttributes<HTMLDivElement> & {
  children: React.ReactNode;
};

export default function NeoCard({
  children,
  className = "",
  ...props
}: NeoCardProps) {
  return (
    <div
      {...props}
      className={`
        border-3
        p-4
        shadow-[6px_6px_0px_#000]
        ${className}
      `}
    >
      {children}
    </div>
  );
}
