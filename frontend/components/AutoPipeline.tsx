import { useState, useEffect } from 'react'
import { HiCog, HiCheckCircle, HiPlay, HiCloudUpload, HiTrash, HiX, HiFolderOpen, HiClock } from 'react-icons/hi'
import { BiLoaderAlt } from 'react-icons/bi'
import axios from 'axios'

interface AutoPipelineProps {
  onNavigate?: (page: string) => void
  onProcessingChange?: (isProcessing: boolean) => void  // 新增：处理状态变化回调
}

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

export default function AutoPipeline({ onNavigate, onProcessingChange }: AutoPipelineProps) {
  const [currentView, setCurrentView] = useState<'config' | 'completed'>('config')
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
  const [batchLabel, setBatchLabel] = useState('')
  
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
  const [envConfigError, setEnvConfigError] = useState<string>('')  // 配置加载错误信息
  
  // 知识库列表
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([])
  const [loadingKBList, setLoadingKBList] = useState(false)
  
  // 批次列表
  const [batches, setBatches] = useState<any[]>([])
  const [selectedBatchIds, setSelectedBatchIds] = useState<string[]>([])
  const [loadingBatches, setLoadingBatches] = useState(false)
  const [hideCompletedBatches, setHideCompletedBatches] = useState(true)  // 默认隐藏已完成批次
  
  // 配置折叠状态
  const [showLlmConfig, setShowLlmConfig] = useState(false)  // 默认折叠LLM配置
  const [showKbConfig, setShowKbConfig] = useState(false)    // 默认折叠知识库配置
  
  // 预计时间相关状态
  const [estimatedTime, setEstimatedTime] = useState(0)  // 预计总时间（秒）
  const [remainingTime, setRemainingTime] = useState(0)  // 剩余时间（秒）
  const [startTime, setStartTime] = useState(0)  // 开始处理的时间戳
  const [totalFilesToProcess, setTotalFilesToProcess] = useState(0)  // 总文件数
  
  // 全局重复邮件
  const [globalDuplicates, setGlobalDuplicates] = useState<any[]>([])

  useEffect(() => {
    fetchUploadedFiles()
    fetchProcessedFiles()
    fetchLlmProcessedFiles()
    fetchBatches()
    
    // 每次组件挂载时都刷新批次列表，确保显示最新状态
    const interval = setInterval(() => {
      if (running) {
        fetchBatches()
      }
    }, 5000)  // 每5秒刷新一次批次状态
    
    return () => clearInterval(interval)
  }, [running])

  // 通知父组件处理状态变化
  useEffect(() => {
    onProcessingChange?.(running)
  }, [running, onProcessingChange])
  
  // 倒计时逻辑
  useEffect(() => {
    if (!running || remainingTime <= 0) return
    
    const timer = setInterval(() => {
      setRemainingTime(prev => {
        if (prev <= 1) {
          return 0
        }
        return prev - 1
      })
    }, 1000)
    
    return () => clearInterval(timer)
  }, [running, remainingTime])

  useEffect(() => {
    if (currentView === 'config') {
      fetchEnvConfig()
    }
  }, [currentView])

  const fetchEnvConfig = async () => {
    setLoadingConfig(true)
    setEnvConfigError('')
    try {
      const response = await axios.get(getApiUrl('/api/config/env'))
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
      } else {
        // 保存详细错误信息
        const errorMsg = response.data.error || '未知错误'
        const details = response.data.details || ''
        const cwd = response.data.cwd || ''
        const scriptDir = response.data.script_dir || ''
        
        let fullError = `${errorMsg}\n\n`
        if (details) fullError += `详细信息:\n${details}\n\n`
        if (cwd) fullError += `当前工作目录: ${cwd}\n`
        if (scriptDir) fullError += `脚本目录: ${scriptDir}`
        
        setEnvConfigError(fullError)
        console.error('环境配置错误:', response.data)
      }
    } catch (error: any) {
      console.error('获取环境配置失败:', error)
      const errorMsg = error.response?.data?.error || error.message || '网络错误'
      setEnvConfigError(`无法连接到后端API\n错误: ${errorMsg}\n\n请确保后端服务正在运行 (port 5001)`)
    } finally {
      setLoadingConfig(false)
    }
  }

  const fetchBatches = async () => {
    setLoadingBatches(true)
    try {
      const response = await axios.get(getApiUrl('/api/batches'))
      if (response.data.success) {
        setBatches(response.data.batches)
      }
    } catch (error: any) {
      console.error('获取批次列表失败:', error)
    } finally {
      setLoadingBatches(false)
    }
  }

  const fetchKnowledgeBases = async (apiKey: string) => {
    setLoadingKBList(true)
    try {
      const response = await axios.post(getApiUrl('/api/knowledge-bases'), {
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

  // 格式化剩余时间
  const formatTime = (seconds: number) => {
    if (seconds <= 0) return '即将完成'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    if (mins > 0) {
      return `${mins}分${secs}秒`
    }
    return `${secs}秒`
  }

  const fetchUploadedFiles = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/uploaded-files'))
      if (response.data.success) {
        setUploadedFiles(response.data.files)
      }
    } catch (error) {
      console.error('获取已上传文件失败:', error)
    }
  }

  const fetchProcessedFiles = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/processed-files'))
      if (response.data.success) {
        setProcessedFiles(response.data.files)
      }
    } catch (error) {
      console.error('获取已去重文件失败:', error)
    }
  }

  const fetchLlmProcessedFiles = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/llm-processed-files'))
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

    // 验证批次标签必填
    if (!batchLabel.trim()) {
      setUploadMessage('请输入批次标签')
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
    
    // 添加批次标签（必填）
    formData.append('label', batchLabel.trim())

    try {
      const response = await axios.post(getApiUrl('/api/upload'), formData, {
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
        const batchInfo = response.data.batch_id 
          ? `批次: ${response.data.batch_id}` 
          : ''
        setUploadMessage(`成功上传 ${response.data.count} 个文件！${batchInfo}`)
        setSelectedFiles([])
        setBatchLabel('')
        fetchUploadedFiles()
        
        // 5秒后清除成功消息
        setTimeout(() => {
          setUploadSuccess(false)
          setUploadMessage('')
        }, 5000)
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
      const response = await axios.delete(`/api/delete-uploaded/${filename}`)
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
        await axios.delete(`/api/delete-uploaded/${filename}`)
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
      const response = await axios.delete(`/api/delete-processed/${filename}`)
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
        await axios.delete(`/api/delete-processed/${filename}`)
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
      const response = await axios.delete(`/api/delete-llm-processed/${filename}`)
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
        await axios.delete(`/api/delete-llm-processed/${filename}`)
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
    if (uploadedFiles.length === 0 && batches.length === 0) {
      setUploadSuccess(false)
      setUploadMessage('请先上传邮件文件或创建批次')
      setTimeout(() => setUploadMessage(''), 3000)
      return
    }
    setCurrentView('config')
  }

  const handleStopProcess = async () => {
    if (confirm('确定要停止处理吗？已处理的数据会保留，但未完成的处理将被中断。')) {
      setShouldStop(true)
      setCurrentStep('正在停止处理...')
      addLog('⚠️ 用户请求停止处理...')
      addLog('   请稍候，正在安全停止当前任务...')
      console.log('⚠️ 用户请求停止处理')
      
      // 发送停止信号到后端
      try {
        await axios.post(getApiUrl('/api/auto/stop'))
        addLog('   ✅ 停止信号已发送到后端')
      } catch (error) {
        console.error('发送停止信号失败:', error)
        addLog('   ⚠️ 停止信号发送失败，但前端会停止')
      }
    }
  }

  const handleStartAutoProcess = async () => {
    if (!config.llmApiKey || !config.kbApiKey || !config.selectedKnowledgeBase) {
      alert('请选择LLM API Key、知识库API Key和目标知识库')
      return
    }

    // 检查是否选择了批次
    if (selectedBatchIds.length === 0) {
      alert('请至少选择一个批次进行处理')
      return
    }
    
    // 限制只能选择一个批次
    if (selectedBatchIds.length > 1) {
      alert('一次只能处理一个批次，请只选择一个批次')
      return
    }

    setRunning(true)
    setShouldStop(false)
    setProgress(0)
    setLogs([])
    addLog('🚀 开始全自动处理流程...')
    
    // 获取选中批次的文件数
    const batchId = selectedBatchIds[0]
    const batch = batches.find(b => b.batch_id === batchId)
    const totalFiles = batch?.file_count || 0
    setTotalFilesToProcess(totalFiles)
    
    // 动态预估：初始使用经验值
    const initialEstimatedTimePerFile = 17  // 秒（基于实际日志：LLM处理~17秒/文件）
    const initialEstimated = totalFiles * initialEstimatedTimePerFile
    setEstimatedTime(initialEstimated)
    setRemainingTime(initialEstimated)
    setStartTime(Date.now())
    
    const hours = Math.floor(initialEstimated / 3600)
    const minutes = Math.floor((initialEstimated % 3600) / 60)
    const seconds = Math.ceil(initialEstimated % 60)
    const timeStr = hours > 0 
      ? `${hours}小时${minutes}分${seconds}秒`
      : minutes > 0 
        ? `${minutes}分${seconds}秒`
        : `${seconds}秒`
    
    addLog(`📊 预计处理 ${totalFiles} 个文件 (批次: ${batchId})`)
    addLog(`   ⏱️ 初步预估: ${timeStr}（基于原始文件数）`)
    addLog(`   📝 注意：去重后会自动调整预估时间`)
    
    try {
      // ========== 单批次处理流程 ==========
      await processSingleBatchFlow(batchId, totalFiles)
    } catch (error: any) {
      console.error('❌ === 处理流程异常 ===')
      console.error('错误详情:', error)
      
      if (axios.isAxiosError(error) && error.response) {
        console.error('响应状态:', error.response.status)
        console.error('响应数据:', error.response.data)
      }
      
      addLog(`❌ 错误: ${error.message}`)
      setCurrentStep('处理失败')
      setProgress(0)
    } finally {
      console.log('=== 处理流程结束 ===')
      setRunning(false)
      setShouldStop(false)
    }
  }

  // ========== 单批次处理流程（原有逻辑）==========
  const processSingleBatchFlow = async (batchId: string, totalFiles: number) => {
    try {
      // 步骤1: 邮件清洗（去重、转markdown）
      setCurrentStep('邮件清洗去重中...')
      setProgress(10)
      addLog(`📧 步骤1: 开始邮件清洗和去重 (1个批次)`)
      
      const cleanResponse = await axios.post(getApiUrl('/api/auto/clean'), {
        batch_ids: [batchId],
        skip_if_exists: true  // 启用智能跳过
      })
      
      console.log('清洗响应:', cleanResponse.data)
      
      if (cleanResponse.data.success) {
        if (cleanResponse.data.skipped) {
          addLog(`⏭️ 邮件去重已完成，跳过此步骤`)
          if (cleanResponse.data.skipped_batches && cleanResponse.data.skipped_batches.length > 0) {
            addLog(`   跳过批次: ${cleanResponse.data.skipped_batches.join(', ')}`)
          }
        } else {
        addLog(`✅ 邮件去重完成: ${cleanResponse.data.processed_count} 个文件`)
        if (cleanResponse.data.duplicates > 0) {
          addLog(`   去除重复邮件: ${cleanResponse.data.duplicates} 个`)
        }
        // 显示并保存全局重复邮件
        if (cleanResponse.data.global_duplicates && cleanResponse.data.global_duplicates.length > 0) {
          addLog(`   🔄 跨批次重复邮件: ${cleanResponse.data.global_duplicates.length} 个（已跳过）`)
          setGlobalDuplicates(cleanResponse.data.global_duplicates)
        }
        }
        console.log('✅ 步骤1成功: 处理了', cleanResponse.data.processed_count, '个文件')
        setProgress(30)
      } else {
        console.error('❌ 步骤1失败:', cleanResponse.data.error)
        throw new Error(cleanResponse.data.error || '邮件去重失败')
      }

      // 检查是否需要停止
      if (shouldStop) {
        addLog('🛑 处理已停止（在步骤1后）')
        addLog(`   ✅ 已完成清洗：${cleanResponse.data.processed_count} 个文件`)
        console.log('🛑 处理已停止')
        setCurrentStep('已停止 - 清洗完成')
        setRunning(false)
        return
      }

      // 步骤2: LLM处理（优化内容）
      // 获取去重后的实际文件数
      let actualFilesToProcess = 0
      try {
        const processedFilesResponse = await axios.get(`${API_BASE_URL}/api/processed-files`)
        if (processedFilesResponse.data.success) {
          // 只统计当前选中批次的文件
          const allProcessedFiles = processedFilesResponse.data.files
          const selectedBatchFiles = allProcessedFiles.filter((file: string) => {
            const fileBatchId = file.split('/')[0] // 提取批次ID
            return fileBatchId === batchId
          })
          actualFilesToProcess = selectedBatchFiles.length
          addLog(`📋 检测到去重后的文件数: ${actualFilesToProcess} 个`)
        }
      } catch (error) {
        console.error('获取去重文件数失败，使用清洗返回的数量:', error)
        actualFilesToProcess = cleanResponse.data.processed_count || totalFiles
      }
      
      // 如果仍然是0，使用批次文件数作为fallback
      if (actualFilesToProcess === 0) {
        actualFilesToProcess = totalFiles
      }
      
      setCurrentStep(`LLM内容处理中 (0/${actualFilesToProcess})...`)
      addLog(`🤖 步骤2: 开始LLM内容处理 (去重后共${actualFilesToProcess}个文件)`)
      console.log('=== 步骤2: LLM处理 ===')
      console.log('请求URL:', `${API_BASE_URL}/api/auto/llm-process`)
      console.log('请求参数:', {
        api_key: config.llmApiKey.substring(0, 8) + '...',
        delay: 1,
        total_files: actualFilesToProcess,
        note: '如果清洗步骤被跳过，使用批次文件数'
      })
      
      // 实时监控LLM处理进度
      let lastProcessedCount = 0
      let llmCompleted = false
      let llmStartTime = Date.now()
      const recentProcessingTimes: number[] = [] // 记录最近几个文件的处理时间
      let lastUpdateTime = llmStartTime
      
      const progressInterval = setInterval(async () => {
        // 检查停止标志
        if (shouldStop) {
          clearInterval(progressInterval)
          return
        }
        
        try {
          // 获取当前已处理的文件数（只统计当前批次）
          const statsResponse = await axios.get(`${API_BASE_URL}/api/llm-processed-files?batch_id=${encodeURIComponent(batchId)}`)
          if (statsResponse.data.success) {
            const currentCount = statsResponse.data.count || statsResponse.data.files.length
            if (currentCount > lastProcessedCount) {
              // 记录这个文件的处理时间
              const now = Date.now()
              const timeSinceLastFile = (now - lastUpdateTime) / 1000
              recentProcessingTimes.push(timeSinceLastFile)
              
              // 只保留最近10个文件的处理时间（移动平均）
              if (recentProcessingTimes.length > 10) {
                recentProcessingTimes.shift()
              }
              
              lastProcessedCount = currentCount
              lastUpdateTime = now
              const processedCount = Math.min(currentCount, actualFilesToProcess)
              
              // 使用最近10个文件的平均时间来预估（更准确）
              const avgTimePerFile = recentProcessingTimes.length > 0
                ? recentProcessingTimes.reduce((a, b) => a + b, 0) / recentProcessingTimes.length
                : (now - llmStartTime) / 1000 / processedCount
              
              const remainingFiles = actualFilesToProcess - processedCount
              const estimatedRemainingSeconds = Math.ceil(avgTimePerFile * remainingFiles)
              const estimatedMinutes = Math.floor(estimatedRemainingSeconds / 60)
              const estimatedSeconds = estimatedRemainingSeconds % 60
              
              const timeEstimate = estimatedMinutes > 0 
                ? `预计剩余 ${estimatedMinutes}分${estimatedSeconds}秒`
                : `预计剩余 ${estimatedSeconds}秒`
              
              setCurrentStep(`LLM内容处理中 (${processedCount}/${actualFilesToProcess}) - ${timeEstimate}...`)
              
              // 更新进度条: 30% + (已处理/总数 * 35%)
              const llmProgress = actualFilesToProcess > 0 
                ? Math.floor((processedCount / actualFilesToProcess) * 35)
                : 0
              setProgress(30 + llmProgress)
              
              console.log(`LLM处理进度: ${processedCount}/${actualFilesToProcess} - ${timeEstimate}`)
              // 也显示在日志面板中
              addLog(`   📝 LLM处理进度: ${processedCount}/${actualFilesToProcess} - ${timeEstimate}`)
              
              // 检查是否完成
              if (processedCount >= actualFilesToProcess) {
                llmCompleted = true
                clearInterval(progressInterval)
              }
            }
          }
        } catch (error) {
          console.error('获取LLM处理进度失败:', error)
        }
      }, 1000) // 每1秒检查一次
      
      // 启动LLM处理（不等待响应，通过进度监控判断完成）
      const llmPromise = axios.post(getApiUrl('/api/auto/llm-process'), {
        api_key: config.llmApiKey,
        delay: 1,  // 每个请求间隔1秒
        batch_ids: [batchId],
        skip_if_exists: true,  // 启用智能跳过
        max_workers: 1  // 并发数：1（串行处理，避免API限流）
      }).catch(error => {
        // 如果请求失败，但进度监控显示已完成，则忽略错误
        console.warn('LLM请求返回错误，但可能已完成:', error.message)
        return { data: { success: false, error: error.message } }
      })
      
      // 等待LLM完成（完全依赖进度监控，不设时间限制）
      let llmResponse = null
      
      while (!llmCompleted) {
        // 每秒检查一次是否通过进度监控判断完成
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 检查停止标志
        if (shouldStop) {
          clearInterval(progressInterval)
          throw new Error('用户手动停止')
        }
        
        // 检查请求是否有响应
        const promiseStatus = await Promise.race([
          llmPromise.then(res => ({ resolved: true, response: res })),
          Promise.resolve({ resolved: false })
        ])
        
        if (promiseStatus.resolved) {
          llmResponse = promiseStatus.response
          break
        }
      }
      
      clearInterval(progressInterval) // 清除进度监控
      
      // 如果通过进度监控判断完成，但没有响应，则认为成功
      if (llmCompleted && !llmResponse) {
        console.log('✅ LLM处理通过进度监控确认完成')
        addLog(`✅ LLM处理完成: ${actualFilesToProcess} 个文件`)
        setProgress(65)
      } else if (llmResponse && llmResponse.data) {
        console.log('LLM响应:', llmResponse.data)
        console.log('LLM响应详情:', JSON.stringify(llmResponse.data, null, 2))
        
        if (llmResponse.data.success) {
          if (llmResponse.data.skipped) {
            addLog(`⏭️ LLM处理已完成，跳过此步骤`)
            if (llmResponse.data.skipped_batches && llmResponse.data.skipped_batches.length > 0) {
              addLog(`   跳过批次: ${llmResponse.data.skipped_batches.join(', ')}`)
            }
          } else {
          addLog(`✅ LLM处理完成: ${llmResponse.data.processed_count} 个文件`)
            if (llmResponse.data.failed_count > 0) {
              addLog(`   ⚠️ 失败: ${llmResponse.data.failed_count} 个文件`)
            }
          }
          console.log('✅ 步骤2成功: 处理了', llmResponse.data.processed_count, '个文件')
          if (llmResponse.data.failed_count > 0) {
            console.warn('⚠️ 失败:', llmResponse.data.failed_count, '个文件')
          }
          setProgress(65)
        } else {
          // 如果响应失败，但进度监控显示完成，仍然继续
          if (llmCompleted) {
            console.log('⚠️ LLM响应失败，但进度监控显示已完成，继续处理')
            addLog(`✅ LLM处理完成: ${lastProcessedCount} 个文件 (通过进度监控确认)`)
            setProgress(65)
          } else {
            console.error('❌ 步骤2失败:', llmResponse?.data?.error || 'Unknown error')
            throw new Error(llmResponse?.data?.error || 'LLM处理失败')
          }
        }
      } else {
        // llmResponse为null或没有data，使用进度监控的结果
        addLog(`✅ LLM处理通过进度监控确认完成`)
        console.log('✅ LLM处理完成（通过进度监控）')
        setProgress(65)
      }

      // 检查是否需要停止
      if (shouldStop) {
        addLog('🛑 处理已停止（在步骤2后）')
        addLog(`   ✅ 已完成LLM处理：${lastProcessedCount} 个文件`)
        console.log('🛑 处理已停止')
        setCurrentStep('已停止 - LLM处理部分完成')
        setRunning(false)
        return
      }

      // 步骤3: 上传到知识库
      setCurrentStep('上传到知识库中...')
      addLog('📚 步骤3: 开始上传到知识库')
      console.log('=== 步骤3: 知识库上传 ===')
      
      const kbUploadParams: any = {
        api_key: config.kbApiKey,
        knowledge_base_id: config.selectedKnowledgeBase,
        batch_size: 15,  // API限制每批最多20个，使用15确保稳定（自动分批）
        batch_ids: [batchId],
        skip_if_exists: true  // 启用智能跳过
      }
      
      // 根据分块模式选择参数      
      if (config.chunkMode === 'token') {
        kbUploadParams.chunk_token = config.chunkToken
      } else {
        kbUploadParams.chunk_separator = config.chunkSeparator
      }
      
      // 启动知识库上传进度监控
      let kbUploadCompleted = false
      const kbProgressInterval = setInterval(async () => {
        if (kbUploadCompleted || shouldStop) {
          clearInterval(kbProgressInterval)
          return
        }
        
        try {
          const progressResponse = await axios.get(getApiUrl('/api/kb-upload-progress'))
          if (progressResponse.data.success) {
            const { uploaded, total, is_uploading } = progressResponse.data
            
            if (total > 0) {
              // 动态计算进度（90%-100%）
              const kbProgress = 90 + (uploaded / total) * 10
              setProgress(Math.min(Math.round(kbProgress), 100))
              setCurrentStep(`Knowledge Base Upload: ${uploaded}/${total} files`)
              addLog(`📚 KB upload progress: ${uploaded}/${total} files`)
              console.log(`📚 KB upload progress: ${uploaded}/${total} files`)
              
              if (!is_uploading && uploaded === total) {
                kbUploadCompleted = true
                clearInterval(kbProgressInterval)
              }
            }
          }
        } catch (error) {
          console.error('Failed to get KB upload progress:', error)
        }
      }, 5000)  // 每5秒检查一次
      
      const kbResponse = await axios.post(getApiUrl('/api/auto/upload-kb'), kbUploadParams)
        .catch(error => {
          // 知识库上传可能因为时间过长而超时，但后台可能还在上传
          addLog('⚠️ Frontend connection timeout, backend still uploading...')
          addLog('   Please check progress monitoring above')
          return { data: { success: false, error: error.message, timeout: true } }
        })
      
      console.log('知识库上传响应:', kbResponse.data)
      
      // 如果是超时，等待进度监控确认完成
      if (kbResponse.data.timeout) {
        addLog('⏰ Upload timeout: Frontend connection lost')
        addLog('   💡 Waiting for backend to finish (monitoring progress)...')
        setCurrentStep('Uploading to KB (backend processing)...')
        
        // 等待上传完成（通过进度监控）
        const maxWaitTime = 30 * 60 * 1000  // 最多等待30分钟
        const startWaitTime = Date.now()
        
        while (!kbUploadCompleted && !shouldStop) {
          if (Date.now() - startWaitTime > maxWaitTime) {
            addLog('⚠️ KB upload still in progress after 30 minutes')
            addLog('   Please check the knowledge base later')
            break
          }
          
          await new Promise(resolve => setTimeout(resolve, 5000))
          
          // 检查进度
          try {
            const progressResponse = await axios.get(getApiUrl('/api/kb-upload-progress'))
            if (progressResponse.data.success) {
              const { uploaded, total, is_uploading } = progressResponse.data
              
              if (!is_uploading && uploaded === total && total > 0) {
                kbUploadCompleted = true
                addLog(`✅ KB upload confirmed complete: ${uploaded} files`)
                
                // 显示完成状态
                setProcessingResult({
                  cleanedCount: cleanResponse.data.processed_count,
                  duplicates: cleanResponse.data.duplicates || 0,
                  llmProcessed: actualFilesToProcess || 0,
                  llmFailed: 0,
                  kbUploaded: uploaded
                })
                
                setProgress(100)
                setCurrentStep('All complete!')
                addLog('🎉 Automated processing completed!')
                setCurrentView('completed')
                clearInterval(kbProgressInterval)
                return
              }
            }
          } catch (error) {
            console.error('Failed to check KB upload status:', error)
          }
        }
        
        // 如果被用户停止
        if (shouldStop) {
          clearInterval(kbProgressInterval)
          addLog('⚠️ User stopped the process')
          setCurrentStep('Stopped by user')
          setCurrentView('completed')
          return
        }
        
        // 如果超时了但还没完成
        clearInterval(kbProgressInterval)
        setProcessingResult({
          cleanedCount: cleanResponse.data.processed_count,
          duplicates: cleanResponse.data.duplicates || 0,
          llmProcessed: actualFilesToProcess || 0,
          llmFailed: 0,
          kbUploaded: 0  // 未知数量
        })
        
        setProgress(95)
        setCurrentStep('Upload in progress (backend processing)')
        addLog('   💡 Backend still uploading, please check later')
        setCurrentView('completed')
        return
      }
      
      // 清除进度监控
      clearInterval(kbProgressInterval)
      kbUploadCompleted = true
      
      if (kbResponse.data.success) {
        if (kbResponse.data.skipped) {
          addLog(`⏭️ KB upload already completed, skipped`)
          if (kbResponse.data.skipped_batches && kbResponse.data.skipped_batches.length > 0) {
            addLog(`   Skipped batches: ${kbResponse.data.skipped_batches.join(', ')}`)
          }
        } else {
          addLog(`✅ KB upload complete: ${kbResponse.data.uploaded_count} files`)
        }
        console.log('✅ Step 3 success: uploaded', kbResponse.data.uploaded_count, 'files')
        setProgress(100)
        setCurrentStep('All complete!')
        addLog('🎉 Automated processing complete!')
        console.log('🎉 === Automated processing complete ===')
        
        // 保存处理结果
        setProcessingResult({
          cleanedCount: cleanResponse.data.processed_count,
          duplicates: cleanResponse.data.duplicates || 0,
          llmProcessed: llmResponse?.data?.processed_count || actualFilesToProcess || 0,
          llmFailed: llmResponse?.data?.failed_count || 0,
          kbUploaded: kbResponse.data.uploaded_count
        })
        
        // 切换到完成页面（无自动跳转）
        setCurrentView('completed')
      } else {
        console.error('❌ Step 3 failed:', kbResponse.data.error)
        throw new Error(kbResponse.data.error || 'KB upload failed')
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
      throw error  // 重新抛出错误供主函数处理
    }
  }

  // 如果正在处理，强制显示配置页面（保持处理状态）
  const activeView = running ? 'config' : currentView

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
            onClick={() => onNavigate?.('batches')}
            disabled={running}
            style={{
              padding: '10px 20px',
              background: running ? '#cbd5e0' : '#e2e8f0',
              border: 'none',
              borderRadius: '8px',
              cursor: running ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              opacity: running ? 0.5 : 1
            }}
          >
            ← 返回批次管理
          </button>
        </div>

        {/* 批次选择部分 */}
        <div className="config-section" style={{ marginBottom: '30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '20px', margin: 0, display: 'flex', alignItems: 'center' }}>
              <HiFolderOpen style={{ fontSize: '24px', marginRight: '12px' }} />
              选择要处理的批次
            </h3>
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              cursor: 'pointer',
              padding: '8px 16px',
              background: hideCompletedBatches ? '#e6fffa' : '#f7fafc',
              border: `2px solid ${hideCompletedBatches ? '#38b2ac' : '#e2e8f0'}`,
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 600,
              color: hideCompletedBatches ? '#234e52' : '#4a5568',
              transition: 'all 0.3s'
            }}>
              <input
                type="checkbox"
                checked={hideCompletedBatches}
                onChange={(e) => setHideCompletedBatches(e.target.checked)}
                style={{ 
                  width: '16px', 
                  height: '16px',
                  cursor: 'pointer'
                }}
              />
              隐藏已完成批次
            </label>
          </div>
          
          {loadingBatches ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <BiLoaderAlt className="spinner" style={{ fontSize: '32px', color: '#667eea' }} />
              <p style={{ marginTop: '16px', color: '#718096' }}>加载批次列表中...</p>
            </div>
          ) : batches.length === 0 ? (
            <div style={{ 
              padding: '40px', 
              textAlign: 'center', 
              background: '#f7fafc', 
              borderRadius: '12px',
              border: '2px dashed #cbd5e0'
            }}>
              <p style={{ fontSize: '16px', color: '#718096', marginBottom: '8px' }}>暂无批次</p>
              <p style={{ fontSize: '14px', color: '#a0aec0' }}>请先在"批次管理"页面创建批次</p>
            </div>
          ) : (() => {
            // 根据 hideCompletedBatches 过滤批次
            const filteredBatches = hideCompletedBatches 
              ? batches.filter(batch => !batch.status?.uploaded_to_kb)
              : batches
            
            if (filteredBatches.length === 0) {
              return (
                <div style={{ 
                  padding: '40px', 
                  textAlign: 'center', 
                  background: '#f7fafc', 
                  borderRadius: '12px',
                  border: '2px dashed #cbd5e0'
                }}>
                  <p style={{ fontSize: '16px', color: '#718096', marginBottom: '8px' }}>
                    {hideCompletedBatches ? '所有批次都已完成处理' : '暂无批次'}
                  </p>
                  <p style={{ fontSize: '14px', color: '#a0aec0' }}>
                    {hideCompletedBatches ? '请取消筛选或创建新批次' : '请先在"批次管理"页面创建批次'}
                  </p>
                </div>
              )
            }
            
            return (
              <>
                <div style={{ 
                  background: '#e6fffa', 
                  border: '2px solid #81e6d9',
                  borderRadius: '10px',
                  padding: '16px 20px',
                  marginBottom: '20px'
                }}>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px',
                    fontSize: '15px',
                    fontWeight: 600,
                    color: '#234e52',
                    marginBottom: '8px'
                  }}>
                    <HiCheckCircle style={{ color: '#38b2ac', fontSize: '20px' }} />
                    <span>
                      {hideCompletedBatches 
                        ? `找到 ${filteredBatches.length} 个未完成批次` 
                        : `找到 ${batches.length} 个批次`}
                    </span>
                  </div>
                  <p style={{ fontSize: '14px', color: '#2c7a7b', margin: 0 }}>
                    {selectedBatchIds.length > 0 
                      ? `已选择 ${selectedBatchIds.length} 个批次进行处理` 
                      : '请选择要处理的批次（可多选）'}
                  </p>
                </div>

                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                  gap: '16px',
                  marginBottom: '20px'
                }}>
                  {filteredBatches.map((batch) => {
                    const isSelected = selectedBatchIds.includes(batch.batch_id)
                    return (
                    <div
                      key={batch.batch_id}
                      onClick={() => {
                        if (isSelected) {
                          setSelectedBatchIds(prev => prev.filter(id => id !== batch.batch_id))
                        } else {
                          setSelectedBatchIds(prev => [...prev, batch.batch_id])
                        }
                      }}
                      style={{
                        padding: '16px',
                        background: isSelected ? '#ebf8ff' : 'white',
                        border: `2px solid ${isSelected ? '#4299e1' : '#e2e8f0'}`,
                        borderRadius: '10px',
                        cursor: 'pointer',
                        transition: 'all 0.3s'
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.borderColor = '#cbd5e0'
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.borderColor = '#e2e8f0'
                        }
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px' }}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          style={{ 
                            marginRight: '12px', 
                            marginTop: '2px',
                            width: '18px',
                            height: '18px',
                            cursor: 'pointer'
                          }}
                        />
                        <div style={{ flex: 1 }}>
                          <div style={{ 
                            fontSize: '14px', 
                            fontWeight: 700, 
                            color: '#2d3748',
                            marginBottom: '6px',
                            wordBreak: 'break-word'
                          }}>
                            {batch.batch_id}
                          </div>
                          {batch.custom_label && (
                            <div style={{ 
                              fontSize: '13px', 
                              color: '#667eea', 
                              fontWeight: 600,
                              marginBottom: '6px'
                            }}>
                              🏷️ {batch.custom_label}
                            </div>
                          )}
                          <div style={{ 
                            fontSize: '12px', 
                            color: '#718096',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <HiClock />
                            {new Date(batch.upload_time).toLocaleString('zh-CN', {
                              month: '2-digit',
                              day: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        </div>
                      </div>
                      <div style={{ 
                        paddingTop: '12px',
                        borderTop: '1px solid #e2e8f0',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px'
                      }}>
                        <div style={{ fontSize: '13px', color: '#4a5568' }}>
                          📧 {batch.file_count} 个文件
                        </div>
                        {/* 处理进度 */}
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '6px',
                          fontSize: '12px',
                          fontWeight: 600
                        }}>
                          {batch.status?.uploaded_to_kb ? (
                            <span style={{ color: '#38a169', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              ✅ 已完成全部流程
                            </span>
                          ) : batch.status?.llm_processed ? (
                            <span style={{ color: '#3182ce', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              🤖 已完成LLM处理
                            </span>
                          ) : batch.status?.cleaned ? (
                            <span style={{ color: '#d69e2e', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              🧹 已完成去重
                            </span>
                          ) : (
                            <span style={{ color: '#718096', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              📤 已上传
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>

              <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
                <button
                  onClick={() => {
                    if (selectedBatchIds.length === filteredBatches.length) {
                      setSelectedBatchIds([])
                    } else {
                      setSelectedBatchIds(filteredBatches.map(b => b.batch_id))
                    }
                  }}
                  disabled={running}
                  style={{
                    padding: '10px 20px',
                    background: selectedBatchIds.length === filteredBatches.length ? '#fed7d7' : '#e2e8f0',
                    border: 'none',
                    borderRadius: '8px',
                    color: selectedBatchIds.length === filteredBatches.length ? '#c53030' : '#4a5568',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.3s'
                  }}
                >
                  {selectedBatchIds.length === filteredBatches.length ? '取消全选' : '全选'}
                </button>
                <button
                  onClick={() => setSelectedBatchIds([])}
                  disabled={running || selectedBatchIds.length === 0}
                  style={{
                    padding: '10px 20px',
                    background: selectedBatchIds.length === 0 ? '#f7fafc' : '#e2e8f0',
                    border: 'none',
                    borderRadius: '8px',
                    color: selectedBatchIds.length === 0 ? '#cbd5e0' : '#4a5568',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: selectedBatchIds.length === 0 ? 'not-allowed' : 'pointer'
                  }}
                >
                  清空
          </button>
              </div>
            </>
            )
          })()}
        </div>

        {/* LLM配置部分 */}
        <div className="config-section">
          <h3 
            style={{ 
              fontSize: '18px', 
              marginBottom: showLlmConfig ? '20px' : '0', 
              display: 'flex', 
              alignItems: 'center',
              cursor: 'pointer',
              padding: '12px 16px',
              background: '#f7fafc',
              borderRadius: '8px',
              transition: 'all 0.3s'
            }}
            onClick={() => setShowLlmConfig(!showLlmConfig)}
          >
            <HiCog style={{ fontSize: '22px', marginRight: '12px' }} />
            1️⃣ LLM邮件清洗配置
            <span style={{ 
              marginLeft: 'auto', 
              fontSize: '14px', 
              color: '#718096',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              {!showLlmConfig && envConfig && (
                <span style={{ fontSize: '12px', color: '#48bb78' }}>
                  ✅ 使用环境变量配置
                </span>
              )}
              <span>{showLlmConfig ? '▼' : '▶'}</span>
            </span>
          </h3>
        
        {showLlmConfig && (loadingConfig ? (
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
        ) : envConfigError ? (
          <div style={{
            padding: '24px',
            borderRadius: '16px',
            background: 'rgba(239, 68, 68, 0.1)',
            backdropFilter: 'blur(20px) saturate(180%)',
            WebkitBackdropFilter: 'blur(20px) saturate(180%)',
            border: '2px solid rgba(239, 68, 68, 0.3)',
            boxShadow: '0 8px 32px rgba(239, 68, 68, 0.15)'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
              <span style={{ fontSize: '32px' }}>❌</span>
              <div style={{ flex: 1 }}>
                <div style={{ 
                  fontSize: '18px', 
                  fontWeight: 700,
                  backgroundImage: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  marginBottom: '12px'
                }}>
                  无法加载环境配置
                </div>
                <div style={{
                  padding: '16px',
                  background: 'rgba(255, 255, 255, 0.8)',
                  borderRadius: '10px',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  marginBottom: '16px',
                  maxHeight: '300px',
                  overflowY: 'auto'
                }}>
                  <pre style={{ 
                    margin: 0,
                    fontSize: '13px',
                    color: '#991b1b',
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word'
                  }}>
                    {envConfigError}
                  </pre>
                </div>
                <div style={{ 
                  fontSize: '14px', 
                  color: '#991b1b',
                  background: 'rgba(254, 226, 226, 0.5)',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid rgba(239, 68, 68, 0.2)'
                }}>
                  <div style={{ fontWeight: 600, marginBottom: '8px' }}>💡 解决步骤：</div>
                  <ol style={{ margin: 0, paddingLeft: '20px' }}>
                    <li>确认 .env 文件在项目根目录</li>
                    <li>检查文件编码为UTF-8（无BOM）</li>
                    <li>确认后端服务在项目根目录启动</li>
                    <li>查看后端日志: logs/api_server.log</li>
                  </ol>
                  <div style={{ marginTop: '12px', fontSize: '13px' }}>
                    📖 详细排查指南请查看: <strong>Windows部署故障排除指南.md</strong>
                  </div>
                </div>
                <button
                  onClick={() => fetchEnvConfig()}
                  style={{
                    marginTop: '16px',
                    padding: '10px 20px',
                    background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(239, 68, 68, 0.3)',
                    transition: 'all 0.3s'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                  onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                >
                  🔄 重新加载配置
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="error-card">
            <p>❌ 无法加载环境配置</p>
            <p style={{ fontSize: '14px', color: '#718096', marginTop: '8px' }}>
              请确保 .env 文件存在并包含正确的配置
            </p>
          </div>
        ))}
      </div>

      {/* 知识库配置部分 */}
      <div className="config-section" style={{ marginTop: '20px' }}>
        <h3 
          style={{ 
            fontSize: '18px', 
            marginBottom: showKbConfig ? '20px' : '0', 
            display: 'flex', 
            alignItems: 'center',
            cursor: 'pointer',
            padding: '12px 16px',
            background: '#f7fafc',
            borderRadius: '8px',
            transition: 'all 0.3s'
          }}
          onClick={() => setShowKbConfig(!showKbConfig)}
        >
          <HiCog style={{ fontSize: '22px', marginRight: '12px' }} />
          2️⃣ 知识库上传配置
          <span style={{ 
            marginLeft: 'auto', 
            fontSize: '14px', 
            color: '#718096',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            {!showKbConfig && envConfig && (
              <span style={{ fontSize: '12px', color: '#48bb78' }}>
                ✅ 使用环境变量配置
              </span>
            )}
            <span>{showKbConfig ? '▼' : '▶'}</span>
          </span>
        </h3>
        
        {showKbConfig && (loadingConfig ? (
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
        ))}
      </div>

      {/* iOS风格毛玻璃知识库选择区域 */}
      {!showKbConfig && envConfig && envConfig.kb_api_keys && knowledgeBases.length > 0 && (
        <div className="config-section" style={{ 
          marginTop: '20px',
          position: 'relative',
          borderRadius: '16px',
          padding: '28px',
          background: 'rgba(255, 255, 255, 0.7)',
          backdropFilter: 'blur(20px) saturate(180%)',
          WebkitBackdropFilter: 'blur(20px) saturate(180%)',
          border: '1px solid rgba(255, 255, 255, 0.5)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.8)',
          overflow: 'hidden'
        }}>
          {/* 背景装饰 */}
          <div style={{
            position: 'absolute',
            top: '-50%',
            right: '-10%',
            width: '200px',
            height: '200px',
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%)',
            borderRadius: '50%',
            filter: 'blur(40px)',
            pointerEvents: 'none'
          }} />
          <div style={{
            position: 'absolute',
            bottom: '-30%',
            left: '-5%',
            width: '150px',
            height: '150px',
            background: 'linear-gradient(135deg, rgba(118, 75, 162, 0.15) 0%, rgba(102, 126, 234, 0.15) 100%)',
            borderRadius: '50%',
            filter: 'blur(40px)',
            pointerEvents: 'none'
          }} />
          
          <div style={{ position: 'relative', zIndex: 1 }}>
            <label style={{ 
              color: '#1a202c',
              fontSize: '18px',
              fontWeight: 700,
              marginBottom: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <span style={{
                backgroundImage: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                fontSize: '20px'
              }}>
                ⭐
              </span>
              <span style={{
                backgroundImage: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                选择目标知识库
              </span>
              <span style={{ color: '#e53e3e', fontSize: '16px' }}>*</span>
            </label>
            <select
              value={config.selectedKnowledgeBase}
              onChange={(e) => setConfig(prev => ({
                ...prev,
                selectedKnowledgeBase: e.target.value
              }))}
              disabled={running}
              style={{
                width: '100%',
                padding: '16px 18px',
                border: '2px solid rgba(102, 126, 234, 0.2)',
                borderRadius: '12px',
                fontSize: '16px',
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                cursor: running ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                color: '#2d3748',
                boxShadow: '0 4px 16px rgba(102, 126, 234, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.8)',
                transition: 'all 0.3s ease',
                outline: 'none'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = 'rgba(102, 126, 234, 0.6)'
                e.target.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.8)'
              }}
              onBlur={(e) => {
                e.target.style.borderColor = 'rgba(102, 126, 234, 0.2)'
                e.target.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.8)'
              }}
            >
              {knowledgeBases.map((kb: any) => (
                <option key={kb.id} value={kb.id}>
                  {kb.name} ({kb.doc_count} 个文档)
                </option>
              ))}
            </select>
            <p style={{ 
              color: '#718096', 
              fontSize: '13px', 
              marginTop: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontWeight: 500
            }}>
              <span>💡</span>
              <span>清洗后的邮件将上传到此知识库</span>
            </p>
          </div>
        </div>
      )}

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
          
          {/* 预计剩余时间 - iOS毛玻璃风格 */}
          {estimatedTime > 0 && (
            <div style={{
              marginTop: '20px',
              padding: '20px 24px',
              borderRadius: '16px',
              background: remainingTime <= 0 
                ? 'rgba(72, 187, 120, 0.1)' 
                : 'rgba(102, 126, 234, 0.1)',
              backdropFilter: 'blur(20px) saturate(180%)',
              WebkitBackdropFilter: 'blur(20px) saturate(180%)',
              border: remainingTime <= 0 
                ? '2px solid rgba(72, 187, 120, 0.3)' 
                : '2px solid rgba(102, 126, 234, 0.3)',
              boxShadow: remainingTime <= 0
                ? '0 8px 32px rgba(72, 187, 120, 0.15)'
                : '0 8px 32px rgba(102, 126, 234, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              transition: 'all 0.5s ease'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <HiClock style={{ 
                  fontSize: '24px', 
                  color: remainingTime <= 0 ? '#38a169' : '#667eea'
                }} />
                <div>
                  <div style={{ 
                    fontSize: '13px', 
                    color: '#718096',
                    fontWeight: 500,
                    marginBottom: '4px'
                  }}>
                    {remainingTime <= 0 ? '处理即将完成' : '预计剩余时间'}
                  </div>
                  <div style={{ 
                    fontSize: '24px', 
                    fontWeight: 700,
                    backgroundImage: remainingTime <= 0
                      ? 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)'
                      : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                  }}>
                    {formatTime(remainingTime)}
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#a0aec0',
                  marginBottom: '4px'
                }}>
                  总文件数
                </div>
                <div style={{ 
                  fontSize: '20px', 
                  fontWeight: 700,
                  color: '#4a5568'
                }}>
                  {totalFilesToProcess}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {logs.length > 0 && (
        <div className="logs-section">
          <h3 style={{ fontSize: '16px', marginBottom: '10px' }}>📋 执行日志</h3>
          
          {/* 全局重复邮件提示 - iOS毛玻璃风格 */}
          {globalDuplicates.length > 0 && (
            <div style={{
              marginBottom: '16px',
              padding: '20px 24px',
              borderRadius: '16px',
              background: 'rgba(251, 191, 36, 0.1)',
              backdropFilter: 'blur(20px) saturate(180%)',
              WebkitBackdropFilter: 'blur(20px) saturate(180%)',
              border: '2px solid rgba(251, 191, 36, 0.3)',
              boxShadow: '0 8px 32px rgba(251, 191, 36, 0.15)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                <span style={{ fontSize: '24px' }}>🔄</span>
                <div>
                  <div style={{ 
                    fontSize: '16px', 
                    fontWeight: 700,
                    backgroundImage: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    marginBottom: '4px'
                  }}>
                    检测到跨批次重复邮件
                  </div>
                  <div style={{ fontSize: '13px', color: '#92400e' }}>
                    共 {globalDuplicates.length} 个邮件在其他批次中已处理，已自动跳过
                  </div>
                </div>
              </div>
              <div style={{ 
                maxHeight: '200px', 
                overflowY: 'auto',
                padding: '12px',
                background: 'rgba(255, 255, 255, 0.6)',
                borderRadius: '10px',
                border: '1px solid rgba(251, 191, 36, 0.2)'
              }}>
                {globalDuplicates.map((dup, index) => (
                  <div key={index} style={{
                    padding: '10px 12px',
                    marginBottom: '8px',
                    background: 'rgba(255, 255, 255, 0.8)',
                    borderRadius: '8px',
                    fontSize: '13px',
                    color: '#78350f',
                    border: '1px solid rgba(251, 191, 36, 0.2)'
                  }}>
                    <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                      📧 {dup.file_name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#92400e' }}>
                      已在批次 <span style={{ fontWeight: 600 }}>{dup.previous_batch}</span> 中处理
                      （{new Date(dup.previous_time).toLocaleString('zh-CN')}）
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
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
                  // 重置状态，返回配置页面准备处理更多邮件
                  setCurrentView('config')
                  setProgress(0)
                  setLogs([])
                  setCurrentStep('')
                  setProcessingResult(null)
                  setSelectedBatchIds([])  // 清空选中的批次
                  fetchBatches()  // 刷新批次列表
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

