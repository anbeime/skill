/**
 * 文件管理技能
 */

import fs from 'fs/promises';
import path from 'path';
import { Skill, SkillParams, SkillResult } from '../types.js';
import { logger } from '../../utils/logger.js';

export const fileManagementSkill: Skill = {
  name: 'file-management',
  description: '文件和文件夹管理操作',
  category: 'file',
  requiresConfirmation: true,

  async execute(params: SkillParams): Promise<SkillResult> {
    const { action, args } = params;

    try {
      switch (action) {
        case 'list':
          return await listFiles(args.directory);
        
        case 'organize':
          return await organizeFiles(args.directory);
        
        case 'search':
          return await searchFiles(args.directory, args.pattern);
        
        case 'create-folder':
          return await createFolder(args.path);
        
        default:
          return {
            success: false,
            error: `Unknown action: ${action}`
          };
      }
    } catch (error: any) {
      logger.error('File management skill error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
};

/**
 * 列出目录中的文件
 */
async function listFiles(directory: string): Promise<SkillResult> {
  const files = await fs.readdir(directory, { withFileTypes: true });
  
  const result = {
    files: files.filter(f => f.isFile()).map(f => f.name),
    folders: files.filter(f => f.isDirectory()).map(f => f.name),
    total: files.length
  };

  return {
    success: true,
    data: result,
    message: `找到 ${result.files.length} 个文件和 ${result.folders.length} 个文件夹`
  };
}

/**
 * 整理文件（按类型分类）
 */
async function organizeFiles(directory: string): Promise<SkillResult> {
  const files = await fs.readdir(directory);
  
  const categories: Record<string, string[]> = {
    '文档': ['.pdf', '.doc', '.docx', '.txt', '.md'],
    '图片': ['.jpg', '.jpeg', '.png', '.gif', '.svg'],
    '代码': ['.js', '.ts', '.py', '.java', '.cpp'],
    '压缩包': ['.zip', '.rar', '.7z', '.tar'],
    '其他': []
  };

  const organized: Record<string, string[]> = {};
  
  for (const file of files) {
    const ext = path.extname(file).toLowerCase();
    let category = '其他';
    
    for (const [cat, exts] of Object.entries(categories)) {
      if (exts.includes(ext)) {
        category = cat;
        break;
      }
    }
    
    if (!organized[category]) {
      organized[category] = [];
    }
    organized[category].push(file);
  }

  // 创建分类文件夹并移动文件
  for (const [category, fileList] of Object.entries(organized)) {
    if (fileList.length === 0) continue;
    
    const categoryPath = path.join(directory, category);
    await fs.mkdir(categoryPath, { recursive: true });
    
    for (const file of fileList) {
      const oldPath = path.join(directory, file);
      const newPath = path.join(categoryPath, file);
      await fs.rename(oldPath, newPath);
    }
  }

  return {
    success: true,
    data: organized,
    message: `文件已按类型整理到 ${Object.keys(organized).length} 个文件夹`
  };
}

/**
 * 搜索文件
 */
async function searchFiles(
  directory: string,
  pattern: string
): Promise<SkillResult> {
  const files = await fs.readdir(directory, { recursive: true });
  const regex = new RegExp(pattern, 'i');
  
  const matches = files.filter(file => regex.test(file.toString()));

  return {
    success: true,
    data: matches,
    message: `找到 ${matches.length} 个匹配的文件`
  };
}

/**
 * 创建文件夹
 */
async function createFolder(folderPath: string): Promise<SkillResult> {
  await fs.mkdir(folderPath, { recursive: true });
  
  return {
    success: true,
    message: `文件夹已创建: ${folderPath}`
  };
}
