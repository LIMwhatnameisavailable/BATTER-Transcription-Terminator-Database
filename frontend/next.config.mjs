/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const origin = process.env.BTED_API_ORIGIN?.replace(/\/$/, "");
    if (!origin) return [];
    return [{
      source: "/api/v1/:path*",
      destination: `${origin}/api/v1/:path*`,
    }];
  },
};

export default nextConfig;
