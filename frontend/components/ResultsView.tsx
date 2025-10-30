import { useState, useEffect } from 'react'
import { HiCheckCircle, HiRefresh, HiDocumentText, HiEye, HiX, HiFolderOpen, HiChevronDown, HiChevronRight } from 'react-icons/hi'
import { BiLoaderAlt } from 'react-icons/bi'
import axios from 'axios'

// 智能API地址：使用相对路径，通过 Next.js 反向代理访问后端
const getApiBaseUrl = () => {
  // 统一使用空字符串，所有请求通过 Next.js 代理转发到 5001 端口
  return ''
}

const API_BASE_URL = getApiBaseUrl()

// 构建完整的API路径
const getApiUrl = (path: string) => {
  // 确保路径以 / 开头
  return path.startsWith('/') ? path : `/${path}`
}

interface BatchData {
  batch_id: string
  custom_label: string
  upload_time: string
  file_count: number
  kb_name?: string  // 知识库名称（可选）
  status: {
    uploaded: boolean
    cleaned: boolean
    llm_processed: boolean
    uploaded_to_kb: boolean
  }
  uploadedFiles: string[]
  processedFiles: string[]
  llmProcessedFiles: string[]
}

export default function ResultsView() {
  const [batches, setBatches] = useState<BatchData[]>([])
  const [expandedBatches, setExpandedBatches] = useState<Set<string>>(new Set())
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())  // 新增：控制各个section的折叠状态
  const [selectedFile, setSelectedFile] = useState<{ filename: string, category: string, batchId: string } | null>(null)
  const [fileContent, setFileContent] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)

  useEffect(() => {
    fetchBatchesWithFiles()
  }, [])

  const fetchBatchesWithFiles = async () => {
    setLoading(true)
    try {
      // 获取所有批次
      const batchesRes = await axios.get(getApiUrl('/api/batches'))
      if (!batchesRes.data.success) {
        console.error('获取批次列表失败')
        return
      }

      const batchList = batchesRes.data.batches

      // 获取所有文件
      const [uploadedRes, processedRes, llmRes] = await Promise.all([
        axios.get(getApiUrl('/api/uploaded-files')),
        axios.get(getApiUrl('/api/processed-files')),
        axios.get(getApiUrl('/api/llm-processed-files'))
      ])

      const uploadedFiles = uploadedRes.data.success ? uploadedRes.data.files : []
      const processedFiles = processedRes.data.success ? processedRes.data.files : []
      const llmProcessedFiles = llmRes.data.success ? llmRes.data.files : []

      // 按批次组织文件
      const batchesWithFiles: BatchData[] = batchList.map((batch: any) => {
        const batchId = batch.batch_id
        
        return {
          batch_id: batchId,
          custom_label: batch.custom_label || '',
          upload_time: batch.upload_time,
          file_count: batch.file_count,
          status: batch.status,
          uploadedFiles: uploadedFiles.filter((f: string) => f.startsWith(batchId + '/')),
          processedFiles: processedFiles.filter((f: string) => f.startsWith(batchId + '/')),
          llmProcessedFiles: llmProcessedFiles.filter((f: string) => f.startsWith(batchId + '/'))
        }
      })

      setBatches(batchesWithFiles)
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleBatch = (batchId: string) => {
    const newExpanded = new Set(expandedBatches)
    if (newExpanded.has(batchId)) {
      newExpanded.delete(batchId)
    } else {
      newExpanded.add(batchId)
    }
    setExpandedBatches(newExpanded)
  }

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId)
    } else {
      newExpanded.add(sectionId)
    }
    setExpandedSections(newExpanded)
  }

  const fetchFileContent = async (filename: string, category: string, batchId: string) => {
    setPreviewLoading(true)
    setSelectedFile({ filename, category, batchId })
    
    try {
      let endpoint = ''
      // 文件名已经包含批次路径
      const encodedFilename = encodeURIComponent(filename)
      
      if (category === 'uploaded') {
        endpoint = getApiUrl(`/api/file-content/uploaded/${encodedFilename}`)
      } else if (category === 'processed') {
        endpoint = getApiUrl(`/api/file-content/processed/${encodedFilename}`)
      } else {
        endpoint = getApiUrl(`/api/file-content/llm-processed/${encodedFilename}`)
      }
      
      const response = await axios.get(endpoint)
      if (response.data.success) {
        setFileContent(response.data.content)
      }
    } catch (error) {
      console.error('获取文件内容失败:', error)
      setFileContent('无法读取文件内容')
    } finally {
      setPreviewLoading(false)
    }
  }

  const closePreview = () => {
    setSelectedFile(null)
    setFileContent('')
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

  const getFileName = (fullPath: string) => {
    return fullPath.split('/').pop() || fullPath
  }

  if (loading) {
    return (
      <div className="results-view-container">
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '400px'
        }}>
          <BiLoaderAlt className="spinner" style={{ fontSize: '48px', color: '#667eea' }} />
          <p style={{ marginTop: '16px', fontSize: '16px', color: '#718096' }}>加载中...</p>
        </div>
        <style jsx>{`
          .spinner {
            animation: spin 1s linear infinite;
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
    <div className="results-view-container">
      <div className={`main-content ${selectedFile ? 'with-preview' : ''}`}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '24px', margin: 0, display: 'flex', alignItems: 'center' }}>
            <HiFolderOpen style={{ fontSize: '28px', marginRight: '12px', color: '#667eea' }} />
            批次文件浏览
          </h2>
          <button 
            onClick={fetchBatchesWithFiles}
            className="refresh-button"
          >
            <HiRefresh />
            刷新列表
          </button>
        </div>

      {batches.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '80px 20px',
          background: 'white',
          borderRadius: '12px',
          border: '2px dashed #cbd5e0'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '16px' }}>📁</div>
          <p style={{ fontSize: '18px', color: '#718096', margin: 0 }}>暂无批次数据</p>
          <p style={{ fontSize: '14px', color: '#a0aec0', marginTop: '8px' }}>
            请先上传邮件创建批次
          </p>
        </div>
      ) : (
        <div className="batches-list">
          {batches.map((batch) => {
            const isExpanded = expandedBatches.has(batch.batch_id)
            const hasProcessed = batch.processedFiles.length > 0
            const hasLlmProcessed = batch.llmProcessedFiles.length > 0

            return (
              <div key={batch.batch_id} className="batch-card">
                <div 
                  className="batch-header"
                  onClick={() => toggleBatch(batch.batch_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                    {isExpanded ? (
                      <HiChevronDown style={{ fontSize: '20px', color: '#667eea' }} />
                    ) : (
                      <HiChevronRight style={{ fontSize: '20px', color: '#a0aec0' }} />
                    )}
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
                        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#2d3748' }}>
                          {batch.batch_id}
                        </h3>
                        {batch.custom_label && (
                          <span style={{
                            padding: '4px 12px',
                            background: '#ebf8ff',
                            color: '#2c5282',
                            borderRadius: '12px',
                            fontSize: '13px',
                            fontWeight: 600
                          }}>
                            🏷️ {batch.custom_label}
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '13px', color: '#718096' }}>
                        上传时间: {formatDate(batch.upload_time)}
                      </div>
                      {batch.kb_name && (
                        <div style={{ 
                          marginTop: '6px',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '4px 10px',
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: 600,
                          color: 'white'
                        }}>
                          ☁️ {batch.kb_name}
                        </div>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                    <div className="file-count-badge">
                      📧 {batch.uploadedFiles.length}
                    </div>
                    {hasProcessed && (
                      <div className="file-count-badge" style={{ background: '#c6f6d5', color: '#22543d' }}>
                        ✅ {batch.processedFiles.length}
                      </div>
                    )}
                    {hasLlmProcessed && (
                      <div className="file-count-badge" style={{ background: '#e6fffa', color: '#234e52' }}>
                        🤖 {batch.llmProcessedFiles.length}
                      </div>
                    )}
                  </div>
                </div>

                {isExpanded && (
                  <div className="batch-content">
                    {/* 已上传文件 */}
                    <div className="file-section">
                      <div 
                        className="section-header"
                        onClick={() => toggleSection(`${batch.batch_id}-uploaded`)}
                        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                      >
                        {expandedSections.has(`${batch.batch_id}-uploaded`) ? (
                          <HiChevronDown style={{ fontSize: '16px', color: '#667eea' }} />
                        ) : (
                          <HiChevronRight style={{ fontSize: '16px', color: '#a0aec0' }} />
                        )}
                        <h4 className="section-title" style={{ margin: 0 }}>
                          📧 已上传邮件 ({batch.uploadedFiles.length})
                        </h4>
                      </div>
                      {expandedSections.has(`${batch.batch_id}-uploaded`) && (
                        batch.uploadedFiles.length > 0 ? (
                          <div className="file-list" style={{ marginTop: '12px' }}>
                            {batch.uploadedFiles.map((file, idx) => (
                              <div key={idx} className="file-item">
                                <span className="file-name">{getFileName(file)}</span>
                                <button
                                  onClick={() => fetchFileContent(file, 'uploaded', batch.batch_id)}
                                  className="preview-btn"
                                >
                                  <HiEye /> 预览
                                </button>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="empty-hint">暂无文件</div>
                        )
                      )}
                    </div>

                    {/* 已去重文件 */}
                    <div className="file-section">
                      <div 
                        className="section-header"
                        onClick={() => toggleSection(`${batch.batch_id}-processed`)}
                        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                      >
                        {expandedSections.has(`${batch.batch_id}-processed`) ? (
                          <HiChevronDown style={{ fontSize: '16px', color: '#667eea' }} />
                        ) : (
                          <HiChevronRight style={{ fontSize: '16px', color: '#a0aec0' }} />
                        )}
                        <h4 className="section-title" style={{ margin: 0 }}>
                          ✅ 已去重邮件 ({batch.processedFiles.length})
                        </h4>
                      </div>
                      {expandedSections.has(`${batch.batch_id}-processed`) && (
                        batch.processedFiles.length > 0 ? (
                          <div className="file-list" style={{ marginTop: '12px' }}>
                            {batch.processedFiles.map((file, idx) => (
                              <div key={idx} className="file-item">
                                <span className="file-name">{getFileName(file)}</span>
                                <button
                                  onClick={() => fetchFileContent(file, 'processed', batch.batch_id)}
                                  className="preview-btn"
                                >
                                  <HiEye /> 预览
                                </button>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="empty-hint">暂无文件</div>
                        )
                      )}
                    </div>

                    {/* LLM处理文件 */}
                    <div className="file-section">
                      <div 
                        className="section-header"
                        onClick={() => toggleSection(`${batch.batch_id}-llm`)}
                        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                      >
                        {expandedSections.has(`${batch.batch_id}-llm`) ? (
                          <HiChevronDown style={{ fontSize: '16px', color: '#667eea' }} />
                        ) : (
                          <HiChevronRight style={{ fontSize: '16px', color: '#a0aec0' }} />
                        )}
                        <h4 className="section-title" style={{ margin: 0 }}>
                          🤖 LLM处理文件 ({batch.llmProcessedFiles.length})
                        </h4>
                      </div>
                      {expandedSections.has(`${batch.batch_id}-llm`) && (
                        batch.llmProcessedFiles.length > 0 ? (
                          <div className="file-list" style={{ marginTop: '12px' }}>
                            {batch.llmProcessedFiles.map((file, idx) => (
                              <div key={idx} className="file-item">
                                <span className="file-name">{getFileName(file)}</span>
                                <button
                                  onClick={() => fetchFileContent(file, 'llm', batch.batch_id)}
                                  className="preview-btn"
                                >
                                  <HiEye /> 预览
                                </button>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="empty-hint">暂无文件</div>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
      </div>

      {/* 侧边预览窗格 */}
      <div className={`preview-panel ${selectedFile ? 'open' : ''}`}>
        <div className="preview-panel-header">
          <div style={{ flex: 1, minWidth: 0 }}>
            <h3 style={{ 
              margin: 0, 
              fontSize: '16px', 
              fontWeight: 700,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {selectedFile ? getFileName(selectedFile.filename) : ''}
            </h3>
            {selectedFile && (
              <p style={{ 
                margin: '6px 0 0 0', 
                fontSize: '12px', 
                color: '#718096',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                批次: {selectedFile.batchId}
              </p>
            )}
            {selectedFile && (
              <div style={{ marginTop: '8px' }}>
                <span style={{
                  display: 'inline-block',
                  padding: '4px 10px',
                  background: selectedFile.category === 'uploaded' ? '#edf2f7' : 
                             selectedFile.category === 'processed' ? '#c6f6d5' : '#e6fffa',
                  color: selectedFile.category === 'uploaded' ? '#2d3748' : 
                         selectedFile.category === 'processed' ? '#22543d' : '#234e52',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: 600
                }}>
                  {selectedFile.category === 'uploaded' ? '📧 已上传' : 
                   selectedFile.category === 'processed' ? '✅ 已去重' : '🤖 LLM处理'}
                </span>
              </div>
            )}
          </div>
          <button onClick={closePreview} className="preview-close-btn">
            <HiX />
          </button>
        </div>
        <div className="preview-panel-body">
          {previewLoading ? (
            <div style={{ 
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%'
            }}>
              <BiLoaderAlt className="spinner" style={{ fontSize: '40px', color: '#667eea' }} />
              <p style={{ marginTop: '16px', color: '#718096', fontSize: '14px' }}>加载中...</p>
            </div>
          ) : (
            <pre style={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontSize: '13px',
              lineHeight: '1.7',
              margin: 0,
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace'
            }}>
              {fileContent}
            </pre>
          )}
        </div>
      </div>

      {/* 遮罩层 */}
      {selectedFile && (
        <div className="preview-overlay" onClick={closePreview} />
      )}

      <style jsx>{`
        .results-view-container {
          position: relative;
          padding: 30px;
          background: #f7fafc;
          min-height: 100vh;
          display: flex;
          overflow: hidden;
        }

        .main-content {
          flex: 1;
          transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          min-width: 0;
        }

        .main-content.with-preview {
          margin-right: 500px;
        }

        .refresh-button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s;
        }

        .refresh-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .batches-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .batch-card {
          background: white;
          border-radius: 12px;
          border: 2px solid #e2e8f0;
          overflow: hidden;
          transition: all 0.3s;
        }

        .batch-card:hover {
          border-color: #cbd5e0;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .batch-header {
          padding: 20px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: white;
        }

        .batch-header:hover {
          background: #f7fafc;
        }

        .file-count-badge {
          padding: 6px 12px;
          background: #edf2f7;
          color: #2d3748;
          border-radius: 12px;
          fontSize: 13px;
          fontWeight: 600;
        }

        .batch-content {
          padding: 0 20px 20px 20px;
          border-top: 1px solid #e2e8f0;
          background: #f7fafc;
        }

        .file-section {
          margin-top: 16px;
          padding: 16px;
          background: white;
          border-radius: 8px;
          border: 1px solid #e2e8f0;
        }

        .section-title {
          margin: 0 0 12px 0;
          fontSize: 14px;
          fontWeight: 700;
          color: #2d3748;
        }

        .section-header {
          padding: 12px;
          background: #f7fafc;
          borderRadius: 8px;
          transition: all 0.2s;
        }

        .section-header:hover {
          background: #edf2f7;
        }

        .file-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .file-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 10px 12px;
          background: #f7fafc;
          border-radius: 6px;
          border: 1px solid #e2e8f0;
          transition: all 0.2s;
        }

        .file-item:hover {
          background: #edf2f7;
          border-color: #cbd5e0;
        }

        .file-name {
          fontSize: 13px;
          color: #2d3748;
          flex: 1;
          overflow: hidden;
          textOverflow: ellipsis;
          whiteSpace: nowrap;
        }

        .preview-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          borderRadius: 8px;
          fontSize: 13px;
          fontWeight: 600;
          cursor: pointer;
          transition: all 0.3s;
          box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
        }

        .preview-btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
        }

        .preview-btn:active {
          transform: translateY(0);
        }

        .empty-hint {
          padding: 20px;
          textAlign: center;
          color: #a0aec0;
          fontSize: 14px;
        }

        .preview-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.3);
          z-index: 999;
          animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        .preview-panel {
          position: fixed;
          top: 0;
          right: -500px;
          width: 500px;
          height: 100vh;
          background: white;
          box-shadow: -4px 0 24px rgba(0, 0, 0, 0.15);
          z-index: 1000;
          display: flex;
          flex-direction: column;
          transition: right 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          border-radius: 16px 0 0 16px;
          overflow: hidden;
        }

        .preview-panel.open {
          right: 0;
        }

        .preview-panel-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 16px;
          padding: 24px;
          border-bottom: 2px solid #e2e8f0;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .preview-panel-header h3 {
          color: white;
        }

        .preview-panel-header p {
          color: rgba(255, 255, 255, 0.9);
        }

        .preview-panel-body {
          flex: 1;
          overflow: auto;
          padding: 24px;
          background: #f7fafc;
        }

        .preview-close-btn {
          width: 36px;
          height: 36px;
          min-width: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.2);
          border: none;
          border-radius: 50%;
          font-size: 20px;
          color: white;
          cursor: pointer;
          transition: all 0.3s;
          backdrop-filter: blur(10px);
        }

        .preview-close-btn:hover {
          background: rgba(255, 255, 255, 0.3);
          transform: rotate(90deg);
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
