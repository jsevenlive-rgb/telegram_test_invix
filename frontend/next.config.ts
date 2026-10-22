import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  basePath: process.env.NEXT_BASE_PATH || "",
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "localhost", port: "9000", pathname: "/**" },
      { protocol: "http", hostname: "minio", port: "9000", pathname: "/**" },
      { protocol: "https", hostname: "**" },
    ],
  },
};

export default nextConfig;
