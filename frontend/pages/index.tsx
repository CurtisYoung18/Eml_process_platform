import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { HiCloudUpload } from 'react-icons/hi'

export default function HomePage() {
  const router = useRouter()
  const [showWelcome, setShowWelcome] = useState(true)
  const [iframeLoaded, setIframeLoaded] = useState(false)

  useEffect(() => {
    // 1.5秒后隐藏欢迎动画
    const timer = setTimeout(() => {
      setShowWelcome(false)
    }, 1800)
    return () => clearTimeout(timer)
  }, [])

  const handleEmailManagement = () => {
    router.push('/login')
  }

  return (
    <div className="qa-main-page">
      {/* 欢迎动画 */}
      {showWelcome && (
        <div className="welcome-overlay">
          <div className="welcome-content-animation">
            <div className="welcome-avatar floating">
              <img src="/logo.png" alt="Logo" />
            </div>
            <h1 className="welcome-title">欢迎使用</h1>
            <h2 className="welcome-username">邮件知识库问答系统</h2>
            <p className="welcome-subtitle">您的智能助手已准备就绪</p>
          </div>
        </div>
      )}

      {/* 顶部导航栏 */}
      <header className="qa-header">
        <div className="qa-header-left">
          <img src="/logo.png" alt="Logo" className="qa-logo floating-slow" />
          <div className="qa-header-title">
            <h1>Nolato邮件知识库问答系统</h1>
            <p>Email Knowledge Base Q&A</p>
          </div>
        </div>
        <div className="qa-header-right">
          <button 
            onClick={handleEmailManagement}
            className="email-management-btn"
          >
            <HiCloudUpload />
            <span>邮件处理管理</span>
          </button>
        </div>
      </header>

      {/* QA问答iframe */}
      <div className="qa-iframe-container">
        {!iframeLoaded && (
          <div className="iframe-loading">
            <div className="loading-spinner"></div>
            <p>加载问答系统...</p>
          </div>
        )}
        <iframe
          src="http://10.52.20.41:19080/widget/eerfztrnqsiqkxj85aobcwb/chat.html"
        
          className={`qa-iframe ${iframeLoaded ? 'loaded' : ''}`}
          onLoad={() => setIframeLoaded(true)}
          title="知识库问答"
          allow="microphone *"
        />
      </div>

  
      <style jsx>{`
        .qa-main-page {
          width: 100vw;
          height: 100vh;
          display: flex;
          flex-direction: column;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          position: relative;
          overflow: hidden;
        }

        .qa-main-page::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-image: url('/imgs/wallpaper.jpg');
          background-size: cover;
          background-position: center;
          opacity: 0.3;
          z-index: 0;
        }

        .qa-header {
          position: relative;
          z-index: 10;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 32px;
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .qa-header-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .qa-logo {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          object-fit: cover;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        .floating {
          animation: float 3s ease-in-out infinite;
        }

        .floating-slow {
          animation: float 6s ease-in-out infinite;
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-15px);
          }
        }

        .qa-header-title {
          color: white;
        }

        .qa-header-title h1 {
          margin: 0;
          font-size: 22px;
          font-weight: 700;
        }

        .qa-header-title p {
          margin: 0;
          font-size: 13px;
          opacity: 0.9;
        }

        .email-management-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: rgba(255, 255, 255, 0.2);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.3);
          border-radius: 12px;
          color: white;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s;
        }

        .email-management-btn:hover {
          background: rgba(255, 255, 255, 0.3);
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
        }

        .qa-iframe-container {
          position: relative;
          z-index: 1;
          flex: 1;
          margin: 16px;
          border-radius: 16px;
          overflow: hidden;
          background: rgba(255, 255, 255, 0.95);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }

        .qa-iframe {
          width: 100%;
          height: 100%;
          border: none;
          opacity: 0;
          transition: opacity 0.5s;
        }

        .qa-iframe.loaded {
          opacity: 1;
        }

        .iframe-loading {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          text-align: center;
          color: #667eea;
        }

        .loading-spinner {
          width: 48px;
          height: 48px;
          border: 4px solid rgba(102, 126, 234, 0.2);
          border-top-color: #667eea;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
          margin: 0 auto 16px;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .iframe-loading p {
          font-size: 16px;
          font-weight: 500;
        }

        /* 欢迎动画样式 */
        .welcome-overlay {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 999;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          animation: shrinkAndFadeOut 1.5s ease-out forwards;
        }

        @keyframes shrinkAndFadeOut {
          0% {
            opacity: 1;
            transform: scale(1);
          }
          70% {
            opacity: 1;
            transform: scale(1);
          }
          100% {
            opacity: 0;
            transform: scale(0.8);
            pointer-events: none;
          }
        }

        .welcome-content-animation {
          text-align: center;
          animation: scaleIn 0.5s ease-out;
        }

        @keyframes scaleIn {
          from {
            transform: scale(0.5);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }

        .welcome-avatar {
          width: 150px;
          height: 150px;
          margin: 0 auto 30px;
          border-radius: 50%;
          overflow: hidden;
          border: 4px solid rgba(255, 255, 255, 0.3);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .welcome-avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .welcome-title {
          font-size: 32px;
          font-weight: 300;
          color: white;
          margin: 0 0 10px 0;
          text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }

        .welcome-username {
          font-size: 42px;
          font-weight: 600;
          color: white;
          margin: 0 0 20px 0;
          text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }

        .welcome-subtitle {
          font-size: 18px;
          color: rgba(255, 255, 255, 0.95);
          margin: 0;
          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        }

        @media (max-width: 768px) {
          .qa-header {
            padding: 12px 16px;
          }

          .qa-logo {
            width: 45px;
            height: 45px;
          }

          .qa-header-title h1 {
            font-size: 16px;
          }

          .qa-header-title p {
            font-size: 11px;
          }

          .email-management-btn {
            padding: 10px 16px;
            font-size: 14px;
          }

          .email-management-btn span {
            display: none;
          }
        }
      `}</style>
    </div>
  )
}
