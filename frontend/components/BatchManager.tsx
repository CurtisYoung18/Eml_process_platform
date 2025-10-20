import { useState, useEffect } from 'react'
import { HiClock, HiCheckCircle, HiTrash, HiRefresh, HiFolderOpen, HiDocumentText, HiPlus, HiCloudUpload, HiX } from 'react-icons/hi'
import { BiLoaderAlt } from 'react-icons/bi'
import axios from 'axios'

export default function BatchManager() {
  const [batches, setBatches] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedBatch, setSelectedBatch] = useState<any>(null)
  const [showDetails, setShowDetails] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState<'success' | 'error'>('success')
  
  // 上传相关状态
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [batchLabel, setBatchLabel] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  
  // 知识库标签相关状态
  const [showKbLabelModal, setShowKbLabelModal] = useState(false)
  const [kbLabelBatchId, setKbLabelBatchId] = useState('')
  const [kbName, setKbName] = useState('')
  const [savingKbLabel, setSavingKbLabel] = useState(false)

  useEffect(() => {
    fetchBatches()
  }, [])

  const fetchBatches = async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:5001/api/batches')
      if (response.data.success) {
        setBatches(response.data.batches)
      }
    } catch (error: any) {
      console.error('获取批次列表失败:', error)
      showMessage('获取批次列表失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  const fetchBatchDetails = async (batchId: string) => {
    try {
      // URL 编码批次ID
      const encodedBatchId = encodeURIComponent(batchId)
      const response = await axios.get(`http://localhost:5001/api/batches/${encodedBatchId}`)
      if (response.data.success) {
        setSelectedBatch(response.data.batch)
        setShowDetails(true)
      } else {
        showMessage(response.data.error || '获取批次详情失败', 'error')
      }
    } catch (error: any) {
      console.error('获取批次详情失败:', error)
      showMessage(`获取批次详情失败: ${error.response?.data?.error || error.message}`, 'error')
    }
  }

  const deleteBatch = async (batchId: string) => {
    if (!confirm(`确定要删除批次 "${batchId}" 吗？此操作不可恢复。`)) {
      return
    }

    try {
      // URL 编码批次ID
      const encodedBatchId = encodeURIComponent(batchId)
      const response = await axios.delete(`http://localhost:5001/api/batches/${encodedBatchId}`)
      if (response.data.success) {
        showMessage('批次已删除', 'success')
        // 立即从本地状态中移除该批次
        setBatches(prev => prev.filter(b => b.batch_id !== batchId))
        if (selectedBatch?.batch_id === batchId) {
          setShowDetails(false)
          setSelectedBatch(null)
        }
        // 然后刷新完整列表
        fetchBatches()
      } else {
        showMessage(response.data.error || '删除批次失败', 'error')
      }
    } catch (error: any) {
      console.error('删除批次失败:', error)
      showMessage(`删除批次失败: ${error.response?.data?.error || error.message}`, 'error')
    }
  }

  const showMessage = (msg: string, type: 'success' | 'error') => {
    setMessage(msg)
    setMessageType(type)
    setTimeout(() => setMessage(''), 3000)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files))
    }
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      showMessage('请选择要上传的文件', 'error')
      return
    }

    // 验证批次标签必填
    if (!batchLabel.trim()) {
      showMessage('请输入批次标签', 'error')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    const formData = new FormData()
    selectedFiles.forEach(file => {
      formData.append('files', file)
    })
    
    // 添加批次标签（必填）
    formData.append('label', batchLabel.trim())

    try {
      const response = await axios.post('http://localhost:5001/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total 
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0
          setUploadProgress(progress)
        }
      })

      if (response.data.success) {
        showMessage(`成功创建批次！已上传 ${response.data.count} 个文件`, 'success')
        setSelectedFiles([])
        setBatchLabel('')
        setShowUploadModal(false)
        fetchBatches()
      }
    } catch (error: any) {
      showMessage(`上传失败: ${error.message}`, 'error')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const openKbLabelModal = (batchId: string, currentKbName?: string) => {
    setKbLabelBatchId(batchId)
    setKbName(currentKbName || '')
    setShowKbLabelModal(true)
  }

  const saveKbLabel = async () => {
    if (!kbName.trim()) {
      showMessage('请输入知识库名称', 'error')
      return
    }

    setSavingKbLabel(true)
    try {
      const encodedBatchId = encodeURIComponent(kbLabelBatchId)
      const response = await axios.put(
        `http://localhost:5001/api/batches/${encodedBatchId}/kb-label`,
        { kb_name: kbName.trim() }
      )

      if (response.data.success) {
        showMessage('知识库标签已保存', 'success')
        setShowKbLabelModal(false)
        setKbName('')
        setKbLabelBatchId('')
        fetchBatches()
      } else {
        showMessage(response.data.error || '保存失败', 'error')
      }
    } catch (error: any) {
      showMessage(`保存失败: ${error.response?.data?.error || error.message}`, 'error')
    } finally {
      setSavingKbLabel(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusColor = (status: any) => {
    if (status?.uploaded_to_kb) return '#48bb78'
    if (status?.llm_processed) return '#4299e1'
    if (status?.cleaned) return '#ed8936'
    return '#cbd5e0'
  }

  const getStatusText = (status: any) => {
    if (status?.uploaded_to_kb) return '✅ 已上传知识库'
    if (status?.llm_processed) return '🤖 已LLM处理'
    if (status?.cleaned) return '🧹 已去重清洗'
    return '📤 已上传'
  }

  return (
    <div style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto' }}>
      <style jsx>{`
        .batch-manager {
          background: white;
          border-radius: 16px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
          overflow: hidden;
        }

        .header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 30px 40px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .header h1 {
          margin: 0;
          font-size: 28px;
          font-weight: 700;
        }

        .refresh-btn {
          background: rgba(255, 255, 255, 0.2);
          border: 2px solid rgba(255, 255, 255, 0.5);
          color: white;
          padding: 10px 20px;
          border-radius: 8px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 600;
          transition: all 0.3s;
        }

        .refresh-btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.3);
          border-color: white;
        }

        .refresh-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .content {
          padding: 40px;
        }

        .batch-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 24px;
        }

        .batch-card {
          background: white;
          border: 2px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.3s;
          position: relative;
        }

        .batch-card:hover {
          border-color: #667eea;
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
          transform: translateY(-2px);
        }

        .batch-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 16px;
        }

        .batch-title {
          font-size: 16px;
          font-weight: 700;
          color: #2d3748;
          margin: 0 0 8px 0;
          word-break: break-word;
        }

        .batch-time {
          font-size: 13px;
          color: #718096;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .batch-status {
          display: inline-block;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
          background: rgba(102, 126, 234, 0.1);
          color: #667eea;
        }

        .batch-info {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid #e2e8f0;
        }

        .info-item {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: #4a5568;
        }

        .info-value {
          font-weight: 700;
          color: #667eea;
        }

        .delete-btn {
          background: #fed7d7;
          border: none;
          color: #c53030;
          padding: 8px 12px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 12px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.3s;
        }

        .delete-btn:hover {
          background: #fc8181;
          color: white;
        }

        .empty-state {
          text-align: center;
          padding: 80px 20px;
        }

        .empty-icon {
          font-size: 80px;
          color: #cbd5e0;
          margin-bottom: 20px;
        }

        .empty-text {
          font-size: 18px;
          color: #718096;
          margin: 0;
        }

        .message-box {
          position: fixed;
          top: 20px;
          right: 20px;
          padding: 16px 24px;
          border-radius: 8px;
          font-weight: 600;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          z-index: 1000;
          animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        .message-success {
          background: #c6f6d5;
          color: #22543d;
          border: 2px solid #48bb78;
        }

        .message-error {
          background: #fed7d7;
          color: #742a2a;
          border: 2px solid #fc8181;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 2000;
          animation: fadeIn 0.3s;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .modal-content {
          background: white;
          border-radius: 16px;
          padding: 40px;
          max-width: 600px;
          width: 90%;
          max-height: 80vh;
          overflow-y: auto;
          animation: slideUp 0.3s;
        }

        @keyframes slideUp {
          from {
            transform: translateY(50px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
          padding-bottom: 16px;
          border-bottom: 2px solid #e2e8f0;
        }

        .modal-title {
          font-size: 22px;
          font-weight: 700;
          color: #2d3748;
          margin: 0;
        }

        .close-btn {
          background: #e2e8f0;
          border: none;
          color: #4a5568;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          transition: all 0.3s;
        }

        .close-btn:hover {
          background: #cbd5e0;
        }

        .detail-section {
          margin-bottom: 24px;
        }

        .detail-label {
          font-size: 14px;
          font-weight: 700;
          color: #4a5568;
          margin-bottom: 8px;
        }

        .detail-value {
          font-size: 15px;
          color: #2d3748;
          padding: 12px;
          background: #f7fafc;
          border-radius: 8px;
        }

        .file-list {
          max-height: 200px;
          overflow-y: auto;
        }

        .file-item {
          padding: 10px 12px;
          background: #f7fafc;
          border-radius: 6px;
          margin-bottom: 8px;
          font-size: 14px;
          color: #2d3748;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .status-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }

        .status-item {
          padding: 12px;
          background: #f7fafc;
          border-radius: 8px;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .status-icon {
          font-size: 20px;
        }

        .status-label {
          font-size: 13px;
          color: #718096;
        }
      `}</style>

      {message && (
        <div className={`message-box ${messageType === 'success' ? 'message-success' : 'message-error'}`}>
          {messageType === 'success' ? '✅ ' : '❌ '}
          {message}
        </div>
      )}

      <div className="batch-manager">
        <div className="header">
          <h1><HiFolderOpen style={{ marginRight: '12px', verticalAlign: 'middle' }} />批次管理</h1>
          <button onClick={() => setShowUploadModal(true)} disabled={loading} className="refresh-btn">
            <HiPlus />
            新增批次
          </button>
        </div>

        <div className="content">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px' }}>
              <BiLoaderAlt className="spinner" style={{ fontSize: '48px', color: '#667eea' }} />
              <p style={{ marginTop: '16px', color: '#718096' }}>加载中...</p>
            </div>
          ) : batches.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📁</div>
              <p className="empty-text">暂无批次数据</p>
              <p style={{ fontSize: '14px', color: '#a0aec0', marginTop: '8px' }}>
                上传邮件后将自动创建批次
              </p>
            </div>
          ) : (
            <div className="batch-grid">
              {batches.map((batch) => (
                <div
                  key={batch.batch_id}
                  className="batch-card"
                  onClick={() => fetchBatchDetails(batch.batch_id)}
                >
                  <div className="batch-header">
                    <div style={{ flex: 1 }}>
                      <h3 className="batch-title">{batch.batch_id}</h3>
                      {batch.custom_label && (
                        <div style={{ 
                          fontSize: '13px', 
                          color: '#667eea', 
                          fontWeight: 600,
                          marginBottom: '8px'
                        }}>
                          🏷️ {batch.custom_label}
                        </div>
                      )}
                      <div className="batch-time">
                        <HiClock />
                        {formatDate(batch.upload_time)}
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: '12px' }}>
                    <span 
                      className="batch-status"
                      style={{ 
                        background: `${getStatusColor(batch.status)}20`,
                        color: getStatusColor(batch.status)
                      }}
                    >
                      {getStatusText(batch.status)}
                    </span>
                  </div>

                  <div className="batch-info">
                    <div className="info-item">
                      <HiDocumentText style={{ color: '#667eea' }} />
                      <span>
                        文件数: <span className="info-value">{batch.file_count}</span>
                      </span>
                    </div>
                    {batch.dedup_stats && (
                      <div className="info-item">
                        <HiCheckCircle style={{ color: '#48bb78' }} />
                        <span>
                          去重后: <span className="info-value">{batch.dedup_stats.unique_emails}</span>
                        </span>
                      </div>
                    )}
                  </div>

                  {/* 知识库标签显示 */}
                  {batch.kb_name && (
                    <div style={{ 
                      marginTop: '12px',
                      padding: '10px 12px',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      borderRadius: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                      <HiCloudUpload style={{ color: 'white', fontSize: '16px' }} />
                      <span style={{ 
                        color: 'white', 
                        fontSize: '13px',
                        fontWeight: 600,
                        flex: 1
                      }}>
                        已上传至: {batch.kb_name}
                      </span>
                    </div>
                  )}

                  {/* 知识库标签按钮（仅在已完成上传且未标记时显示） */}
                  {batch.status?.uploaded_to_kb && !batch.kb_name && (
                    <div style={{ 
                      marginTop: '12px',
                      padding: '10px 12px',
                      background: '#fef5e7',
                      border: '2px dashed #f39c12',
                      borderRadius: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '8px'
                    }}>
                      <span style={{ 
                        color: '#d68910', 
                        fontSize: '12px',
                        fontWeight: 600
                      }}>
                        💡 请标记知识库
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          openKbLabelModal(batch.batch_id)
                        }}
                        style={{
                          padding: '6px 12px',
                          background: '#f39c12',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          transition: 'all 0.3s'
                        }}
                      >
                        添加标签
                      </button>
                    </div>
                  )}

                  <div style={{ marginTop: '16px', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                    {batch.kb_name && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          openKbLabelModal(batch.batch_id, batch.kb_name)
                        }}
                        style={{
                          padding: '8px 12px',
                          background: '#e6f7ff',
                          border: '1px solid #91d5ff',
                          color: '#0050b3',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          transition: 'all 0.3s'
                        }}
                      >
                        <HiCloudUpload />
                        修改标签
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteBatch(batch.batch_id)
                      }}
                      className="delete-btn"
                    >
                      <HiTrash />
                      删除批次
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showDetails && selectedBatch && (
        <div className="modal" onClick={() => setShowDetails(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">批次详情</h2>
              <button onClick={() => setShowDetails(false)} className="close-btn">
                ×
              </button>
            </div>

            <div className="detail-section">
              <div className="detail-label">批次ID</div>
              <div className="detail-value">{selectedBatch.batch_id}</div>
            </div>

            {selectedBatch.custom_label && (
              <div className="detail-section">
                <div className="detail-label">批次标签</div>
                <div className="detail-value">🏷️ {selectedBatch.custom_label}</div>
              </div>
            )}

            <div className="detail-section">
              <div className="detail-label">上传时间</div>
              <div className="detail-value">{formatDate(selectedBatch.upload_time)}</div>
            </div>

            <div className="detail-section">
              <div className="detail-label">处理状态</div>
              <div className="status-grid">
                <div className="status-item">
                  <span className="status-icon">
                    {selectedBatch.status?.uploaded ? '✅' : '⏳'}
                  </span>
                  <div>
                    <div className="status-label">已上传</div>
                  </div>
                </div>
                <div className="status-item">
                  <span className="status-icon">
                    {selectedBatch.status?.cleaned ? '✅' : '⏳'}
                  </span>
                  <div>
                    <div className="status-label">已去重清洗</div>
                  </div>
                </div>
                <div className="status-item">
                  <span className="status-icon">
                    {selectedBatch.status?.llm_processed ? '✅' : '⏳'}
                  </span>
                  <div>
                    <div className="status-label">已LLM处理</div>
                  </div>
                </div>
                <div className="status-item">
                  <span className="status-icon">
                    {selectedBatch.status?.uploaded_to_kb ? '✅' : '⏳'}
                  </span>
                  <div>
                    <div className="status-label">已上传知识库</div>
                  </div>
                </div>
              </div>
            </div>

            {selectedBatch.dedup_stats && (
              <div className="detail-section">
                <div className="detail-label">去重统计</div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <div className="detail-value" style={{ flex: 1 }}>
                    总数: {selectedBatch.dedup_stats.total_emails}
                  </div>
                  <div className="detail-value" style={{ flex: 1 }}>
                    唯一: {selectedBatch.dedup_stats.unique_emails}
                  </div>
                  <div className="detail-value" style={{ flex: 1 }}>
                    重复: {selectedBatch.dedup_stats.duplicates}
                  </div>
                </div>
              </div>
            )}

            {selectedBatch.current_files && selectedBatch.current_files.length > 0 && (
              <div className="detail-section">
                <div className="detail-label">文件列表 ({selectedBatch.current_files.length})</div>
                <div className="file-list">
                  {selectedBatch.current_files.map((file: string, index: number) => (
                    <div key={index} className="file-item">
                      <HiDocumentText style={{ color: '#667eea' }} />
                      {file}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedBatch.processing_history && Object.keys(selectedBatch.processing_history).length > 0 && (
              <div className="detail-section">
                <div className="detail-label">处理历史</div>
                <div className="detail-value">
                  {Object.entries(selectedBatch.processing_history).map(([key, value]: [string, any]) => (
                    <div key={key} style={{ marginBottom: '4px' }}>
                      <strong>{key}:</strong> {formatDate(value)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 上传模态窗口 */}
      {showUploadModal && (
        <div className="modal" onClick={() => !uploading && setShowUploadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal-header">
              <h2 className="modal-title">新增批次</h2>
              <button 
                onClick={() => setShowUploadModal(false)} 
                className="close-btn"
                disabled={uploading}
              >
                ×
              </button>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: '#4a5568' }}>
                批次标签 <span style={{ color: '#e53e3e' }}>*</span>
              </label>
              <input
                type="text"
                value={batchLabel}
                onChange={(e) => setBatchLabel(e.target.value)}
                placeholder="邮件主要内容"
                disabled={uploading}
                required
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  border: '2px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '14px'
                }}
              />
              <p style={{ fontSize: '12px', color: '#718096', margin: '6px 0 0 0' }}>
                💡 添加标签方便后续查找和管理批次
              </p>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <input
                type="file"
                multiple
                accept=".eml"
                onChange={handleFileSelect}
                disabled={uploading}
                id="batch-file-upload"
                style={{ display: 'none' }}
              />
              <label 
                htmlFor="batch-file-upload" 
                style={{
                  display: 'block',
                  padding: '40px 20px',
                  border: '2px dashed #cbd5e0',
                  borderRadius: '8px',
                  textAlign: 'center',
                  cursor: uploading ? 'not-allowed' : 'pointer',
                  background: '#f7fafc',
                  transition: 'all 0.3s'
                }}
                onMouseEnter={(e) => !uploading && (e.currentTarget.style.borderColor = '#667eea')}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = '#cbd5e0')}
              >
                <HiCloudUpload style={{ fontSize: '48px', color: '#667eea', marginBottom: '12px' }} />
                <p style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px', color: '#2d3748' }}>
                  点击选择EML文件
                </p>
                <p style={{ fontSize: '14px', color: '#718096' }}>
                  支持多文件上传
                </p>
              </label>
            </div>

            {selectedFiles.length > 0 && (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span style={{ fontSize: '14px', fontWeight: 600, color: '#4a5568' }}>
                    已选择 {selectedFiles.length} 个文件
                  </span>
                  <button 
                    onClick={() => setSelectedFiles([])}
                    disabled={uploading}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#e53e3e',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: 600
                    }}
                  >
                    <HiX style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                    清空
                  </button>
                </div>
                <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                  {selectedFiles.map((file, index) => (
                    <div 
                      key={index} 
                      style={{
                        padding: '8px 12px',
                        background: '#f7fafc',
                        borderRadius: '6px',
                        marginBottom: '6px',
                        fontSize: '13px',
                        color: '#2d3748',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                    >
                      <HiDocumentText style={{ color: '#667eea' }} />
                      {file.name}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {uploading && (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ 
                  height: '8px', 
                  background: '#e2e8f0', 
                  borderRadius: '4px', 
                  overflow: 'hidden' 
                }}>
                  <div 
                    style={{ 
                      height: '100%', 
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      width: `${uploadProgress}%`,
                      transition: 'width 0.3s'
                    }}
                  />
                </div>
                <p style={{ fontSize: '13px', color: '#718096', marginTop: '8px', textAlign: 'center' }}>
                  上传中... {uploadProgress}%
                </p>
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowUploadModal(false)}
                disabled={uploading}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: '#e2e8f0',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#4a5568',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: uploading ? 'not-allowed' : 'pointer',
                  opacity: uploading ? 0.5 : 1
                }}
              >
                取消
              </button>
              <button
                onClick={handleUpload}
                disabled={uploading || selectedFiles.length === 0}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: selectedFiles.length > 0 && !uploading 
                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                    : '#cbd5e0',
                  border: 'none',
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: selectedFiles.length > 0 && !uploading ? 'pointer' : 'not-allowed'
                }}
              >
                {uploading ? '上传中...' : '创建批次'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 知识库标签模态窗口 */}
      {showKbLabelModal && (
        <div className="modal" onClick={() => !savingKbLabel && setShowKbLabelModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '450px' }}>
            <div className="modal-header">
              <h2 className="modal-title">
                <HiCloudUpload style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
                标记知识库
              </h2>
              <button 
                onClick={() => setShowKbLabelModal(false)} 
                className="close-btn"
                disabled={savingKbLabel}
              >
                ×
              </button>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <p style={{ fontSize: '14px', color: '#718096', marginBottom: '16px' }}>
                请输入该批次邮件上传到的知识库名称，方便后续追踪和管理。
              </p>
              
              <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: '#4a5568' }}>
                知识库名称 <span style={{ color: '#e53e3e' }}>*</span>
              </label>
              <input
                type="text"
                value={kbName}
                onChange={(e) => setKbName(e.target.value)}
                placeholder="例如：客户服务知识库"
                disabled={savingKbLabel}
                autoFocus
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  border: '2px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '14px',
                  transition: 'border-color 0.3s'
                }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && kbName.trim()) {
                    saveKbLabel()
                  }
                }}
              />
              <p style={{ fontSize: '12px', color: '#718096', margin: '8px 0 0 0' }}>
                💡 提示：可以是GPTBots中的知识库名称
              </p>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowKbLabelModal(false)}
                disabled={savingKbLabel}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: '#e2e8f0',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#4a5568',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: savingKbLabel ? 'not-allowed' : 'pointer',
                  opacity: savingKbLabel ? 0.5 : 1
                }}
              >
                取消
              </button>
              <button
                onClick={saveKbLabel}
                disabled={savingKbLabel || !kbName.trim()}
                style={{
                  flex: 1,
                  padding: '12px',
                  background: kbName.trim() && !savingKbLabel 
                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                    : '#cbd5e0',
                  border: 'none',
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: kbName.trim() && !savingKbLabel ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                {savingKbLabel ? (
                  <>
                    <BiLoaderAlt className="spinner" style={{ fontSize: '16px' }} />
                    保存中...
                  </>
                ) : (
                  '保存'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

