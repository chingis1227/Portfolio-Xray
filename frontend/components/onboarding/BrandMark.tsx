export function BrandMark({ className = "h-12 w-12" }: { className...: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" role="img" aria-label="Portfolio MRI mark">
      <defs>
        <linearGradient id="pmri-mark-gradient" x1="14" x2="50" y1="10" y2="54" gradientUnits="userSpaceOnUse">
          <stop stopColor="#ECEFF3" />
          <stop offset="0.52" stopColor="#AAB7C6" />
          <stop offset="1" stopColor="#3B82F6" />
        </linearGradient>
      </defs>
      <path
        d="M32 7 55 52h-9.4L32 25.1 18.4 52H9L32 7Z"
        fill="none"
        stroke="url(#pmri-mark-gradient)"
        strokeLinejoin="round"
        strokeWidth="4"
      />
      <path
        d="M23.2 42.6h17.6L32 25.1l-8.8 17.5Z"
        fill="url(#pmri-mark-gradient)"
        opacity="0.92"
      />
      <path d="M18 52h28" stroke="#ECEFF3" strokeLinecap="round" strokeWidth="2" opacity="0.55" />
    </svg>
  );
}
