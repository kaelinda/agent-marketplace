/**
 * Markdown → 微信兼容 HTML 转换器
 * 
 * 支持多主题定制（Reader / CodeFine / Ocean / ChatEx）
 * 设计参考: markdown-theme-hub
 */

import { marked } from 'marked'
import fs from 'fs'
import path from 'path'
import { uploadImage } from './wechatApi.js'
import { getTheme } from './themes.js'

// 配置 marked
marked.setOptions({
  gfm: true,
  breaks: true
})

/**
 * 将 Markdown 转换为微信兼容 HTML
 * 
 * @param {string} markdown - Markdown 文本
 * @param {Object} options - 配置选项
 * @param {string} options.theme - 主题名称（reader/codefine/ocean/chatex）
 * @param {Function} options.onImageUpload - 图片上传回调
 */
export async function markdownToHtml(markdown, options = {}) {
  const { theme = 'reader', onImageUpload } = options

  // 获取主题配置
  const t = getTheme(theme)

  // 1. 解析 Markdown
  let html = await marked.parse(markdown)

  // 2. 处理图片
  html = await processImages(html, onImageUpload)

  // 3. 应用主题样式
  html = applyThemeStyles(html, t)

  // 4. 清理不支持的标签
  html = cleanUnsupportedTags(html)

  return html
}

/**
 * 处理 HTML 中的图片
 */
async function processImages(html, onImageUpload) {
  const imgRegex = /<img\s+src=["']([^"']+)["'][^>]*>/gi
  const matches = [...html.matchAll(imgRegex)]

  for (const match of matches) {
    const fullMatch = match[0]
    const src = match[1]

    // 跳过外链图片
    if (src.startsWith('http://') || src.startsWith('https://')) {
      console.warn('⚠️ 跳过外链图片（微信公众号不支持）:', src.substring(0, 50))
      continue
    }

    // 上传本地图片
    if (onImageUpload) {
      try {
        const imgPath = src.startsWith('/') 
          ? src 
          : path.resolve(process.cwd(), src)
        
        const { url } = await onImageUpload(imgPath)
        const newImg = fullMatch.replace(src, url)
        html = html.replace(fullMatch, newImg)
      } catch (err) {
        console.warn(`⚠️ 图片上传失败: ${src}`, err.message)
      }
    }
  }

  return html
}

/**
 * 应用主题内联样式
 */
