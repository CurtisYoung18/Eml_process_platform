/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 配置API代理到Python后端
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5001/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig

