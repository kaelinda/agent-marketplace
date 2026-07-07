/**
 * 微信公众号主题配置
 * 
 * 提供多种排版主题供用户选择
 */

export const THEMES = {
  // 1. Reader 主题 - 暖色调阅读风格（默认）
  reader: {
    name: 'Reader',
    description: '暖色调沉浸阅读，适合技术文章',
    colors: {
      body: '#212121',
      heading: '#1a1a1a',
      secondary: '#555555',
      link: '#1a73e8',
      code: '#d63384',
      border: '#e8e8e8',
      bg: '#ffffff',
      codeBg: '#f6f8fa',
      blockquoteBg: '#f8f9fa',
      tableBorder: '#e1e4e8',
      tableHeader: '#f6f8fa',
    },
    fonts: {
      body: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      heading: 'Georgia, "Times New Roman", serif',
      code: '"SF Mono", "Fira Code", Consolas, "Liberation Mono", Menlo, monospace',
    },
    sizes: {
      body: '16px',
      h1: '24px',
      h2: '20px',
      h3: '18px',
      code: '14px',
    },
  },

  // 2. CodeFine 主题 - 深色代码风格
  codefine: {
    name: 'CodeFine',
    description: '深色背景，适合代码类内容',
    colors: {
      body: '#e6e6e6',
      heading: '#ffffff',
      secondary: '#8b949e',
      link: '#58a6ff',
      code: '#ff7b72',
      border: '#30363d',
      bg: '#0d1117',
      codeBg: '#161b22',
      blockquoteBg: '#161b22',
      tableBorder: '#30363d',
      tableHeader: '#21262d',
    },
    fonts: {
      body: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      heading: 'Georgia, "Times New Roman", serif',
      code: '"SF Mono", "Fira Code", Consolas, "Liberation Mono", Menlo, monospace',
    },
    sizes: {
      body: '16px',
      h1: '24px',
      h2: '20px',
      h3: '18px',
      code: '14px',
    },
  },

  // 3. Ocean 主题 - 海洋蓝色调
  ocean: {
    name: 'Ocean',
    description: '海蓝色调，专业沉稳',
    colors: {
      body: '#24292f',
      heading: '#0969da',
      secondary: '#57606a',
      link: '#0969da',
      code: '#d73a49',
      border: '#d0d7de',
      bg: '#ffffff',
      codeBg: '#f6f8fa',
      blockquoteBg: '#f6f8fa',
      tableBorder: '#d0d7de',
      tableHeader: '#f6f8fa',
    },
    fonts: {
      body: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      heading: 'Georgia, "Times New Roman", serif',
      code: '"SF Mono", "Fira Code", Consolas, "Liberation Mono", Menlo, monospace',
    },
    sizes: {
      body: '16px',
      h1: '24px',
      h2: '20px',
      h3: '18px',
      code: '14px',
    },
  },

  // 4. ChatEx 主题 - 聊天消息风格
  chatex: {
    name: 'ChatEx',
    description: '对话式布局，适合教程和问答',
    colors: {
      body: '#1f1f1f',
      heading: '#1a1a1a',
      secondary: '#666666',
      link: '#007bff',
      code: '#e83e8c',
      border: '#dee2e6',
      bg: '#ffffff',
      codeBg: '#f8f9fa',
      blockquoteBg: '#e3f2fd',
      tableBorder: '#dee2e6',
      tableHeader: '#f8f9fa',
    },
    fonts: {
      body: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      heading: '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", sans-serif',
      code: '"SF Mono", "Fira Code", Consolas, "Liberation Mono", Menlo, monospace',
    },
    sizes: {
      body: '16px',
      h1: '22px',
      h2: '18px',
      h3: '16px',
      code: '14px',
    },
  },
}

/**
 * 获取主题配置
 */
export function getTheme(name) {
  const theme = THEMES[name]
  if (!theme) {
    console.warn(`⚠️ 未知主题: ${name}，使用默认 reader 主题`)
    return THEMES.reader
  }
  return theme
}

/**
 * 列出所有可用主题
 */
export function listThemes() {
  return Object.entries(THEMES).map(([key, theme]) => ({
    id: key,
    name: theme.name,
    description: theme.description,
  }))
}
