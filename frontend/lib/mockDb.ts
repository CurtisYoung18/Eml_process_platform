// Mock数据库 - 用户数据
export interface User {
  id: string
  username: string
  password: string
  role: 'admin'
}

// Mock用户数据库
export const mockUsers: User[] = [
  {
    id: 'admin-001',
    username: 'admin',
    password: 'admin123', // 实际应用中应该使用加密密码
    role: 'admin'
  }
]

// 验证用户
export function verifyUser(username: string, password: string): User | null {
  const user = mockUsers.find(
    u => u.username === username && u.password === password
  )
  return user || null
}

// 检查是否已登录
export function checkAuth(): boolean {
  if (typeof window === 'undefined') return false
  
  // 先检查 localStorage（记住我），再检查 sessionStorage
  const localToken = localStorage.getItem('admin_token')
  const sessionToken = sessionStorage.getItem('admin_token')
  
  return localToken === 'authenticated' || sessionToken === 'authenticated'
}

// 登录
export function login(username: string, password: string, rememberMe: boolean = false): boolean {
  const user = verifyUser(username, password)
  if (user) {
    const storage = rememberMe ? localStorage : sessionStorage
    storage.setItem('admin_token', 'authenticated')
    storage.setItem('admin_user', JSON.stringify(user))
    
    // 记录是否使用了记住我功能
    if (rememberMe) {
      localStorage.setItem('rememberMe', 'true')
    } else {
      localStorage.removeItem('rememberMe')
    }
    return true
  }
  return false
}

// 登出
export function logout(): void {
  // 清除所有存储的登录信息
  sessionStorage.removeItem('admin_token')
  sessionStorage.removeItem('admin_user')
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_user')
  localStorage.removeItem('rememberMe')
}

// 获取当前用户
export function getCurrentUser(): User | null {
  if (typeof window === 'undefined') return null
  
  // 先检查 localStorage，再检查 sessionStorage
  const localUserStr = localStorage.getItem('admin_user')
  const sessionUserStr = sessionStorage.getItem('admin_user')
  const userStr = localUserStr || sessionUserStr
  
  if (!userStr) return null
  try {
    return JSON.parse(userStr)
  } catch {
    return null
  }
}

// 检查是否记住了登录
export function isRemembered(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem('rememberMe') === 'true'
}
