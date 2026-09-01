/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow remote images from Google's CDN (used by Stitch-generated logo)
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
      },
    ],
  },
};

module.exports = nextConfig;
