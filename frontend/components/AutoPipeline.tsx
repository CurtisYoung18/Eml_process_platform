import { useState, useEffect } from 'react'
import { HiCog, HiCheckCircle, HiPlay, HiCloudUpload, HiTrash, HiX } from 'react-icons/hi'
import { BiLoaderAlt } from 'react-icons/bi'
import axios from 'axios'

interface AutoPipelineProps {
  onNavigate?: (page: string) => void
}

export default function AutoPipeline({ onNavigate }: AutoPipelineProps) {
  const [currentView, setCurrentView] = useState<'upload' | 'config' | 'completed'>('upload')
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')
  const [logs, setLogs] = useState<string[]>([])
  const [processingResult, setProcessingResult] = useState<any>(null)
  const [shouldStop, setShouldStop] = useState(false)
  
  // 上传相关状态
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const [processedFiles, setProcessedFiles] = useState<string[]>([])
  const [llmProcessedFiles, setLlmProcessedFiles] = useState<string[]>([])
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [uploadMessage, setUploadMessage] = useState('')
  
  // 配置参数
  const [config, setConfig] = useState({
    selectedLlmKey: '',
    llmApiKey: '',
    selectedKbKey: '',
    kbApiKey: '',
    selectedKnowledgeBase: '',
    chunkMode: 'token', // 'token' 或 'separator'
    chunkToken: 600,
    chunkSeparator: '\n\n'
  })
  
  // 环境变量配置
  const [envConfig, setEnvConfig] = useState<any>(null)
  const [loadingConfig, setLoadingConfig] = useState(false)
  
  // 知识库列表
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([])
  const [loadingKBList, setLoadingKBList] = useState(false)

  useEffect(() => {
    fetchUploadedFiles()
    fetchProcessedFiles()
    fetchLlmProcessedFiles()
    
    // 如果正在运行，确保显示配置页面
    if (running && currentView === 'upload') {
      setCurrentView('config')
    }
  }, [])

  useEffect(() => {
    if (currentView === 'config') {
      fetchEnvConfig()
    }
  }, [currentView])

  const fetchEnvConfig = async () => {
    setLoadingConfig(true)
    try {
      const response = await axios.get('http://localhost:5001/api/config/env')
      if (response.data.success) {
        setEnvConfig(response.data.config)
        // 默认选择第一个LLM API Key
        if (response.data.config.llm_api_keys.length > 0 && !config.llmApiKey) {
          const firstKey = response.data.config.llm_api_keys[0]
          setConfig(prev => ({
            ...prev,
            selectedLlmKey: firstKey.id,
            llmApiKey: firstKey.value
          }))
        }
        // 默认选择第一个KB API Key
        if (response.data.config.kb_api_keys.length > 0 && !config.kbApiKey) {
          const firstKbKey = response.data.config.kb_api_keys[0]
          setConfig(prev => ({
            ...prev,
            selectedKbKey: firstKbKey.id,
            kbApiKey: firstKbKey.value
          }))
          // 自动获取知识库列表
          fetchKnowledgeBases(firstKbKey.value)
        }
      }
    } catch (error) {
      console.error('获取环境配置失败:', error)
    } finally {
      setLoadingConfig(false)
    }
  }

  const fetchKnowledgeBases = async (apiKey: string) => {
    setLoadingKBList(true)
    try {
      const response = await axios.post('http://localhost:5001/api/knowledge-bases', {
        api_key: apiKey
      })
      if (response.data.success) {
        setKnowledgeBases(response.data.knowledge_bases || [])
        // 默认选择第一个知识库
        if (response.data.knowledge_bases && response.data.knowledge_bases.length > 0) {
          setConfig(prev => ({
            ...prev,
            selectedKnowledgeBase: response.data.knowledge_bases[0].id
          }))
        }
      } else {
        // 显示后端返回的具体错误信息
        const errorMsg = response.data.error || '获取知识库列表失败'
        console.error('获取知识库列表失败:', errorMsg)
        alert(errorMsg)
      }
    } catch (error: any) {
      console.error('获取知识库列表失败:', error)
      const errorMsg = error.response?.data?.error || error.message || '网络请求失败'
      alert(`获取知识库列表失败: ${errorMsg}`)
    } finally {
      setLoadingKBList(false)
    }
  }

  const addLog = (message: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`])
  }

  const fetchUploadedFiles = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/uploaded-files')
      if (response.data.success) {
        setUploadedFiles(response.data.files)
      }
    } catch (error) {
      console.error('获取已上传文件失败:', error)
    }
  }

  const fetchProcessedFiles = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/processed-files')
      if (response.data.success) {
        setProcessedFiles(response.data.files)
      }
    } catch (error) {
      console.error('获取已去重文件失败:', error)
    }
  }

  const fetchLlmProcessedFiles = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/llm-processed-files')
      if (response.data.success) {
        setLlmProcessedFiles(response.data.files)
      }
    } catch (error) {
      console.error('获取LLM处理文件失败:', error)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files))
    }
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setUploadMessage('请选择要上传的文件')
      setUploadSuccess(false)
      setTimeout(() => setUploadMessage(''), 3000)
      return
    }

    setUploading(true)
    setUploadProgress(0)
    setUploadSuccess(false)

    const formData = new FormData()
    selectedFiles.forEach(file => {
      formData.append('files', file)
    })

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
        setUploadSuccess(true)
        setUploadMessage(`成功上传 ${response.data.count} 个文件！`)
        setSelectedFiles([])
        fetchUploadedFiles()
        
        // 3秒后清除成功消息
        setTimeout(() => {
          setUploadSuccess(false)
          setUploadMessage('')
        }, 3000)
      }
    } catch (error: any) {
      setUploadSuccess(false)
      setUploadMessage(`上传失败: ${error.message}`)
      setTimeout(() => setUploadMessage(''), 3000)
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const handleDeleteFile = async (filename: string) => {
    try {
      const response = await axios.delete(`http://localhost:5001/api/delete-uploaded/${filename}`)
      if (response.data.success) {
        fetchUploadedFiles()
        setUploadSuccess(true)
        setUploadMessage(`已删除: ${filename}`)
        setTimeout(() => {
          setUploadSuccess(false)
          setUploadMessage('')
        }, 2000)
      }
    } catch (error: any) {
      setUploadSuccess(false)
      setUploadMessage(`删除失败: ${error.message}`)
      setTimeout(() => setUploadMessage(''), 3000)
    }
  }

  const handleClearAllUploaded = async () => {
    const count = uploadedFiles.length
    if (count === 0) return
    
    try {
      // 逐个删除所有文件
      for (const filename of uploadedFiles) {
        await axios.delete(`http://localhost:5001/api/delete-uploaded/${filename}`)
      }
      fetchUploadedFiles()
      setUploadSuccess(true)
      setUploadMessage(`已清空 ${count} 个文件`)
      setTimeout(() => {
        setUploadSuccess(false)
        setUploadMessage('')
      }, 2000)
    } catch (error: any) {
      setUploadSuccess(false)
      setUploadMessage(`清空失败: ${error.message}`)
      setTimeout(() => setUploadMessage(''), 3000)
    }
  }

  const handleClearSelectedFiles = () => {
    setSelectedFiles([])
  }

  const handleDeleteProcessed = async (filename: string) => {
    try {
      const response = await axios.delete(`http://localhost:5001/api/delete-processed/${filename}`)
      if (response.data.success) {
        fetchProcessedFiles()
        setUploadSuccess(true)
        setUploadMessage(`已删除: ${filename}`)
        setTimeout(() => {
          setUploadSuccess(false)
          setUploadMessage('')
        }, 2000)
      }
    } catch (error: any) {
      setUploadSuccess(false)
      setUploadMessage(`删除失败: ${error.message}`)
      setTimeout(() => setUploadMessage(''), 3000)
    }
  }

  const handleClearAllProcessed = async () => {
    const count = processedFiles.length
    if (count === 0) return
    
    try {
      for (const filename of processedFiles) {
        await axios.delete(`http://localhost:5001/api/delete-processed/${filename}`)
      }
      fetchProcessedFiles()
      setUploadSuccess(true)
      setUploadMessage(`已清空 ${count} 个文件`)
      setTimeout(() => {
        setUploadSuccess(false)
        setUploadMessage('')
      }, 2000)
    } catch (error: any) {
      setUploadSuccess(false)
      setUploadMessage(`清空失败: ${error.message}`)
      setTimeout(() => setUploadMessage(''), 3000)
    }
  }

  const handleDeleteLlmProcessed = async (filename: string) => {
    try {
      const response = await axios.delete(`http://localhost:5001/api/delete-llm-processed/${filename}`)
      if (response.data.success) {
        fetchLlmProcessedFiles()
        setUploadSuccess(true)
        setUploadMessage(`已删除: ${filename}`)
        setTimeout(() => {
          setUploadSuccess(false)
          setUploadMessage('')
        }, 2000)
      }
    } catch (error: any) {
      setUploadSuccess(false)
      setUploadMessage(`删除失败: ${error.message}`)
      setTimeout(() => setUploadMessage(''), 3000)
    }
  }

  const handleClearAllLlmProcessed = async () => {
    const count = llmProcessedFiles.length
    if (count === 0) return
    
    try {
      for (const filename of llmProcessedFiles) {
        await axios.delete(`http://localhost:5001/api/delete-llm-processed/${filename}`)
      }
      fetchLlmProcessedFiles()
      setUploadSuccess(true)
      setUploadMessage(`已清空 ${count} 个文件`)
      setTimeout(() => {
        setUploadSuccess(false)
        setUploadMessage('')
      }, 2000)
    } catch (error: any) {
      setUploadSuccess(false)
      setUploadMessage(`清空失败: ${error.message}`)
      setTimeout(() => setUploadMessage(''), 3000)
    }
  }

  const handleProceedToConfig = () => {
    if (uploadedFiles.length === 0) {
      setUploadSuccess(false)
      setUploadMessage('请先上传邮件文件')
      setTimeout(() => setUploadMessage(''), 3000)
      return
    }
    setCurrentView('config')
  }

  const handleStopProcess = () => {
    if (confirm('确定要停止处理吗？已处理的数据会保留，但未完成的处理将被中断。')) {
      setShouldStop(true)
      addLog('⚠️ 用户请求停止处理...')
      console.log('⚠️ 用户请求停止处理')
    }
  }

  const handleStartAutoProcess = async () => {
    if (!config.llmApiKey || !config.kbApiKey || !config.selectedKnowledgeBase) {
      alert('请选择LLM API Key、知识库API Key和目标知识库')
      return
    }

    setRunning(true)
    setShouldStop(false)
    setProgress(0)
    setLogs([])
    addLog('🚀 开始全自动处理流程...')
    
    console.log('=================================')
    console.log('🚀 开始全自动处理流程')
    console.log('=================================')
    console.log('配置信息:')
    console.log('- LLM API Key:', config.llmApiKey.substring(0, 8) + '...')
    console.log('- KB API Key:', config.kbApiKey.substring(0, 8) + '...')
    console.log('- 知识库ID:', config.selectedKnowledgeBase)
    console.log('- 分块模式:', config.chunkMode)
    if (config.chunkMode === 'token') {
      console.log('- 分块大小:', config.chunkToken, 'tokens')
    } else {
      console.log('- 分隔符:', config.chunkSeparator)
    }
    console.log('=================================')

    try {
      // 步骤1: 邮件清洗（去重、转markdown）
      setCurrentStep('邮件清洗去重中...')
      setProgress(10)
      addLog('📧 步骤1: 开始邮件清洗和去重')
      console.log('=== 步骤1: 邮件清洗 ===')
      console.log('请求URL:', 'http://localhost:5001/api/auto/clean')
      console.log('请求参数:', { files: 'all' })
      
      const cleanResponse = await axios.post('http://localhost:5001/api/auto/clean', {
        files: 'all'
      })
      
      console.log('清洗响应:', cleanResponse.data)
      
      if (cleanResponse.data.success) {
        addLog(`✅ 邮件去重完成: ${cleanResponse.data.processed_count} 个文件`)
        console.log('✅ 步骤1成功: 处理了', cleanResponse.data.processed_count, '个文件')
        if (cleanResponse.data.duplicates > 0) {
          addLog(`   去除重复邮件: ${cleanResponse.data.duplicates} 个`)
        }
        setProgress(30)
      } else {
        console.error('❌ 步骤1失败:', cleanResponse.data.error)
        throw new Error(cleanResponse.data.error || '邮件去重失败')
      }

      // 检查是否需要停止
      if (shouldStop) {
        addLog('🛑 处理已停止（在步骤1后）')
        console.log('🛑 处理已停止')
        setCurrentStep('处理已停止')
        return
      }

      // 步骤2: LLM处理（优化内容）
      const totalFiles = cleanResponse.data.processed_count
      setCurrentStep(`LLM内容处理中 (0/${totalFiles})...`)
      addLog(`🤖 步骤2: 开始LLM内容处理 (共${totalFiles}个文件)`)
      console.log('=== 步骤2: LLM处理 ===')
      console.log('请求URL:', 'http://localhost:5001/api/auto/llm-process')
      console.log('请求参数:', {
        api_key: config.llmApiKey.substring(0, 8) + '...',
        delay: 2,
        total_files: totalFiles
      })
      
      // 实时监控LLM处理进度
      let lastProcessedCount = 0
      const progressInterval = setInterval(async () => {
        // 检查停止标志
        if (shouldStop) {
          clearInterval(progressInterval)
          return
        }
        
        try {
          // 获取当前已处理的文件数
          const statsResponse = await axios.get('http://localhost:5001/api/llm-processed-files')
          if (statsResponse.data.success) {
            const currentCount = statsResponse.data.files.length
            if (currentCount > lastProcessedCount) {
              lastProcessedCount = currentCount
              const processedCount = Math.min(currentCount, totalFiles)
              setCurrentStep(`LLM内容处理中 (${processedCount}/${totalFiles})...`)
              
              // 更新进度条: 30% + (已处理/总数 * 35%)
              const llmProgress = Math.floor((processedCount / totalFiles) * 35)
              setProgress(30 + llmProgress)
              
              console.log(`LLM处理进度: ${processedCount}/${totalFiles}`)
            }
          }
        } catch (error) {
          console.error('获取LLM处理进度失败:', error)
        }
      }, 1000) // 每1秒检查一次
      
      const llmResponse = await axios.post('http://localhost:5001/api/auto/llm-process', {
        api_key: config.llmApiKey,
        delay: 2
      })
      
      clearInterval(progressInterval) // 清除进度监控
      
      console.log('LLM响应:', llmResponse.data)
      console.log('LLM响应详情:', JSON.stringify(llmResponse.data, null, 2))
      
      if (llmResponse.data.success) {
        addLog(`✅ LLM处理完成: ${llmResponse.data.processed_count} 个文件`)
        console.log('✅ 步骤2成功: 处理了', llmResponse.data.processed_count, '个文件')
        if (llmResponse.data.failed_count > 0) {
          console.warn('⚠️ 失败:', llmResponse.data.failed_count, '个文件')
        }
        setProgress(65)
      } else {
        console.error('❌ 步骤2失败:', llmResponse.data.error)
        throw new Error(llmResponse.data.error || 'LLM处理失败')
      }

      // 检查是否需要停止
      if (shouldStop) {
        addLog('🛑 处理已停止（在步骤2后）')
        console.log('🛑 处理已停止')
        setCurrentStep('处理已停止')
        return
      }

      // 步骤3: 上传到知识库
      setCurrentStep('上传到知识库中...')
      addLog('📚 步骤3: 开始上传到知识库')
      console.log('=== 步骤3: 知识库上传 ===')
      
      const kbUploadParams: any = {
        api_key: config.kbApiKey,
        knowledge_base_id: config.selectedKnowledgeBase,
        batch_size: 15  // API限制每批最多20个，使用15确保稳定（自动分批）
      }
      
      // 根据分块模式选择参数
      if (config.chunkMode === 'token') {
        kbUploadParams.chunk_token = config.chunkToken
        console.log('分块模式: Token大小 =', config.chunkToken)
      } else {
        kbUploadParams.chunk_separator = config.chunkSeparator
        console.log('分块模式: 分隔符 =', config.chunkSeparator)
      }
      
      console.log('请求URL:', 'http://localhost:5001/api/auto/upload-kb')
      console.log('请求参数:', {
        api_key: config.kbApiKey.substring(0, 8) + '...',
        knowledge_base_id: config.selectedKnowledgeBase,
        chunk_mode: config.chunkMode,
        batch_size: 15,
        note: '后端会自动分批处理，每批最多15个文件'
      })
      
      const kbResponse = await axios.post('http://localhost:5001/api/auto/upload-kb', kbUploadParams)
      
      console.log('知识库上传响应:', kbResponse.data)
      
      if (kbResponse.data.success) {
        addLog(`✅ 知识库上传完成: ${kbResponse.data.uploaded_count} 个文件`)
        console.log('✅ 步骤3成功: 上传了', kbResponse.data.uploaded_count, '个文件')
        setProgress(100)
        setCurrentStep('全部完成！')
        addLog('🎉 全自动处理流程完成！')
        console.log('🎉 === 全自动处理流程完成 ===')
        
        // 保存处理结果
        setProcessingResult({
          cleanedCount: cleanResponse.data.processed_count,
          duplicates: cleanResponse.data.duplicates || 0,
          llmProcessed: llmResponse.data.processed_count,
          llmFailed: llmResponse.data.failed_count || 0,
          kbUploaded: kbResponse.data.uploaded_count
        })
        
        // 切换到完成页面（无自动跳转）
        setCurrentView('completed')
      } else {
        console.error('❌ 步骤3失败:', kbResponse.data.error)
        throw new Error(kbResponse.data.error || '知识库上传失败')
      }

    } catch (error: any) {
      console.error('❌ === 处理流程异常 ===')
      console.error('错误详情:', error)
      if (error.response) {
        console.error('响应状态:', error.response.status)
        console.error('响应数据:', error.response.data)
      }
      addLog(`❌ 错误: ${error.message}`)
      setCurrentStep('处理失败')
    } finally {
      setRunning(false)
      console.log('=== 处理流程结束 ===')
    }
  }

  // 如果正在处理，强制显示配置页面（保持处理状态）
  const activeView = running ? 'config' : currentView

  if (activeView === 'upload') {
    return (
      <div className="auto-pipeline-container">
        <h2 style={{ fontSize: '24px', marginBottom: '20px', display: 'flex', alignItems: 'center' }}>
          <HiCloudUpload style={{ fontSize: '28px', marginRight: '12px' }} />
          邮件上传
        </h2>

        {/* 消息提示 */}
        {uploadMessage && (
          <div className={`message-toast ${uploadSuccess ? 'success' : 'error'}`}>
            {uploadSuccess ? '✅ ' : '⚠️ '}
            {uploadMessage}
          </div>
        )}

        {/* 文件上传区域 */}
        <div className="upload-section">
          <div className="file-input-wrapper">
            <input
              type="file"
              multiple
              accept=".eml"
              onChange={handleFileSelect}
              disabled={uploading}
              id="file-upload"
              style={{ display: 'none' }}
            />
            <label htmlFor="file-upload" className="file-upload-label">
              <HiCloudUpload style={{ fontSize: '48px', marginBottom: '12px' }} />
              <p style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
                点击选择EML文件
              </p>
              <p style={{ fontSize: '14px', color: '#718096' }}>
                支持多文件上传
              </p>
            </label>
          </div>

          {/* 已选择的文件 */}
          {selectedFiles.length > 0 && (
            <div className="selected-files">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h3 style={{ fontSize: '16px', margin: 0 }}>
                  已选择 {selectedFiles.length} 个文件
                </h3>
                <button onClick={handleClearSelectedFiles} className="clear-btn">
                  <HiX /> 清空全部
                </button>
              </div>
              <div className="file-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item-with-remove">
                    <span className="file-item-name">📧 {file.name}</span>
                    <button 
                      onClick={() => {
                        setSelectedFiles(prev => prev.filter((_, i) => i !== index))
                      }}
                      className="remove-file-btn"
                    >
                      <HiX />
                    </button>
                  </div>
                ))}
              </div>
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="upload-button"
              >
                {uploading ? (
                  <>
                    <BiLoaderAlt className="spinner" />
                    上传中... {uploadProgress}%
                  </>
                ) : (
                  <>
                    <HiCloudUpload />
                    开始上传
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* 文件列表 - 三列布局 */}
        <div className="files-grid">
          {/* 已上传的文件列表 */}
          <div className="file-list-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', margin: 0, color: '#2d3748' }}>
                📂 已上传邮件
              </h3>
              <span style={{ fontSize: '14px', color: '#718096', fontWeight: 600 }}>
                {uploadedFiles.length} 个
              </span>
            </div>
            {uploadedFiles.length > 0 ? (
              <>
                <div className="file-list-scroll">
                  {uploadedFiles.map((filename, index) => (
                    <div key={index} className="file-item">
                      <span className="file-name">📧 {filename}</span>
                      <button
                        onClick={() => handleDeleteFile(filename)}
                        className="file-delete-btn"
                        title="删除"
                      >
                        <HiTrash />
                      </button>
                    </div>
                  ))}
                </div>
                <button onClick={handleClearAllUploaded} className="clear-btn">
                  <HiTrash /> 清空全部
                </button>
              </>
            ) : (
              <div className="empty-state">暂无文件</div>
            )}
          </div>

          {/* 已去重的文件列表 */}
          <div className="file-list-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', margin: 0, color: '#2d3748' }}>
                ✅ 已去重邮件
              </h3>
              <span style={{ fontSize: '14px', color: '#718096', fontWeight: 600 }}>
                {processedFiles.length} 个
              </span>
            </div>
            {processedFiles.length > 0 ? (
              <>
                <div className="file-list-scroll">
                  {processedFiles.map((filename, index) => (
                    <div key={index} className="file-item">
                      <span className="file-name">📄 {filename}</span>
                      <button
                        onClick={() => handleDeleteProcessed(filename)}
                        className="file-delete-btn"
                        title="删除"
                      >
                        <HiTrash />
                      </button>
                    </div>
                  ))}
                </div>
                <button onClick={handleClearAllProcessed} className="clear-btn">
                  <HiTrash /> 清空全部
                </button>
              </>
            ) : (
              <div className="empty-state">暂无文件</div>
            )}
          </div>

          {/* LLM处理的文件列表 */}
          <div className="file-list-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', margin: 0, color: '#2d3748' }}>
                🤖 LLM处理
              </h3>
              <span style={{ fontSize: '14px', color: '#718096', fontWeight: 600 }}>
                {llmProcessedFiles.length} 个
              </span>
            </div>
            {llmProcessedFiles.length > 0 ? (
              <>
                <div className="file-list-scroll">
                  {llmProcessedFiles.map((filename, index) => (
                    <div key={index} className="file-item">
                      <span className="file-name">✨ {filename}</span>
                      <button
                        onClick={() => handleDeleteLlmProcessed(filename)}
                        className="file-delete-btn"
                        title="删除"
                      >
                        <HiTrash />
                      </button>
                    </div>
                  ))}
                </div>
                <button onClick={handleClearAllLlmProcessed} className="clear-btn">
                  <HiTrash /> 清空全部
                </button>
              </>
            ) : (
              <div className="empty-state">暂无文件</div>
            )}
          </div>
        </div>

        {/* 下一步按钮 */}
        {uploadedFiles.length > 0 && (
          <button
            onClick={handleProceedToConfig}
            className="proceed-button"
            style={{ marginTop: '30px' }}
          >
            下一步：配置处理参数 →
          </button>
        )}

        <style jsx>{`
          .auto-pipeline-container {
            padding: 30px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          }

          .upload-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
          }

          .file-input-wrapper {
            margin-bottom: 20px;
          }

          .file-upload-label {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 30px 40px;
            border: 2px dashed #cbd5e0;
            border-radius: 12px;
            background: white;
            cursor: pointer;
            transition: all 0.3s;
            color: #667eea;
          }

          .file-upload-label:hover {
            border-color: #667eea;
            background: #f7fafc;
          }

          .selected-files {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
          }

          .file-list {
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: 16px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 8px;
          }

          .file-item {
            padding: 10px 12px;
            background: #f7fafc;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 14px;
            color: #4a5568;
          }

          .file-item-with-remove {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 14px;
            background: #f7fafc;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 14px;
            color: #4a5568;
            transition: all 0.2s;
          }

          .file-item-with-remove:hover {
            background: #edf2f7;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          }

          .file-item-name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-right: 12px;
          }

          .remove-file-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            padding: 0;
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            cursor: pointer;
            color: #718096;
            transition: all 0.2s;
            flex-shrink: 0;
          }

          .remove-file-btn:hover {
            background: #fc8181;
            border-color: #fc8181;
            color: white;
          }

          .clear-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: #fee;
            color: #c53030;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
          }

          .clear-btn:hover {
            background: #fed7d7;
          }

          .clear-all-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: #fee;
            color: #c53030;
            border: 1px solid #fc8181;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
          }

          .clear-all-btn:hover {
            background: #fc8181;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(252, 129, 129, 0.3);
          }

          .upload-button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s;
          }

          .upload-button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
          }

          .upload-button:disabled {
            opacity: 0.7;
            cursor: not-allowed;
          }

          .uploaded-files-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
          }

          .uploaded-file-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 20px;
            max-height: 500px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px;
            background: white;
          }

          .uploaded-file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: white;
            border-radius: 8px;
            transition: all 0.3s;
          }

          .uploaded-file-item:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          }

          .file-name {
            font-size: 14px;
            color: #2d3748;
          }

          .delete-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: #fee;
            color: #c53030;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
          }

          .delete-btn:hover {
            background: #fc8181;
            color: white;
          }

          .proceed-button {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
          }

          .proceed-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(72, 187, 120, 0.4);
          }

          .spinner {
            animation: spin 1s linear infinite;
          }

          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }

          /* 三列文件列表布局 */
          .files-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 30px;
          }

          .file-list-card {
            background: #f8f9fa;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            height: 500px;
          }

          .file-list-scroll {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 12px;
            padding-right: 8px;
          }

          .file-list-scroll::-webkit-scrollbar {
            width: 6px;
          }

          .file-list-scroll::-webkit-scrollbar-track {
            background: #edf2f7;
            border-radius: 3px;
          }

          .file-list-scroll::-webkit-scrollbar-thumb {
            background: #cbd5e0;
            border-radius: 3px;
          }

          .file-list-scroll::-webkit-scrollbar-thumb:hover {
            background: #a0aec0;
          }

          .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 12px;
            background: white;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 13px;
            transition: all 0.2s;
            border: 1px solid transparent;
          }

          .file-item:hover {
            border-color: #667eea;
            box-shadow: 0 2px 6px rgba(102, 126, 234, 0.15);
          }

          .file-name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-right: 8px;
            color: #4a5568;
          }

          .file-delete-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            padding: 0;
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            color: #e53e3e;
            font-size: 14px;
          }

          .file-delete-btn:hover {
            background: #fff5f5;
            border-color: #fc8181;
            transform: scale(1.05);
          }

          .clear-btn {
            width: 100%;
            padding: 10px;
            background: #fff;
            color: #e53e3e;
            border: 1px solid #e53e3e;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: all 0.2s;
          }

          .clear-btn:hover {
            background: #fff5f5;
            border-color: #fc8181;
          }

          .empty-state {
            padding: 40px 20px;
            text-align: center;
            color: #a0aec0;
            font-size: 14px;
          }

          @media (max-width: 1200px) {
            .files-grid {
              grid-template-columns: 1fr;
            }
            
            .file-list-card {
              height: 350px;
            }
          }

          /* 消息提示框 */
          .message-toast {
            position: fixed;
            top: 80px;
            right: 30px;
            padding: 16px 24px;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 500;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            z-index: 1000;
            animation: slideIn 0.3s ease-out, fadeOut 0.3s ease-in 2.7s forwards;
            max-width: 400px;
            word-wrap: break-word;
          }

          .message-toast.success {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
          }

          .message-toast.error {
            background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
            color: white;
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

          @keyframes fadeOut {
            from {
              opacity: 1;
            }
            to {
              opacity: 0;
              transform: translateX(400px);
            }
          }
        `}</style>
      </div>
    )
  }

  // 配置视图
  if (activeView === 'config') {
    return (
      <div className="auto-pipeline-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '24px', margin: 0, display: 'flex', alignItems: 'center' }}>
            <HiCog style={{ fontSize: '28px', marginRight: '12px' }} />
            全自动处理配置
          </h2>
          <button 
            onClick={() => setCurrentView('upload')}
            style={{
              padding: '10px 20px',
              background: '#e2e8f0',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500
            }}
          >
            ← 返回上传
          </button>
        </div>

        {/* LLM配置部分 */}
        <div className="config-section">
          <h3 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center' }}>
            <HiCog style={{ fontSize: '24px', marginRight: '12px' }} />
            1️⃣ LLM邮件清洗配置
          </h3>
        
        {loadingConfig ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <BiLoaderAlt className="spinner" style={{ fontSize: '32px', color: '#667eea' }} />
            <p style={{ marginTop: '16px', color: '#718096' }}>加载配置中...</p>
          </div>
        ) : envConfig ? (
          <>
            <div className="env-info-card">
              <div className="info-header">
                <HiCheckCircle style={{ color: '#48bb78', fontSize: '20px' }} />
                <span>已从环境配置文件读取</span>
              </div>
              <div className="info-content">
                <p>✅ 检测到 {envConfig.llm_api_keys.length} 个LLM API Key配置</p>
              </div>
            </div>

            <div className="config-item-full">
              <label>选择LLM API Key *</label>
              <select
                value={config.selectedLlmKey}
                onChange={(e) => {
                  const value = e.target.value
                  if (value === 'custom') {
                    setConfig(prev => ({
                      ...prev,
                      selectedLlmKey: 'custom',
                      llmApiKey: ''
                    }))
                  } else {
                    const selected = envConfig.llm_api_keys.find((k: any) => k.id === value)
                    if (selected) {
                      setConfig(prev => ({
                        ...prev,
                        selectedLlmKey: selected.id,
                        llmApiKey: selected.value
                      }))
                    }
                  }
                }}
                disabled={running}
                className="api-key-select"
              >
                {envConfig.llm_api_keys.map((key: any) => (
                  <option key={key.id} value={key.id}>
                    {key.name} - {key.masked}
                  </option>
                ))}
                <option value="custom">🔑 自定义输入...</option>
              </select>
              <p className="config-hint">
                用于邮件内容清洗和结构化处理
              </p>
            </div>

            {config.selectedLlmKey === 'custom' ? (
              <div className="config-item-full">
                <label>输入自定义LLM API Key *</label>
                <input
                  type="text"
                  value={config.llmApiKey}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    llmApiKey: e.target.value
                  }))}
                  disabled={running}
                  className="api-key-select"
                  placeholder="请输入完整的API Key，例如：app-xxxxxx"
                  style={{ fontFamily: 'monospace' }}
                />
                <p className="config-hint">
                  请输入有效的GPTBots LLM API Key
                </p>
              </div>
            ) : (
              <div className="selected-key-display">
                <div className="key-label">当前使用的LLM API Key:</div>
                <div className="key-value">
                  {envConfig.llm_api_keys.find((k: any) => k.id === config.selectedLlmKey)?.masked || '未选择'}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="error-card">
            <p>❌ 无法加载环境配置</p>
            <p style={{ fontSize: '14px', color: '#718096', marginTop: '8px' }}>
              请确保 .env 文件存在并包含正确的配置
            </p>
          </div>
        )}
      </div>

      {/* 知识库配置部分 */}
      <div className="config-section" style={{ marginTop: '20px' }}>
        <h3 style={{ fontSize: '20px', marginBottom: '20px', display: 'flex', alignItems: 'center' }}>
          <HiCog style={{ fontSize: '24px', marginRight: '12px' }} />
          2️⃣ 知识库上传配置
        </h3>
        
        {loadingConfig ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <BiLoaderAlt className="spinner" style={{ fontSize: '32px', color: '#667eea' }} />
            <p style={{ marginTop: '16px', color: '#718096' }}>加载配置中...</p>
          </div>
        ) : envConfig && envConfig.kb_api_keys ? (
          <>
            <div className="env-info-card">
              <div className="info-header">
                <HiCheckCircle style={{ color: '#48bb78', fontSize: '20px' }} />
                <span>已从环境配置文件读取</span>
              </div>
              <div className="info-content">
                <p>✅ 检测到 {envConfig.kb_api_keys.length} 个知识库 API Key配置</p>
              </div>
            </div>

            <div className="config-item-full">
              <label>选择知识库 API Key *</label>
              <select
                value={config.selectedKbKey}
                onChange={(e) => {
                  const value = e.target.value
                  if (value === 'custom') {
                    setConfig(prev => ({
                      ...prev,
                      selectedKbKey: 'custom',
                      kbApiKey: ''
                    }))
                    setKnowledgeBases([])
                  } else {
                    const selected = envConfig.kb_api_keys.find((k: any) => k.id === value)
                    if (selected) {
                      setConfig(prev => ({
                        ...prev,
                        selectedKbKey: selected.id,
                        kbApiKey: selected.value
                      }))
                      // 重新获取知识库列表
                      fetchKnowledgeBases(selected.value)
                    }
                  }
                }}
                disabled={running}
                className="api-key-select"
              >
                {envConfig.kb_api_keys.map((key: any) => (
                  <option key={key.id} value={key.id}>
                    {key.name} - {key.masked}
                  </option>
                ))}
                <option value="custom">🔑 自定义输入...</option>
              </select>
              <p className="config-hint">
                用于上传处理后的文档到GPTBots知识库
              </p>
            </div>

            {config.selectedKbKey === 'custom' ? (
              <>
                <div className="config-item-full">
                  <label>输入自定义知识库 API Key *</label>
                  <input
                    type="text"
                    value={config.kbApiKey}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      kbApiKey: e.target.value
                    }))}
                    disabled={running}
                    className="api-key-select"
                    placeholder="请输入完整的API Key，例如：app-xxxxxx"
                    style={{ fontFamily: 'monospace' }}
                  />
                  <p className="config-hint">
                    请输入有效的GPTBots知识库 API Key
                  </p>
                </div>
                <button
                  onClick={() => {
                    if (config.kbApiKey) {
                      fetchKnowledgeBases(config.kbApiKey)
                    }
                  }}
                  disabled={!config.kbApiKey || loadingKBList}
                  style={{
                    padding: '10px 20px',
                    background: '#667eea',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: config.kbApiKey && !loadingKBList ? 'pointer' : 'not-allowed',
                    fontSize: '14px',
                    fontWeight: 500,
                    marginBottom: '20px',
                    opacity: config.kbApiKey && !loadingKBList ? 1 : 0.5
                  }}
                >
                  {loadingKBList ? '获取中...' : '获取知识库列表'}
                </button>
              </>
            ) : (
              <div className="selected-key-display">
                <div className="key-label">当前使用的知识库 API Key:</div>
                <div className="key-value">
                  {envConfig.kb_api_keys.find((k: any) => k.id === config.selectedKbKey)?.masked || '未选择'}
                </div>
              </div>
            )}

            {loadingKBList ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <BiLoaderAlt className="spinner" style={{ fontSize: '32px', color: '#667eea' }} />
                <p style={{ marginTop: '16px', color: '#718096' }}>正在获取知识库列表...</p>
              </div>
            ) : knowledgeBases.length > 0 ? (
              <>
                <div className="config-item-full">
                  <label>选择目标知识库 *</label>
                  <select
                    value={config.selectedKnowledgeBase}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      selectedKnowledgeBase: e.target.value
                    }))}
                    disabled={running}
                    className="api-key-select"
                  >
                    {knowledgeBases.map((kb: any) => (
                      <option key={kb.id} value={kb.id}>
                        {kb.name} ({kb.doc_count} 个文档)
                      </option>
                    ))}
                  </select>
                  <p className="config-hint">
                    清洗后的邮件将上传到此知识库
                  </p>
                </div>

                <div className="config-item-full">
                  <label>分块方式 *</label>
                  <div style={{ display: 'flex', gap: '20px', marginBottom: '15px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="chunkMode"
                        value="token"
                        checked={config.chunkMode === 'token'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          chunkMode: 'token'
                        }))}
                        disabled={running}
                        style={{ marginRight: '8px' }}
                      />
                      <span>按Token大小分块</span>
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="chunkMode"
                        value="separator"
                        checked={config.chunkMode === 'separator'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          chunkMode: 'separator'
                        }))}
                        disabled={running}
                        style={{ marginRight: '8px' }}
                      />
                      <span>按分隔符分块</span>
                    </label>
                  </div>
                  
                  {config.chunkMode === 'token' ? (
                    <>
                      <input
                        type="number"
                        value={config.chunkToken}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          chunkToken: parseInt(e.target.value)
                        }))}
                        disabled={running}
                        className="api-key-select"
                        min="100"
                        max="2000"
                        placeholder="输入Token数"
                      />
                      <p className="config-hint">
                        文档将按指定的Token数分块，默认600（范围：100-2000）
                      </p>
                    </>
                  ) : (
                    <>
                      <input
                        type="text"
                        value={config.chunkSeparator}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          chunkSeparator: e.target.value
                        }))}
                        disabled={running}
                        className="api-key-select"
                        placeholder="输入分隔符，如 \n\n 或 ### 等"
                      />
                      <p className="config-hint">
                        文档将按指定的分隔符分块，常用：\n\n（双换行）、\n---\n（分隔线）、###（三级标题）
                      </p>
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="error-card">
                <p>❌ 未找到可用的知识库</p>
                <p style={{ fontSize: '14px', color: '#718096', marginTop: '8px' }}>
                  请确保您的API Key有权访问知识库
                </p>
              </div>
            )}
          </>
        ) : (
          <div className="error-card">
            <p>❌ 无法加载环境配置</p>
            <p style={{ fontSize: '14px', color: '#718096', marginTop: '8px' }}>
              请确保 .env 文件存在并包含正确的配置
            </p>
          </div>
        )}
      </div>

      {/* 开始处理按钮 */}
      {envConfig && !loadingConfig && knowledgeBases.length > 0 && (
        <div style={{ marginTop: '30px', display: 'flex', gap: '16px' }}>
          <button
            onClick={handleStartAutoProcess}
            disabled={running}
            className="start-button"
            style={{ fontSize: '18px', padding: '18px', flex: 1 }}
          >
            {running ? (
              <>
                <BiLoaderAlt className="spinner" />
                处理中...
              </>
            ) : (
              <>
                <HiPlay />
                开始全自动处理
              </>
            )}
          </button>
          
          {running && (
            <button
              onClick={handleStopProcess}
              className="stop-button"
              style={{ fontSize: '18px', padding: '18px' }}
            >
              <HiX style={{ fontSize: '20px' }} />
              紧急停止
            </button>
          )}
        </div>
      )}

      {running && (
        <div className="progress-section">
          <div className="progress-info">
            <span>{currentStep}</span>
            <span>{progress}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
        </div>
      )}

      {logs.length > 0 && (
        <div className="logs-section">
          <h3 style={{ fontSize: '16px', marginBottom: '10px' }}>📋 执行日志</h3>
          <div className="logs-container">
            {logs.map((log, index) => (
              <div key={index} className="log-item">{log}</div>
            ))}
          </div>
        </div>
      )}

      <style jsx>{`
        .auto-pipeline-container {
          padding: 30px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .config-section {
          background: #f8f9fa;
          padding: 25px;
          border-radius: 10px;
          margin-bottom: 20px;
        }

        .config-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 25px;
        }

        .config-item {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .config-item label {
          font-size: 14px;
          font-weight: 600;
          color: #495057;
        }

        .config-item input {
          padding: 10px 12px;
          border: 2px solid #dee2e6;
          border-radius: 8px;
          font-size: 14px;
          transition: all 0.3s;
        }

        .config-item input:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .config-item input:disabled {
          background: #e9ecef;
          cursor: not-allowed;
        }

        .config-item-full {
          display: flex;
          flex-direction: column;
          gap: 10px;
          margin: 25px 0;
        }

        .config-item-full label {
          font-size: 15px;
          font-weight: 600;
          color: #2d3748;
        }

        .api-key-select {
          padding: 12px 16px;
          border: 2px solid #dee2e6;
          border-radius: 8px;
          font-size: 15px;
          background: white;
          cursor: pointer;
          transition: all 0.3s;
        }

        .api-key-select:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .api-key-select:disabled {
          background: #e9ecef;
          cursor: not-allowed;
        }

        .config-hint {
          font-size: 13px;
          color: #718096;
          margin: 0;
        }

        .env-info-card {
          background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
          border: 2px solid #81e6d9;
          border-radius: 10px;
          padding: 16px 20px;
          margin-bottom: 25px;
        }

        .info-header {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 15px;
          font-weight: 600;
          color: #234e52;
          margin-bottom: 8px;
        }

        .info-content {
          font-size: 14px;
          color: #2c7a7b;
        }

        .info-content p {
          margin: 4px 0;
        }

        .selected-key-display {
          background: #f7fafc;
          border: 2px solid #e2e8f0;
          border-radius: 8px;
          padding: 16px;
          margin: 20px 0;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .key-label {
          font-size: 14px;
          font-weight: 600;
          color: #4a5568;
        }

        .key-value {
          font-family: 'Courier New', monospace;
          font-size: 14px;
          color: #667eea;
          font-weight: 600;
          background: white;
          padding: 6px 12px;
          border-radius: 6px;
          border: 1px solid #cbd5e0;
        }

        .error-card {
          background: #fff5f5;
          border: 2px solid #feb2b2;
          border-radius: 10px;
          padding: 20px;
          text-align: center;
          color: #c53030;
        }

        .start-button {
          width: 100%;
          padding: 16px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 10px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          transition: all 0.3s;
        }

        .start-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }

        .start-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .stop-button {
          padding: 16px 32px;
          background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
          color: white;
          border: none;
          border-radius: 10px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          transition: all 0.3s;
          white-space: nowrap;
        }

        .stop-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(245, 101, 101, 0.4);
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .progress-section {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 10px;
          margin-bottom: 20px;
        }

        .progress-info {
          display: flex;
          justify-content: space-between;
          margin-bottom: 10px;
          font-size: 14px;
          font-weight: 600;
          color: #495057;
        }

        .progress-bar {
          width: 100%;
          height: 12px;
          background: #e9ecef;
          border-radius: 6px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
          transition: width 0.5s ease;
          border-radius: 6px;
          position: relative;
          overflow: hidden;
        }

        .progress-fill::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.3),
            transparent
          );
          animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }

        .logs-section {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 10px;
        }

        .logs-container {
          max-height: 400px;
          overflow-y: auto;
          background: #2d3748;
          padding: 15px;
          border-radius: 8px;
          font-family: 'Courier New', monospace;
          font-size: 13px;
        }

        .log-item {
          color: #e2e8f0;
          padding: 4px 0;
          line-height: 1.6;
        }

        .logs-container::-webkit-scrollbar {
          width: 8px;
        }

        .logs-container::-webkit-scrollbar-track {
          background: #1a202c;
          border-radius: 4px;
        }

        .logs-container::-webkit-scrollbar-thumb {
          background: #4a5568;
          border-radius: 4px;
        }
      `}</style>
    </div>
  )
  }

  if (activeView === 'completed') {
    return (
      <div className="auto-pipeline-container">
        {/* 白色容器卡片 */}
        <div className="completed-card">
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center',
            minHeight: '500px',
            textAlign: 'center'
          }}>
            <div style={{
              width: '120px',
              height: '120px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '30px',
              animation: 'bounce 0.6s ease-in-out'
            }}>
              <HiCheckCircle style={{ fontSize: '72px', color: 'white' }} />
            </div>

            <h2 style={{ fontSize: '32px', marginBottom: '16px', color: '#2d3748' }}>
              🎉 处理完成！
            </h2>

            <p style={{ fontSize: '18px', color: '#718096', marginBottom: '40px' }}>
              所有邮件已成功处理并上传到知识库
            </p>

            {processingResult && (
              <div className="result-summary-box">
                <div className="result-row">
                  <span>去重后的邮件总数:</span>
                  <span className="result-value">{processingResult.cleanedCount} 个文件</span>
                </div>
                {processingResult.duplicates > 0 && (
                  <div className="result-row">
                    <span>去除重复:</span>
                    <span className="result-value" style={{color: '#ed8936'}}>{processingResult.duplicates} 个</span>
                  </div>
                )}
                <div className="result-row">
                  <span>LLM处理:</span>
                  <span className="result-value">{processingResult.llmProcessed} 个文件</span>
                </div>
                {processingResult.llmFailed > 0 && (
                  <div className="result-row">
                    <span>处理失败:</span>
                    <span className="result-value" style={{color: '#e53e3e'}}>{processingResult.llmFailed} 个</span>
                  </div>
                )}
                <div className="result-row" style={{borderBottom: 'none'}}>
                  <span>知识库上传:</span>
                  <span className="result-value" style={{color: '#48bb78'}}>{processingResult.kbUploaded} 个文件</span>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '16px' }}>
              <button
                onClick={() => {
                  // 重置状态，准备处理更多邮件
                  setCurrentView('upload')
                  setProgress(0)
                  setLogs([])
                  setCurrentStep('')
                  setProcessingResult(null)
                  setSelectedFiles([])
                  fetchUploadedFiles()
                }}
                className="action-button primary-button"
              >
                <HiCloudUpload style={{ fontSize: '20px' }} />
                继续处理更多邮件
              </button>

              <button
                onClick={() => {
                  if (onNavigate) {
                    onNavigate('results')
                  }
                }}
                className="action-button secondary-button"
              >
                📊 查看详细结果
              </button>
            </div>
          </div>
        </div>

        <style jsx>{`
          .completed-card {
            background: white;
            border-radius: 20px;
            padding: 60px 40px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
          }

          .result-summary-box {
            background: #f7fafc;
            border-radius: 16px;
            padding: 30px;
            border: 1px solid #e2e8f0;
            margin-bottom: 50px;
            min-width: 400px;
          }

          .result-row {
            display: flex;
            justify-content: space-between;
            padding: 16px 0;
            border-bottom: 1px solid #e2e8f0;
            font-size: 16px;
          }

          .result-row span:first-child {
            color: #4a5568;
            font-weight: 500;
          }

          .result-value {
            color: #667eea;
            font-weight: 600;
          }

          .action-button {
            padding: 16px 32px;
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            fontSize: 16px;
            fontWeight: 600;
            display: flex;
            alignItems: center;
            gap: 10px;
            transition: all 0.3s;
          }

          .primary-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
          }

          .primary-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
          }

          .secondary-button {
            background: linear-gradient(135deg, #4299e1 0%, #667eea 100%);
            box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4);
          }

          .secondary-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(66, 153, 225, 0.5);
          }

          @keyframes bounce {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
          }
        `}</style>
      </div>
    )
  }

  return null
}

