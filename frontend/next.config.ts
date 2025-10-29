import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Optionally use standalone for smaller Docker images
  // Set to undefined to use standard mode
  output: process.env.NEXT_STANDALONE === 'true' ? 'standalone' : undefined,
  // Disable strict mode for now (can enable later)
  reactStrictMode: false,
};

export default nextConfig;
