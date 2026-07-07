/**
 * 微信公众平台 API 客户端
 * 
 * 核心接口:
 * - getAccessToken() - 获取调用凭证
 * - uploadImage(filePath) - 上传图片获取 CDN URL
 * - uploadThumbImage(filePath) - 上传封面图获取 thumb_media_id
 * - addDraft(articles) - 新增草稿
 */

import fetch from 'node-fetch'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// 加载环境变量
function loadEnv() {
  const envPath = path.join(__dirname, '..', '.env')
  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, 'utf-8')
    content.split('\n').forEach(line => {
      const [key, ...vals] = line.split('=')
      if (key && vals.length) {
        process.env[key.trim()] = vals.join('=').trim()
      }
    })
  }
}
loadEnv()

const APP_ID = () => process.env.WECHAT_APP_ID
const APP_SECRET = () => process.env.WECHAT_APP_SECRET
const API_BASE = 'https://api.weixin.qq.com'

// Token 缓存
let tokenCache = {
  token: null,
  expiresAt: 0
}

/**
 * 检查环境变量
 */
function checkEnv() {
  if (!process.env.WECHAT_APP_ID || !process.env.WECHAT_APP_SECRET) {
    throw new Error('缺少环境变量: WECHAT_APP_ID 和 WECHAT_APP_SECRET')
  }
}

/**
 * 获取 access_token（带缓存）
 */
export { checkEnv, loadEnv }
export async function getAccessToken() {
  checkEnv()

  // 检查缓存（提前 5 分钟过期）
  if (tokenCache.token && Date.now() < tokenCache.expiresAt - 300000) {
    return tokenCache.token
  }

  const appId = process.env.WECHAT_APP_ID
  const appSecret = process.env.WECHAT_APP_SECRET
  const url = `${API_BASE}/cgi-bin/token?grant_type=client_credential&appid=${appId}&secret=${appSecret}`
  
  const res = await fetch(url)
  const data = await res.json()

  if (data.errcode) {
    throw new Error(`获取 access_token 失败: ${data.errcode} - ${data.errmsg}`)
  }

  // 缓存 token
  tokenCache = {
    token: data.access_token,
    expiresAt: Date.now() + (data.expires_in * 1000)
  }

  return data.access_token
}

/**
 * 上传图片到微信 CDN
 * 返回可用于图文消息中的图片 URL
 */
export async function uploadImage(filePath) {
  const token = await getAccessToken()
  
  if (!fs.existsSync(filePath)) {
    throw new Error(`图片文件不存在: ${filePath}`)
  }

  const fileBuffer = fs.readFileSync(filePath)
  const fileName = path.basename(filePath)
  const mimeType = getMimeType(fileName)

  // 使用 form-data 上传
  const boundary = `----WechatBoundary${Date.now()}`
  const body = Buffer.concat([
    Buffer.from(`--${boundary}\r\n`),
    Buffer.from(`Content-Disposition: form-data; name="media"; filename="${fileName}"\r\n`),
    Buffer.from(`Content-Type: ${mimeType}\r\n\r\n`),
    fileBuffer,
    Buffer.from(`\r\n--${boundary}--\r\n`)
  ])

  const url = `${API_BASE}/cgi-bin/media/uploadimg?access_token=${token}&type=image`
  
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': `multipart/form-data; boundary=${boundary}`
    },
    body
  })

  const data = await res.json()

  if (data.errcode) {
    throw new Error(`图片上传失败: ${data.errcode} - ${data.errmsg}`)
  }

  return {
    url: data.url,
    mediaId: data.media_id
  }
}

/**
 * 上传封面图（thumb media）
 * 返回 thumb_media_id（用于图文消息封面）
 */
export async function uploadThumbImage(filePath) {
  const token = await getAccessToken()
  
  if (!fs.existsSync(filePath)) {
    throw new Error(`封面图文件不存在: ${filePath}`)
  }

  const fileBuffer = fs.readFileSync(filePath)
  const fileName = path.basename(filePath)
  const mimeType = getMimeType(fileName)

  const boundary = `----WechatBoundary${Date.now()}`
  const body = Buffer.concat([
    Buffer.from(`--${boundary}\r\n`),
    Buffer.from(`Content-Disposition: form-data; name="media"; filename="${fileName}"\r\n`),
    Buffer.from(`Content-Type: ${mimeType}\r\n\r\n`),
    fileBuffer,
    Buffer.from(`\r\n--${boundary}--\r\n`)
  ])

  // 封面图使用永久素材接口（草稿接口需要永久素材的 media_id）
  const url = `${API_BASE}/cgi-bin/material/add_material?access_token=${token}&type=thumb`
  
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': `multipart/form-data; boundary=${boundary}`
    },
    body
  })

  const data = await res.json()

  if (data.errcode) {
    throw new Error(`封面上传失败: ${data.errcode} - ${data.errmsg}`)
  }

  return {
    mediaId: data.thumb_media_id || data.media_id,
    // thumb 返回 thumb_media_id, 其他类型返回 media_id
  }
}

/**
 * 新增草稿
 * @param {Array} articles 图文素材数组
 */
export async function addDraft(articles) {
  const token = await getAccessToken()

  const url = `${API_BASE}/cgi-bin/draft/add?access_token=${token}`
  
  const body = JSON.stringify({ articles: articles.map(a => {
    const filtered = {}
    for (const [k, v] of Object.entries(a)) {
      if (v !== undefined) filtered[k] = v
    }
    return filtered
  }) })
  console.log('📤 请求体:', body.substring(0, 1000))
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body
  })

  const data = await res.json()

  if (data.errcode) {
    throw new Error(`创建草稿失败: ${data.errcode} - ${data.errmsg}`)
  }

  return {
    mediaId: data.media_id
  }
}

/**
 * 测试连接
 */
export async function testConnection() {
  try {
    checkEnv()
    const token = await getAccessToken()
    return {
      success: true,
      token,
      appId: APP_ID
    }
  } catch (err) {
    return {
      success: false,
      error: err.message
    }
  }
}

/**
 * 获取文件 MIME 类型
 */
function getMimeType(filename) {
  const ext = path.extname(filename).toLowerCase()
  const mimeTypes = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.bmp': 'image/bmp'
  }
  return mimeTypes[ext] || 'application/octet-stream'
}
