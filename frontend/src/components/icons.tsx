type IconProps = { className?: string; style?: React.CSSProperties };

const base = {
  width: 19,
  height: 19,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function IconGrid({ className, style }: IconProps) {
  return (
    <svg {...base} className={className} style={style}>
      <rect x="3" y="3" width="7.5" height="7.5" rx="1.6" />
      <rect x="13.5" y="3" width="7.5" height="7.5" rx="1.6" />
      <rect x="3" y="13.5" width="7.5" height="7.5" rx="1.6" />
      <rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.6" />
    </svg>
  );
}

export function IconUsers({ className, style }: IconProps) {
  return (
    <svg {...base} className={className} style={style}>
      <circle cx="9" cy="8" r="3.25" />
      <path d="M2.75 20c0-3.45 2.8-6 6.25-6s6.25 2.55 6.25 6" />
      <path d="M15.5 3.4c1.7.5 2.95 2.1 2.95 4s-1.25 3.5-2.95 4" />
      <path d="M17.75 13.4c1.9.5 3.5 2.4 3.5 4.9" />
    </svg>
  );
}

export function IconCross({ className, style }: IconProps) {
  return (
    <svg {...base} className={className} style={style}>
      <path d="M4 21V9.5L12 3l8 6.5V21" />
      <path d="M9.75 21v-6.5h4.5V21" />
      <path d="M12 8v4M10 10h4" />
    </svg>
  );
}

export function IconBulb({ className, style }: IconProps) {
  return (
    <svg {...base} className={className} style={style}>
      <path d="M9 18h6" />
      <path d="M10 21h4" />
      <path d="M12 3a6.5 6.5 0 0 0-3.6 11.9c.55.4.85 1.05.85 1.73V17h5.5v-.37c0-.68.3-1.33.85-1.73A6.5 6.5 0 0 0 12 3Z" />
    </svg>
  );
}

export function IconBook({ className, style }: IconProps) {
  return (
    <svg {...base} className={className} style={style}>
      <path d="M4 4.8c0-.7.55-1.2 1.25-1.15C8 3.8 10.3 4.5 12 6c1.7-1.5 4-2.2 6.75-2.35.7-.05 1.25.45 1.25 1.15v13c0 .65-.5 1.15-1.15 1.2-2.95.2-5.15.95-6.85 2.5-1.7-1.55-3.9-2.3-6.85-2.5-.65-.05-1.15-.55-1.15-1.2Z" />
      <path d="M12 6v14" />
    </svg>
  );
}

export function IconFileText({ className, style }: IconProps) {
  return (
    <svg {...base} className={className} style={style}>
      <path d="M14 3v4a1 1 0 0 0 1 1h4" />
      <path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2Z" />
      <path d="M9 13h6" />
      <path d="M9 17h6" />
    </svg>
  );
}
