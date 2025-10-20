import { useState, useEffect } from 'react'
import { HiCloudUpload, HiCog, HiChartBar, HiChip, HiFolderOpen } from 'react-icons/hi'
import axios from 'axios'

interface OverviewProps {
  onNavigate: (page: string) => void
}

export default function Overview({ onNavigate }: OverviewProps) {
  const [stats, setStats] = useState({
    totalBatches: 0,
    processingBatches: 0,
    completedBatches: 0,
    totalFiles: 0,
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
      // 获取批次统计
      const batchesResponse = await axios.get('http://localhost:5001/api/batches')
      let totalBatches = 0
      let processingBatches = 0
      let completedBatches = 0
      let totalFiles = 0
      
      if (batchesResponse.data.success) {
        const batches = batchesResponse.data.batches
        totalBatches = batches.length
        
        batches.forEach((batch: any) => {
          totalFiles += batch.file_count || 0
          
          if (batch.status?.uploaded_to_kb) {
            completedBatches++
          } else if (batch.status?.cleaned || batch.status?.llm_processed) {
            processingBatches++
          }
        })
      }
      
      // 获取文件统计
      const statsResponse = await axios.get('http://localhost:5001/api/stats')
      const fileStats = statsResponse.data.success ? statsResponse.data.stats : {}
      
      setStats({
        totalBatches,
        processingBatches,
        completedBatches,
        totalFiles,
        uploaded: fileStats.uploaded || 0,
        cleaned: fileStats.cleaned || 0,
        processed: fileStats.processed || 0,
        inKnowledgeBase: fileStats.inKnowledgeBase || 0
      })
    } catch (error) {
      console.error('获取统计信息失败:', error)
    }
  }

  return (
    <div>
      <div className="glass-card">
        <h2>📊 系统概览</h2>
        
        {/* 批次统计卡片 */}
        <div className="stats-grid">
          <div className="stat-card" onClick={() => onNavigate('batches')} style={{ cursor: 'pointer' }}>
            <div className="stat-icon" style={{ color: '#667eea' }}>
              📁
            </div>
            <h3 className="stat-value">{stats.totalBatches}</h3>
            <p className="stat-label">总批次数</p>
          </div>

          <div className="stat-card" onClick={() => onNavigate('batches')} style={{ cursor: 'pointer' }}>
            <div className="stat-icon" style={{ color: '#f6ad55' }}>
              ⏳
            </div>
            <h3 className="stat-value">{stats.processingBatches}</h3>
            <p className="stat-label">处理中批次</p>
          </div>

          <div className="stat-card" onClick={() => onNavigate('batches')} style={{ cursor: 'pointer' }}>
            <div className="stat-icon" style={{ color: '#48bb78' }}>
              ✅
            </div>
            <h3 className="stat-value">{stats.completedBatches}</h3>
            <p className="stat-label">已完成批次</p>
          </div>

          <div className="stat-card" onClick={() => onNavigate('results')} style={{ cursor: 'pointer' }}>
            <div className="stat-icon" style={{ color: '#9f7aea' }}>
              📧
            </div>
            <h3 className="stat-value">{stats.totalFiles}</h3>
            <p className="stat-label">累计处理文件</p>
          </div>
        </div>
      </div>

      <div className="glass-card">
        <h2>🔄 批次处理流程</h2>
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
              icon={<HiFolderOpen />}
              title="1. 创建批次"
              description="在批次管理中创建新批次，添加自定义标签，上传EML邮件文件"
              color="#667eea"
              onClick={() => onNavigate('batches')}
            />
            <ProcessStep 
              icon={<HiCog />}
              title="2. 选择批次"
              description="在全自动配置中选择要处理的批次，支持多批次同时处理"
              color="#48bb78"
              onClick={() => onNavigate('auto')}
            />
            <ProcessStep 
              icon={<HiChip />}
              title="3. 自动处理"
              description="一键执行去重清洗、LLM优化、知识库上传，智能跳过已完成步骤"
              color="#ed8936"
              onClick={() => onNavigate('auto')}
            />
            <ProcessStep 
              icon={<HiChartBar />}
              title="4. 查看结果"
              description="按批次查看处理结果，预览不同阶段的文件，标记知识库信息"
              color="#9f7aea"
              onClick={() => onNavigate('results')}
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
            onClick={() => onNavigate('batches')}
          >
            <HiFolderOpen />
            开始创建批次
          </button>
          <button 
            className="btn btn-secondary"
            onClick={() => onNavigate('auto')}
          >
            <HiCog />
            全自动处理
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


