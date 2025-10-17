import { useState, useEffect } from 'react'
import { HiCloudUpload, HiCog, HiChartBar, HiChip } from 'react-icons/hi'
import axios from 'axios'

interface OverviewProps {
  onNavigate: (page: string) => void
}

export default function Overview({ onNavigate }: OverviewProps) {
  const [stats, setStats] = useState({
    uploaded: 0,
    cleaned: 0,
    processed: 0,
    inKnowledgeBase: 0
  })

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/stats')
      if (response.data.success) {
        setStats(response.data.stats)
      }
    } catch (error) {
      console.error('获取统计信息失败:', error)
    }
  }

  return (
    <div>
      <div className="glass-card">
        <h2>📊 系统概览</h2>
        
        {/* 统计卡片 */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ color: '#667eea' }}>
              📧
            </div>
            <h3 className="stat-value">{stats.uploaded}</h3>
            <p className="stat-label">已上传邮件</p>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ color: '#48bb78' }}>
              🧹
            </div>
            <h3 className="stat-value">{stats.cleaned}</h3>
            <p className="stat-label">已清洗邮件</p>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ color: '#ed8936' }}>
              🤖
            </div>
            <h3 className="stat-value">{stats.processed}</h3>
            <p className="stat-label">LLM处理完成</p>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ color: '#9f7aea' }}>
              📚
            </div>
            <h3 className="stat-value">{stats.inKnowledgeBase}</h3>
            <p className="stat-label">知识库文档</p>
          </div>
        </div>
      </div>

      <div className="glass-card">
        <h2>🔄 处理流程</h2>
        <div style={{ 
          background: 'white', 
          padding: '32px', 
          borderRadius: '12px',
          marginBottom: '24px'
        }}>
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '16px',
            maxWidth: '800px',
            margin: '0 auto'
          }}>
            <ProcessStep 
              icon={<HiCloudUpload />}
              title="1. 邮件上传"
              description="上传EML格式邮件文件，支持批量上传"
              color="#667eea"
              onClick={() => onNavigate('upload')}
            />
            <ProcessStep 
              icon={<HiCog />}
              title="2. 数据清洗"
              description="自动提取邮件内容，去除HTML标签和重复信息"
              color="#48bb78"
              onClick={() => onNavigate('cleaning')}
            />
            <ProcessStep 
              icon={<HiChip />}
              title="3. LLM处理"
              description="使用AI技术进行内容优化和结构化处理"
              color="#ed8936"
              onClick={() => onNavigate('llm')}
            />
            <ProcessStep 
              icon={<HiChartBar />}
              title="4. 知识库构建"
              description="上传到知识库，支持智能问答和内容检索"
              color="#9f7aea"
              onClick={() => onNavigate('knowledge')}
            />
          </div>
        </div>

        <div style={{ 
          display: 'flex', 
          gap: '16px', 
          justifyContent: 'center',
          flexWrap: 'wrap'
        }}>
          <button 
            className="btn btn-primary"
            onClick={() => onNavigate('auto')}
          >
            <HiCloudUpload />
            开始吧！
          </button>
          <button 
            className="btn btn-secondary"
            onClick={() => window.location.href = '/'}
          >
            💬 进入问答系统
          </button>
        </div>
      </div>

    </div>
  )
}

function ProcessStep({ icon, title, description, color, onClick }: any) {
  return (
    <div 
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '20px',
        padding: '20px',
        background: '#f7fafc',
        borderRadius: '12px',
        cursor: 'pointer',
        transition: 'all 0.3s',
        border: `2px solid transparent`
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = color
        e.currentTarget.style.transform = 'translateX(8px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'transparent'
        e.currentTarget.style.transform = 'translateX(0)'
      }}
    >
      <div style={{ 
        fontSize: '36px', 
        color: color,
        flexShrink: 0
      }}>
        {icon}
      </div>
      <div style={{ flex: 1 }}>
        <h3 style={{ 
          fontSize: '18px', 
          fontWeight: 600,
          color: '#1a202c',
          margin: '0 0 8px 0'
        }}>
          {title}
        </h3>
        <p style={{ 
          fontSize: '14px',
          color: '#718096',
          margin: 0
        }}>
          {description}
        </p>
      </div>
    </div>
  )
}


