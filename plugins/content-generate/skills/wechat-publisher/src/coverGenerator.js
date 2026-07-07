import fs from 'fs'
import path from 'path'
import os from 'os'
import { fileURLToPath } from 'url'
import OpenAI from 'openai'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

function ensureOpenAIKey() {
  const key = process.env.OPENAI_API_KEY
  if (!key) {
    throw new Error('缺少环境变量: OPENAI_API_KEY')
  }
  return key
}

function buildPrompt({ title, markdownText }) {
  const seed = (markdownText || title || '').slice(0, 120).replace(/\s+/g, ' ').trim()
  return [
    'Create a clean, modern WeChat public account cover illustration.',
    'Style: minimalist, editorial, polished, high readability, no text, no logos, no watermark.',
    'Aspect ratio: 16:9 landscape.',
    'Topic:',
    seed || title || 'AI knowledge and productivity'
  ].join(' ')
}

export async function generateCoverImage({ title, markdownText }) {
  ensureOpenAIKey()
  const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })
  const prompt = buildPrompt({ title, markdownText })

  const result = await client.images.generate({
    model: 'gpt-image-1',
    prompt,
    size: '1536x1024',
  })

  const data = result.data?.[0]
  if (!data) {
    throw new Error('封面图生成失败：没有返回图片数据')
  }

  const outDir = path.join(os.tmpdir(), 'wechat-publisher-covers')
  fs.mkdirSync(outDir, { recursive: true })

  const fileName = `cover-${Date.now()}.png`
  const outPath = path.join(outDir, fileName)

  if (data.b64_json) {
    fs.writeFileSync(outPath, Buffer.from(data.b64_json, 'base64'))
    return { path: outPath, prompt }
  }

  if (data.url) {
    const res = await fetch(data.url)
    if (!res.ok) {
      throw new Error(`封面图下载失败: ${res.status}`)
    }
    const arrayBuffer = await res.arrayBuffer()
    fs.writeFileSync(outPath, Buffer.from(arrayBuffer))
    return { path: outPath, prompt }
  }

  throw new Error('封面图生成失败：返回结果中没有 b64_json 或 url')
}
