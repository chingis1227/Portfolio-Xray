const brandMarkSizeClasses = {
  sm: "h-8 w-8",
  md: "h-9 w-9",
  base: "h-12 w-12",
  lg: "h-14 w-14",
  xl: "h-20 w-20"
};

type BrandMarkSize = keyof typeof brandMarkSizeClasses;

export function BrandMark({ size = "base" }: { size?: BrandMarkSize }) {
  return (
    <svg className={brandMarkSizeClasses[size]} viewBox="0 0 64 64" role="img" aria-label="Portfolio MRI mark">
      <path
        d="M32 7 55 52h-9.4L32 25.1 18.4 52H9L32 7Z"
        fill="none"
        stroke="#DADBDF"
        strokeLinejoin="round"
        strokeWidth="4"
      />
      <path
        d="M23.2 42.6h17.6L32 25.1l-8.8 17.5Z"
        fill="#FFFFFF"
        opacity="0.86"
      />
      <path d="M18 52h28" stroke="#ECEFF3" strokeLinecap="round" strokeWidth="2" opacity="0.55" />
    </svg>
  );
}
