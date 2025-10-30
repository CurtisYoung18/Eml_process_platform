import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { HiUser, HiLockClosed, HiArrowLeft } from 'react-icons/hi'
import { BiLoaderAlt } from 'react-icons/bi'
import { login, isRemembered, checkAuth } from '@/lib/mockDb'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [loginSuccess, setLoginSuccess] = useState(false)
  const [checking, setChecking] = useState(true) // 添加检查状态

  useEffect(() => {
    // 延迟检查，防止闪烁和循环
    const timer = setTimeout(() => {
      // 如果已经登录，直接跳转到admin页面
      if (checkAuth()) {
        console.log('已登录，自动跳转到admin页面')
        router.push('/admin')
        return
      }
      
      // 检查是否之前勾选了记住我
      const remembered = isRemembered()
      console.log('初始化记住我状态:', remembered)
      setRememberMe(remembered)
      setChecking(false)
    }, 100)
    
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 500))

    const success = login(username, password, rememberMe)
    
    if (success) {
      // 显示成功动画
      setLoginSuccess(true)
      // 等待动画完成后跳转
      setTimeout(() => {
        router.push('/admin')
      }, 1500)
    } else {
      setError('用户名或密码错误')
      setLoading(false)
    }
  }

  const handleBack = () => {
    router.push('/')
  }

  // 显示加载状态，防止闪烁
  if (checking) {
    return (
      <div className="login-page-container">
        <div style={{ textAlign: 'center', color: 'white' }}>
          <BiLoaderAlt style={{ fontSize: '48px', animation: 'spin 1s linear infinite' }} />
          <p style={{ marginTop: '16px' }}>加载中...</p>
        </div>
        <style jsx>{`
          .login-page-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    )
  }

  return (
    <>
      {/* 登录成功过渡动画 */}
      {loginSuccess && (
        <div className="success-overlay">
          <div className="success-animation">
            <div className="success-logo-container">
              <img src="/logo.png" alt="Logo" className="success-logo" />
              <div className="success-checkmark-badge">✓</div>
            </div>
            <h2 className="success-title">登录成功！</h2>
            <p className="success-subtitle">正在进入管理后台...</p>
          </div>
        </div>
      )}

      <div className="login-page-container">
        <button 
          className="back-to-home-btn"
          onClick={handleBack}
          type="button"
        >
          <HiArrowLeft /> 返回首页
        </button>

        <div className="login-card-wrapper">
          <div className="login-card-modern">
            <div className="login-header-modern">
              <h2>管理员登录</h2>
              <p>请输入您的账号和密码</p>
            </div>

            <form onSubmit={handleSubmit} className="login-form-modern">
              <div className="form-group-modern">
                <label htmlFor="username">
                  <HiUser className="input-icon" />
                  用户名
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="请输入用户名"
                  disabled={loading}
                  required
                  autoComplete="username"
                />
              </div>

              <div className="form-group-modern">
                <label htmlFor="password">
                  <HiLockClosed className="input-icon" />
                  密码
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="请输入密码"
                  disabled={loading}
                  required
                  autoComplete="current-password"
                />
              </div>

              <div className="remember-me-container">
                <label className="remember-me-label">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    disabled={loading}
                  />
                  <span>记住登录信息</span>
                </label>
              </div>

              {error && <div className="error-message-modern">{error}</div>}

              <button type="submit" className="login-submit-btn" disabled={loading}>
                {loading ? (
                  <>
                    <BiLoaderAlt className="spinner-icon" />
                    登录中...
                  </>
                ) : (
                  '登录'
                )}
              </button>
            </form>

            <div className="login-footer-modern">
              <HiLockClosed />
              <small>您的资料将会被保密处理</small>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .login-page-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 20px;
          position: relative;
        }

        .back-to-home-btn {
          position: absolute;
          top: 30px;
          left: 30px;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: rgba(255, 255, 255, 0.2);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.3);
          border-radius: 50px;
          color: white;
          font-size: 15px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
          z-index: 10;
        }

        .back-to-home-btn:hover {
          background: rgba(255, 255, 255, 0.3);
          transform: translateX(-5px);
        }

        .login-card-wrapper {
          width: 100%;
          max-width: 420px;
          animation: slideUp 0.5s ease-out;
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .login-card-modern {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 20px;
          padding: 40px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }

        .login-header-modern {
          text-align: center;
          margin-bottom: 35px;
        }

        .login-header-modern h2 {
          font-size: 28px;
          font-weight: 700;
          color: #2d3748;
          margin: 0 0 10px 0;
        }

        .login-header-modern p {
          font-size: 15px;
          color: #718096;
          margin: 0;
        }

        .login-form-modern {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .form-group-modern {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .form-group-modern label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 600;
          color: #4a5568;
        }

        .input-icon {
          font-size: 18px;
          color: #667eea;
        }

        .form-group-modern input {
          width: 100%;
          padding: 14px 16px;
          border: 2px solid #e2e8f0;
          border-radius: 12px;
          font-size: 15px;
          color: #2d3748;
          background: white;
          transition: all 0.3s ease;
          box-sizing: border-box;
        }

        .form-group-modern input:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-group-modern input:disabled {
          background: #f7fafc;
          cursor: not-allowed;
        }

        .error-message-modern {
          padding: 12px 16px;
          background: #fff5f5;
          border: 1px solid #fc8181;
          border-radius: 10px;
          color: #c53030;
          font-size: 14px;
          text-align: center;
          animation: shake 0.3s ease;
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }

        .remember-me-container {
          display: flex;
          align-items: center;
          margin-bottom: 4px;
        }

        .remember-me-label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: #4a5568;
          cursor: pointer;
          user-select: none;
        }

        .remember-me-label input[type="checkbox"] {
          width: 18px;
          height: 18px;
          cursor: pointer;
          accent-color: #667eea;
        }

        .remember-me-label input[type="checkbox"]:disabled {
          cursor: not-allowed;
          opacity: 0.5;
        }

        .remember-me-label span {
          font-weight: 500;
        }

        .login-submit-btn {
          width: 100%;
          padding: 16px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 12px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          margin-top: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }

        .login-submit-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        .login-submit-btn:active:not(:disabled) {
          transform: translateY(0);
        }

        .login-submit-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .spinner-icon {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .login-footer-modern {
          margin-top: 25px;
          padding-top: 20px;
          border-top: 1px solid #e2e8f0;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          color: #718096;
          font-size: 13px;
        }

        @media (max-width: 768px) {
          .back-to-home-btn {
            top: 20px;
            left: 20px;
            padding: 10px 20px;
            font-size: 14px;
          }

          .login-card-modern {
            padding: 30px 25px;
          }

          .login-header-modern h2 {
            font-size: 24px;
          }
        }

        /* 登录成功动画样式 */
        .success-overlay {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          animation: fadeIn 0.3s ease-out;
        }

        .success-animation {
          text-align: center;
          color: white;
        }

        .success-logo-container {
          position: relative;
          width: 150px;
          height: 150px;
          margin: 0 auto 30px;
          background: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
          animation: logoFloat 1.5s ease-in-out infinite;
          padding: 20px;
        }

        .success-logo {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .success-checkmark-badge {
          position: absolute;
          bottom: -10px;
          right: -10px;
          width: 50px;
          height: 50px;
          background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 30px;
          color: white;
          font-weight: bold;
          box-shadow: 0 4px 20px rgba(72, 187, 120, 0.5);
          animation: checkmarkPop 0.5s ease-out 0.3s both;
        }

        @keyframes logoFloat {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-15px);
          }
        }

        @keyframes checkmarkPop {
          0% {
            transform: scale(0) rotate(0deg);
            opacity: 0;
          }
          50% {
            transform: scale(1.2) rotate(180deg);
          }
          100% {
            transform: scale(1) rotate(360deg);
            opacity: 1;
          }
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .success-title {
          font-size: 32px;
          font-weight: 700;
          margin: 0 0 10px 0;
          animation: slideUp 0.5s ease-out 0.5s both;
        }

        .success-subtitle {
          font-size: 16px;
          opacity: 0.9;
          margin: 0;
          animation: slideUp 0.5s ease-out 0.6s both;
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </>
  )
}