function applyThemeStyles(html, t) {
  // ==================== 代码块 ====================
  html = html.replace(
    /<pre>\s*<code>/gi,
    `<pre style="`
    + `background-color:${t.colors.codeBg};`
    + `border-radius:8px;`
    + `padding:16px;`
    + `overflow-x:auto;`
    + `margin:24px 0;`
    + `border:1px solid ${t.colors.border};`
    + `font-family:${t.fonts.code};`
    + `font-size:${t.sizes.code};`
    + `line-height:1.6;`
    + `"><code style="`
    + `font-family:${t.fonts.code};`
    + `font-size:${t.sizes.code};`
    + `background:none;`
    + `padding:0;`
    + `border-radius:0;`
    + `color:${t.colors.body};`
    + `">`
  )

  // ==================== 行内代码 ====================
  html = html.replace(
    /<code>(?!<\/code>)/gi,
    `<code style="`
    + `font-family:${t.fonts.code};`
    + `font-size:${t.sizes.code};`
    + `background-color:${t.colors.codeBg};`
    + `color:${t.colors.code};`
    + `padding:2px 6px;`
    + `border-radius:4px;`
    + `">`
  )

  // ==================== 引用块 ====================
  html = html.replace(
    /<blockquote>/gi,
    `<blockquote style="`
    + `border-left:4px solid ${t.colors.link};`
    + `background-color:${t.colors.blockquoteBg};`
    + `margin:24px 0;`
    + `padding:12px 20px;`
    + `color:${t.colors.secondary};`
    + `font-style:italic;`
    + `border-radius:0 8px 8px 0;`
    + `">`
  )

  // ==================== 表格 ====================
  html = html.replace(
    /<table>/gi,
    `<table style="`
    + `border-collapse:collapse;`
    + `width:100%;`
    + `margin:24px 0;`
    + `font-size:15px;`
    + `border-radius:8px;`
    + `overflow:hidden;`
    + `border:1px solid ${t.colors.tableBorder};`
    + `">`
  )

  html = html.replace(
    /<thead>/gi,
    `<thead style="`
    + `background-color:${t.colors.tableHeader};`
    + `">`
  )

  html = html.replace(
    /<th(?:\s|>)/gi,
    `<th style="`
    + `border:1px solid ${t.colors.tableBorder};`
    + `padding:10px 14px;`
    + `text-align:left;`
    + `font-weight:600;`
    + `color:${t.colors.heading};`
    + `font-family:${t.fonts.heading};`
    + `">`
  )

  html = html.replace(
    /<td(?:\s|>)/gi,
    `<td style="`
    + `border:1px solid ${t.colors.tableBorder};`
    + `padding:10px 14px;`
    + `color:${t.colors.body};`
    + `line-height:1.8;`
    + `">`
  )

  // ==================== 链接 ====================
  html = html.replace(
    /<a\s/gi,
    `<a style="`
    + `color:${t.colors.link};`
    + `text-decoration:none;`
    + `border-bottom:1px solid ${t.colors.link};`
    + `padding-bottom:1px;`
    + `" `
  )

  // ==================== 标题 ====================
  // H1
  html = html.replace(
    /<h1>/gi,
    `<h1 style="`
    + `font-family:${t.fonts.heading};`
    + `font-size:${t.sizes.h1};`
    + `font-weight:600;`
    + `color:${t.colors.heading};`
    + `margin:24px 0 16px;`
    + `padding-bottom:12px;`
    + `border-bottom:2px solid ${t.colors.border};`
    + `line-height:1.4;`
    + `">`
  )

  // H2
  html = html.replace(
    /<h2>/gi,
    `<h2 style="`
    + `font-family:${t.fonts.heading};`
    + `font-size:${t.sizes.h2};`
    + `font-weight:600;`
    + `color:${t.colors.heading};`
    + `margin:24px 0 12px;`
    + `padding-bottom:8px;`
    + `border-bottom:1px solid ${t.colors.border};`
    + `line-height:1.4;`
    + `">`
  )

  // H3
  html = html.replace(
    /<h3>/gi,
    `<h3 style="`
    + `font-family:${t.fonts.heading};`
    + `font-size:${t.sizes.h3};`
    + `font-weight:600;`
    + `color:${t.colors.heading};`
    + `margin:20px 0 10px;`
    + `line-height:1.4;`
    + `">`
  )

  // H4-H6
  html = html.replace(
    /<h([456])>/gi,
    `<h$1 style="`
    + `font-family:${t.fonts.heading};`
    + `font-size:16px;`
    + `font-weight:600;`
    + `color:${t.colors.heading};`
    + `margin:16px 0 8px;`
    + `line-height:1.4;`
    + `">`
  )

  // ==================== 图片 ====================
  html = html.replace(
    /<img\s+/gi,
    `<img style="`
    + `max-width:100%;`
    + `height:auto;`
    + `border-radius:8px;`
    + `margin:16px auto;`
    + `display:block;`
    + `box-shadow:0 2px 8px rgba(0,0,0,0.08);`
    + `" `
  )

  // ==================== 列表 ====================
  html = html.replace(
    /<ul>/gi,
    `<ul style="`
    + `margin:8px 0;`
    + `padding-left:20px;`
    + `color:${t.colors.body};`
    + `line-height:1.6;`
    + `">`
  )

  html = html.replace(
    /<ol>/gi,
    `<ol style="`
    + `margin:8px 0;`
    + `padding-left:20px;`
    + `color:${t.colors.body};`
    + `line-height:1.6;`
    + `">`
  )

  html = html.replace(
    /<li>/gi,
    `<li style="`
    + `margin:0;`
    + `padding:2px 0;`
    + `line-height:1.6;`
    + `">`
  )

  // ==================== 段落 ====================
  html = html.replace(
    /<p>/gi,
    `<p style="`
    + `margin:12px 0;`
    + `font-size:${t.sizes.body};`
    + `line-height:1.8;`
    + `color:${t.colors.body};`
    + `font-family:${t.fonts.body};`
    + `">`
  )

  // ==================== 水平线 ====================
  html = html.replace(
    /<hr>/gi,
    `<hr style="`
    + `border:none;`
    + `border-top:1px solid ${t.colors.border};`
    + `margin:24px 0;`
    + `">`
  )

  // ==================== 强调 ====================
  html = html.replace(
    /<strong>/gi,
    `<strong style="`
    + `font-weight:600;`
    + `color:${t.colors.heading};`
    + `">`
  )

  html = html.replace(
    /<em>/gi,
    `<em style="`
    + `font-style:italic;`
    + `">`
  )

  return html
}

/**
 * 清理不支持的 HTML 标签和属性
 */
function cleanUnsupportedTags(html) {
  html = html.replace(/\s*class=["'][^"']*["']/gi, '')
  html = html.replace(/\s*id=["'][^"']*["']/gi, '')
  html = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
  html = html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')

  const disallowedTags = ['iframe', 'form', 'input', 'button', 'select', 'textarea']
  for (const tag of disallowedTags) {
    const regex = new RegExp(`<${tag}[^>]*>[\\s\\S]*?<\\/${tag}>`, 'gi')
    html = html.replace(regex, '')
    const regex2 = new RegExp(`<${tag}[^>]*/?>`, 'gi')
    html = html.replace(regex2, '')
  }

  return html
}

/**
 * 从文件读取 Markdown 并转换
 */
export async function convertFile(markdownPath, options = {}) {
  if (!fs.existsSync(markdownPath)) {
    throw new Error(`Markdown 文件不存在: ${markdownPath}`)
  }

  const markdown = fs.readFileSync(markdownPath, 'utf-8')
  return markdownToHtml(markdown, options)
}
