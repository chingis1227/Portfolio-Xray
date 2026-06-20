/** @type {import('next').NextConfig} */
const nextConfig = {
  ...(process.env.PMRI_NEXT_DIST_DIR ? { distDir: process.env.PMRI_NEXT_DIST_DIR } : {}),
};

export default nextConfig;
