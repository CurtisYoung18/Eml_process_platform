import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { 
  HiHome, 
  HiCloudUpload, 
  HiCog, 
  HiChartBar, 
  HiDatabase,
  HiLogout,
  HiChip,
  HiFolderOpen
} from 'react-icons/hi'
import { checkAuth, logout, getCurrentUser } from '@/lib/mockDb'

// 页面组件
import Overview from '@/components/Overview'
import AutoPipeline from '@/components/AutoPipeline'
import ResultsView from '@/components/ResultsView'
import BatchManager from '@/components/BatchManager'

export default function AdminPage() {
  const router = useRouter()
  const [currentPage, setCurrentPage] = useState('overview')
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)  // 新增：处理中状态

  useEffect(() => {
    // 延迟检查，防止闪烁和循环
    const timer = setTimeout(() => {
      // 检查登录状态
      if (!checkAuth()) {
        router.push('/login')
        return
      }
      
      const currentUser = getCurrentUser()
      setUser(currentUser)
      setLoading(false)
    }, 100)
    
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const navItems = [
    { id: 'overview', label: '首页概览', icon: HiHome },
    { id: 'batches', label: '批次管理', icon: HiFolderOpen },
    { id: 'auto', label: '全自动运行', icon: HiCog },
    { id: 'results', label: '结果查看', icon: HiChartBar },
  ]

  const renderContent = () => {
    switch (currentPage) {
      case 'overview':
        return <Overview onNavigate={setCurrentPage} />
      case 'auto':
        return <AutoPipeline onNavigate={setCurrentPage} onProcessingChange={setIsProcessing} />
      case 'batches':
        return <BatchManager />
      case 'results':
        return <ResultsView />
      default:
        return <Overview onNavigate={setCurrentPage} />
    }
  }

  const handleLogout = () => {
    if (confirm('确定要退出登录吗？')) {
      logout()
      router.push('/')
    }
  }

  const handleBackToHome = () => {
    router.push('/')
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>验证身份...</p>
      </div>
    )
  }

  return (
    <div className="workspace-page">
      {/* 顶部导航栏 */}
      <header className="workspace-header">
        <div className="header-left">
          <img src="/logo.png" alt="Logo" className="header-logo" />
          <div className="header-title">
            <h1>邮件处理管理后台</h1>
            <p>Email Processing Management</p>
          </div>
        </div>
        <div className="header-right">
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px',
            padding: '8px 16px',
            background: 'rgba(255, 255, 255, 0.15)',
            borderRadius: '10px',
            color: 'white',
            marginRight: '12px'
          }}>
            <span style={{ fontSize: '20px' }}>👤</span>
            <span style={{ fontWeight: 600 }}>{user?.username}</span>
          </div>
          <button 
            onClick={handleBackToHome}
            className="btn btn-secondary"
            style={{ 
              background: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              marginRight: '8px'
            }}
          >
            🏠 返回首页
          </button>
          <button 
            onClick={handleLogout}
            className="btn btn-secondary"
            style={{ 
              background: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.3)'
            }}
          >
            <HiLogout />
            <span>退出登录</span>
          </button>
        </div>
      </header>

      {/* 主内容区域 */}
      <div className="workspace-main">
        {/* 侧边栏导航 */}
        <aside className="workspace-sidebar">
          <div className="nav-menu">
            {navItems.map((item) => (
              <button
                key={item.id}
                className={`nav-item ${currentPage === item.id ? 'active' : ''} ${isProcessing && item.id !== 'auto' ? 'disabled' : ''}`}
                onClick={() => !isProcessing && setCurrentPage(item.id)}
                disabled={isProcessing && item.id !== 'auto'}
                style={{
                  cursor: isProcessing && item.id !== 'auto' ? 'not-allowed' : 'pointer',
                  opacity: isProcessing && item.id !== 'auto' ? 0.5 : 1,
                  pointerEvents: isProcessing && item.id !== 'auto' ? 'none' : 'auto'
                }}
              >
                <item.icon className="nav-icon" />
                <span className="nav-label">{item.label}</span>
              </button>
            ))}
          </div>
        </aside>

        {/* 内容区域 */}
        <main className="workspace-content">
          {renderContent()}
        </main>
      </div>
    </div>
  )
}

