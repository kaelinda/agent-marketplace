#!/usr/bin/env node

/**
 * 微信公众号草稿发布工具 - CLI
 * 
 * 用法:
 *   npx wechat-publisher test
 *   npx wechat-publisher publish --title "标题" --markdown ./article.md --theme reader
 *   npx wechat-publisher publish --title "标题" --content "# 内容" --theme codefine
 *   npx wechat-publisher publish --title "标题" --markdown ./article.md --account parenting
 *   npx wechat-publisher themes
 */

import minimist from 'minimist'
import chalk from 'chalk'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { testConnection, loadEnv, checkEnv } from './wechatApi.js'
import { publishArticle } from './publisher.js'
import { listThemes } from './themes.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const argv = minimist(process.argv.slice(2))
const command = argv._[0]

// 多账号支持：根据 --account 参数选择凭证文件
const account = argv.account || 'tech'
const envFiles = {
  tech: path.join(__dirname, '..', 'wechat.env'),
  parenting: path.join(__dirname, '..', 'wechat-parenting.env')
}

// 先尝试加载指定账号的凭证文件
const envFile = envFiles[account]
if (fs.existsSync(envFile)) {
  const content = fs.readFileSync(envFile, 'utf-8')
  content.split('\n').forEach(line => {
    const match = line.match(/^export\s+(\w+)="(.*)"$/)
    if (match) {
      process.env[match[1]] = match[2]
    }
  })
} else {
  loadEnv() // 回退到默认 .env
}

// 命令分发
switch (command) {
  case 'test':
    await cmdTest()
    break

  case 'publish':
    await cmdPublish()
    break

  case 'themes':
    cmdThemes()
    break

  default:
    showHelp()
}

// ============================================================

async function cmdTest() {
  console.log(chalk.cyan('🔍 测试微信 API 连接...\n'))

  const result = await testConnection()

  if (result.success) {
    console.log(chalk.green('✅ 连接成功！'))
    console.log(`   AppID: ${result.appId}`)
    console.log(`   Token: ${result.token.substring(0, 20)}...`)
  } else {
    console.log(chalk.red('❌ 连接失败'))
    console.log(`   错误: ${result.error}`)
    console.log('\n请检查:')
    console.log('   1. .env 文件中的 APP_ID 和 APP_SECRET 是否正确')
    console.log('   2. 服务器 IP 是否已加入微信公众号白名单')
    console.log(`   3. 当前 IP: ${result.ip || '未知'}`)
  }
}

async function cmdPublish() {
  const { 
    title, 
    markdown, 
    content, 
    author, 
    cover,
    theme = 'reader'
  } = argv

  const accountNames = { tech: '技术号 (AICoder)', parenting: '育儿号 (亲子成长陪伴育儿育己)' }
  console.log(chalk.gray(`📱 账号: ${accountNames[account] || account}\n`))

  // 验证必填参数
  if (!title) {
    console.error(chalk.red('❌ 缺少参数: --title 是必填的'))
    process.exit(1)
  }

  if (!markdown && !content) {
    console.error(chalk.red('❌ 缺少参数: 需要 --markdown 或 --content'))
    process.exit(1)
  }

  // 检查环境变量
  try {
    checkEnv()
  } catch (err) {
    console.error(chalk.red('❌ 缺少环境变量配置'))
    console.error('请确保 .env 文件中包含 WECHAT_APP_ID 和 WECHAT_APP_SECRET')
    process.exit(1)
  }

  // 验证主题
  const validThemes = ['reader', 'codefine', 'ocean', 'chatex']
  if (!validThemes.includes(theme)) {
    console.error(chalk.red(`❌ 无效主题: ${theme}`))
    console.error(`可用主题: ${validThemes.join(', ')}`)
    process.exit(1)
  }

  console.log(chalk.cyan(`📝 开始发布文章: ${title}\n`))

  try {
    const result = await publishArticle({
      title,
      markdown,
      content,
      author,
      cover,
      theme,
    })

    console.log(chalk.green('\n✅ 发布成功！'))
    console.log(`   标题: ${result.title}`)
    console.log(`   作者: ${result.author}`)
    console.log(`   主题: ${result.theme}`)
    console.log(`   草稿ID: ${result.mediaId}`)
    console.log(`   内容大小: ${(result.contentLength / 1024).toFixed(1)} KB`)
    console.log(`   图片数量: ${result.imagesUploaded}`)
    console.log('\n📌 请登录微信公众号后台 -> 内容与互动 -> 草稿箱 -> 预览并发布')

  } catch (err) {
    console.error(chalk.red('\n❌ 发布失败:', err.message))
    process.exit(1)
  }
}

function cmdThemes() {
  console.log(chalk.cyan('🎨 可用的主题:\n'))

  const themes = listThemes()
  themes.forEach((t, i) => {
    const num = (i + 1).toString().padStart(2, ' ')
    console.log(`  ${chalk.yellow(num)}. ${chalk.bold(t.name)}`)
    console.log(`      ${t.description}`)
    console.log('')
  })

  console.log(chalk.gray('  使用方式: --theme <主题名>'))
  console.log(chalk.gray('  示例: npx wechat-publisher publish --title "标题" --markdown ./a.md --theme codefine\n'))
}

function showHelp() {
  console.log(`
${chalk.cyan('微信公众号草稿发布工具')}

${chalk.yellow('命令:')}

  ${chalk.bold('npx wechat-publisher test')}
      测试 API 连接是否正常

  ${chalk.bold('npx wechat-publisher publish --title "标题" --markdown <文件> [选项]')}
      发布文章到草稿箱

  ${chalk.bold('npx wechat-publisher themes')}
      查看所有可用主题

${chalk.yellow('发布选项:')}

  --title    文章标题（必填）
  --markdown Markdown 文件路径
  --content  Markdown 内容（与 --markdown 二选一）
  --author   作者名
  --cover    封面图路径
  --theme    主题名称（默认: reader）
  --account  账号选择（默认: tech）
             tech = 技术号 (AICoder)
             parenting = 育儿号 (亲子成长陪伴育儿育己)

${chalk.yellow('可用主题:')}

  reader    暖色调沉浸阅读（默认）
  codefine  深色代码风格
  ocean     海蓝色调专业沉稳
  chatex    聊天消息风格

${chalk.yellow('示例:')}

  ${chalk.gray('# 测试连接')}
  npx wechat-publisher test

  ${chalk.gray('# 发布到技术号（默认）')}
  npx wechat-publisher publish --title "Hello" --markdown ./article.md --author 张三

  ${chalk.gray('# 发布到育儿号')}
  npx wechat-publisher publish --title "育儿心得" --markdown ./parenting.md --account parenting

  ${chalk.gray('# 使用 CodeFine 主题')}
  npx wechat-publisher publish --title "代码教程" --markdown ./code.md --theme codefine

  ${chalk.gray('# 直接传入内容')}
  npx wechat-publisher publish --title "标题" --content "# 内容" --theme ocean
`)
}
