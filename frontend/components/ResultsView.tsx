import { useState, useEffect } from 'react'
import { HiCheckCircle, HiRefresh, HiDocumentText, HiEye, HiX } from 'react-icons/hi'
import axios from 'axios'

export default function ResultsView() {
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const [processedFiles, setProcessedFiles] = useState<string[]>([])
  const [llmProcessedFiles, setLlmProcessedFiles] = useState<string[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<'uploaded' | 'processed' | 'llm'>('uploaded')
  const [fileContent, setFileContent] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)

  useEffect(() => {
    fetchAllFiles()
  }, [])

  const fetchAllFiles = async () => {
    setLoading(true)
    try {
      const [uploadedRes, processedRes, llmRes] = await Promise.all([
        axios.get('http://localhost:5001/api/uploaded-files'),
        axios.get('http://localhost:5001/api/processed-files'),
        axios.get('http://localhost:5001/api/llm-processed-files')
      ])
      
      if (uploadedRes.data.success) setUploadedFiles(uploadedRes.data.files)
      if (processedRes.data.success) setProcessedFiles(processedRes.data.files)
      if (llmRes.data.success) setLlmProcessedFiles(llmRes.data.files)
    } catch (error) {
      console.error('获取文件列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchFileContent = async (filename: string, category: 'uploaded' | 'processed' | 'llm') => {
    setPreviewLoading(true)
    setSelectedFile(filename)
    setSelectedCategory(category)
    
    try {
      let endpoint = ''
      if (category === 'uploaded') {
        endpoint = `http://localhost:5001/api/file-content/uploaded/${filename}`
      } else if (category === 'processed') {
        endpoint = `http://localhost:5001/api/file-content/processed/${filename}`
      } else {
        endpoint = `http://localhost:5001/api/file-content/llm-processed/${filename}`
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

  if (loading) {
    return (
      <div className="results-view-container">
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '400px',
          fontSize: '18px',
          color: '#718096'
        }}>
          加载中...
        </div>
      </div>
    )
  }

  return (
    <div className="results-view-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '24px', margin: 0, display: 'flex', alignItems: 'center' }}>
          <HiDocumentText style={{ fontSize: '28px', marginRight: '12px', color: '#667eea' }} />
          文件浏览
        </h2>
        <button 
          onClick={fetchAllFiles}
          className="refresh-button"
        >
          <HiRefresh />
          刷新列表
        </button>
      </div>

      <div className="content-layout">
        {/* 三列文件列表 */}
        <div className="files-grid">
          {/* 已上传邮件 */}
          <div className="file-list-section">
            <h3 className="section-title">
              📂 已上传邮件
              <span className="file-count">{uploadedFiles.length}</span>
            </h3>
            <div className="file-list">
              {uploadedFiles.length > 0 ? (
                uploadedFiles.map((file, index) => (
                  <div
                    key={index}
                    className={`file-item ${selectedFile === file && selectedCategory === 'uploaded' ? 'active' : ''}`}
                    onClick={() => fetchFileContent(file, 'uploaded')}
                  >
                    <span className="file-name">📧 {file}</span>
                    <HiEye className="view-icon" />
                  </div>
                ))
              ) : (
                <div className="empty-state">暂无文件</div>
              )}
            </div>
          </div>

          {/* 已去重邮件 */}
          <div className="file-list-section">
            <h3 className="section-title">
              ✅ 已去重邮件
              <span className="file-count">{processedFiles.length}</span>
            </h3>
            <div className="file-list">
              {processedFiles.length > 0 ? (
                processedFiles.map((file, index) => (
                  <div
                    key={index}
                    className={`file-item ${selectedFile === file && selectedCategory === 'processed' ? 'active' : ''}`}
                    onClick={() => fetchFileContent(file, 'processed')}
                  >
                    <span className="file-name">📄 {file}</span>
                    <HiEye className="view-icon" />
                  </div>
                ))
              ) : (
                <div className="empty-state">暂无文件</div>
              )}
            </div>
          </div>

          {/* LLM处理邮件 */}
          <div className="file-list-section">
            <h3 className="section-title">
              🤖 LLM处理
              <span className="file-count">{llmProcessedFiles.length}</span>
            </h3>
            <div className="file-list">
              {llmProcessedFiles.length > 0 ? (
                llmProcessedFiles.map((file, index) => (
                  <div
                    key={index}
                    className={`file-item ${selectedFile === file && selectedCategory === 'llm' ? 'active' : ''}`}
                    onClick={() => fetchFileContent(file, 'llm')}
                  >
                    <span className="file-name">✨ {file}</span>
                    <HiEye className="view-icon" />
                  </div>
                ))
              ) : (
                <div className="empty-state">暂无文件</div>
              )}
            </div>
          </div>
        </div>

        {/* 文件预览区域 */}
        {selectedFile && (
          <div className="preview-section">
            <div className="preview-header">
              <div>
                <h3 style={{ margin: 0, fontSize: '16px', color: '#2d3748' }}>
                  {selectedCategory === 'uploaded' ? '📧 原始邮件' : 
                   selectedCategory === 'processed' ? '✅ 清洗结果' : 
                   '🤖 LLM优化'}
                </h3>
                <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#718096' }}>
                  {selectedFile}
                </p>
              </div>
              <button onClick={closePreview} className="close-button">
                <HiX />
              </button>
            </div>
            <div className="preview-content">
              {previewLoading ? (
                <div className="preview-loading">加载中...</div>
              ) : (
                <pre className="file-content">{fileContent}</pre>
              )}
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .results-view-container {
          padding: 30px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .refresh-button {
          padding: 10px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: all 0.3s;
        }

        .refresh-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .content-layout {
          display: flex;
          gap: 20px;
          min-height: 600px;
        }

        .files-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 20px;
          flex: 1;
        }

        .file-list-section {
          display: flex;
          flex-direction: column;
        }

        .section-title {
          font-size: 16px;
          color: #2d3748;
          margin: 0 0 12px 0;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .file-count {
          font-size: 14px;
          color: #718096;
          background: #f8f9fa;
          padding: 4px 12px;
          border-radius: 12px;
          font-weight: 600;
        }

        .file-list {
          background: #f8f9fa;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 12px;
          flex: 1;
          overflow-y: auto;
          max-height: 550px;
        }

        .file-list::-webkit-scrollbar {
          width: 6px;
        }

        .file-list::-webkit-scrollbar-track {
          background: #edf2f7;
          border-radius: 3px;
        }

        .file-list::-webkit-scrollbar-thumb {
          background: #cbd5e0;
          border-radius: 3px;
        }

        .file-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 12px;
          background: white;
          border: 1px solid transparent;
          border-radius: 8px;
          margin-bottom: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .file-item:hover {
          border-color: #667eea;
          box-shadow: 0 2px 6px rgba(102, 126, 234, 0.15);
        }

        .file-item.active {
          border-color: #667eea;
          background: linear-gradient(135deg, #f7faff 0%, #f0f4ff 100%);
          box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }

        .file-name {
          flex: 1;
          font-size: 13px;
          color: #4a5568;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          margin-right: 8px;
        }

        .view-icon {
          color: #667eea;
          font-size: 16px;
          flex-shrink: 0;
        }

        .empty-state {
          text-align: center;
          padding: 40px 20px;
          color: #a0aec0;
          font-size: 14px;
        }

        .preview-section {
          width: 500px;
          background: #f8f9fa;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .preview-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: 16px 20px;
          background: white;
          border-bottom: 1px solid #e2e8f0;
        }

        .close-button {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #fff;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          cursor: pointer;
          color: #718096;
          transition: all 0.2s;
        }

        .close-button:hover {
          background: #f7fafc;
          border-color: #cbd5e0;
          color: #e53e3e;
        }

        .preview-content {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }

        .preview-content::-webkit-scrollbar {
          width: 8px;
        }

        .preview-content::-webkit-scrollbar-track {
          background: #edf2f7;
          border-radius: 4px;
        }

        .preview-content::-webkit-scrollbar-thumb {
          background: #cbd5e0;
          border-radius: 4px;
        }

        .preview-loading {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 200px;
          color: #718096;
          font-size: 14px;
        }

        .file-content {
          font-family: 'Courier New', monospace;
          font-size: 13px;
          line-height: 1.6;
          color: #2d3748;
          white-space: pre-wrap;
          word-wrap: break-word;
          margin: 0;
        }

        @media (max-width: 1400px) {
          .content-layout {
            flex-direction: column;
          }

          .files-grid {
            grid-template-columns: 1fr;
          }

          .preview-section {
            width: 100%;
            max-height: 400px;
          }
        }
      `}</style>
    </div>
  )
}
