/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 配置API代理到Python后端
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: 'http://localhost:5000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig

