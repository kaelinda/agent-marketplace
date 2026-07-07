/**
 * 微信公众号文章发布器
 * 
 * 支持多主题定制（Reader / CodeFine / Ocean / ChatEx）
 */

import fs from 'fs'
import path from 'path'
import { markdownToHtml } from './markdownToHtml.js'
import { generateCoverImage } from './coverGenerator.js'
import { uploadImage, uploadThumbImage, addDraft, loadEnv, checkEnv } from './wechatApi.js'

/**
 * 发布文章到草稿箱
 * 
 * @param {Object} params - 发布参数
 * @param {string} params.title - 文章标题
 * @param {string} params.markdown - Markdown 文件路径
 * @param {string} params.content - Markdown 内容（与 markdown 二选一）
 * @param {string} params.author - 作者
 * @param {string} params.cover - 封面图路径
 * @param {string} params.theme - 主题名称（reader/codefine/ocean/chatex）
 * @returns {Promise<Object>} 发布结果
 */
export async function publishArticle(params) {
  const { 
    title, 
    markdown, 
    content, 
    author = 'Unknown', 
    cover,
    theme = 'reader'
  } = params

  // 1. 读取 Markdown
  if (!markdown && !content) {
    throw new Error('必须提供 --markdown 或 --content')
  }

  let markdownText
  if (markdown) {
    if (!fs.existsSync(markdown)) {
      throw new Error(`Markdown 文件不存在: ${markdown}`)
    }
    markdownText = fs.readFileSync(markdown, 'utf-8')
  } else {
    markdownText = content
  }

  // 2. 上传图片到微信 CDN
  const uploadedImages = new Map()
  
  const onImageUpload = async (localPath) => {
    // 避免重复上传
    if (uploadedImages.has(localPath)) {
      return { url: uploadedImages.get(localPath) }
    }
    
    try {
      const result = await uploadImage(localPath)
      uploadedImages.set(localPath, result.url)
      return result
    } catch (err) {
      console.warn(`⚠️ 图片上传失败: ${localPath}`)
      return { url: localPath }
    }
  }

  // 3. 转换为 HTML（带主题）
  console.log(`🎨 使用主题: ${theme}`)
  const html = await markdownToHtml(markdownText, { 
    theme,
    onImageUpload 
  })

  // 4. 验证内容大小（微信限制 2MB）
  const contentLength = Buffer.byteLength(html, 'utf-8')
  if (contentLength > 2 * 1024 * 1024) {
    throw new Error(`文章内容过大: ${(contentLength / 1024 / 1024).toFixed(2)}MB（最大 2MB）`)
  }

  // 5. 生成/上传封面图
  let coverPath = cover
  if (!coverPath) {
    console.log('🎨 未提供封面图，正在自动生成...')
    const generated = await generateCoverImage({ title, markdownText })
    coverPath = generated.path
    console.log(`✅ 封面图生成成功: ${coverPath}`)
  }

  let thumbMediaId = '0'
  if (coverPath) {
    if (!fs.existsSync(coverPath)) {
      throw new Error(`封面图不存在: ${coverPath}`)
    }
    const thumbResult = await uploadThumbImage(coverPath)
    thumbMediaId = thumbResult.mediaId || '0'
    console.log(`✅ 封面上传成功: ${thumbMediaId}`)
  }

  // 6. 构建文章对象
  const article = {
    title,
    author,
    content: html,
    content_source_url: undefined,

    digest: markdownText.substring(0, 54), // 摘要取前54字
    need_open_comment: 1, // 打开评论
    only_fans_can_comment: 0, // 所有人都可评论
    thumb_media_id: thumbMediaId,
  }

  // 7. 发布到草稿箱
  console.log(`📤 正在发布到草稿箱...`)
  const result = await addDraft([article])

  return {
    success: true,
    mediaId: result.mediaId,
    title,
    author,
    theme,
    contentLength,
    imagesUploaded: uploadedImages.size,
  }
}
