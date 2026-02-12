"""
Flask API 服务器示例
用于接收和管理技能商店数据
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域请求

SKILLS_FILE = 'skills_store.json'
API_KEY = 'your_secret_api_key_here'  # 生产环境请使用环境变量


def verify_api_key():
    """验证 API Key"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header[7:]
    return token == API_KEY


def load_skills():
    """加载技能数据"""
    if os.path.exists(SKILLS_FILE):
        with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'skills': [], 'total': 0, 'updated_at': None}


def save_skills(data):
    """保存技能数据"""
    data['updated_at'] = datetime.now().isoformat()
    with open(SKILLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route('/api/skills', methods=['GET'])
def get_skills():
    """获取所有技能"""
    data = load_skills()
    
    # 支持分页
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    skills = data['skills']
    total = len(skills)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return jsonify({
        'skills': skills[start:end],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/skills/batch', methods=['POST'])
def batch_import():
    """批量导入技能"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    skills = data.get('skills', [])
    
    if not skills:
        return jsonify({'error': 'No skills provided'}), 400
    
    store = load_skills()
    store['skills'] = skills
    store['total'] = len(skills)
    save_skills(store)
    
    return jsonify({
        'success': True,
        'added': len(skills),
        'message': 'Skills imported successfully'
    })


@app.route('/api/skills/<path:skill_name>', methods=['GET'])
def get_skill(skill_name):
    """获取单个技能"""
    store = load_skills()
    
    for skill in store['skills']:
        if skill['name'] == skill_name:
            return jsonify(skill)
    
    return jsonify({'error': 'Skill not found'}), 404


@app.route('/api/skills/<path:skill_name>', methods=['PUT'])
def update_skill(skill_name):
    """更新技能"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    skill_data = request.json
    store = load_skills()
    
    # 查找并更新
    for i, skill in enumerate(store['skills']):
        if skill['name'] == skill_name:
            store['skills'][i] = skill_data
            save_skills(store)
            return jsonify({'success': True, 'updated': True})
    
    # 不存在则添加
    store['skills'].append(skill_data)
    store['total'] = len(store['skills'])
    save_skills(store)
    return jsonify({'success': True, 'created': True}), 201


@app.route('/api/skills/<path:skill_name>', methods=['DELETE'])
def delete_skill(skill_name):
    """删除技能"""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    store = load_skills()
    original_count = len(store['skills'])
    store['skills'] = [s for s in store['skills'] if s['name'] != skill_name]
    
    if len(store['skills']) == original_count:
        return jsonify({'error': 'Skill not found'}), 404
    
    store['total'] = len(store['skills'])
    save_skills(store)
    return jsonify({'success': True, 'deleted': True})


@app.route('/api/skills/search', methods=['GET'])
def search_skills():
    """搜索技能"""
    query = request.args.get('q', '').lower()
    category = request.args.get('category', '')
    
    store = load_skills()
    skills = store['skills']
    
    # 过滤
    if query:
        skills = [s for s in skills if 
                  query in s['name'].lower() or 
                  query in s['description'].lower()]
    
    if category:
        skills = [s for s in skills if s['category'] == category]
    
    return jsonify({
        'skills': skills,
        'total': len(skills)
    })


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    store = load_skills()
    categories = {}
    
    for skill in store['skills']:
        cat = skill.get('category', 'Other')
        categories[cat] = categories.get(cat, 0) + 1
    
    return jsonify({
        'categories': [
            {'name': name, 'count': count}
            for name, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)
        ]
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    store = load_skills()
    
    categories = {}
    for skill in store['skills']:
        cat = skill.get('category', 'Other')
        categories[cat] = categories.get(cat, 0) + 1
    
    return jsonify({
        'total_skills': store['total'],
        'total_categories': len(categories),
        'last_updated': store.get('updated_at'),
        'top_categories': sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]
    })


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("=" * 60)
    print("技能商店 API 服务器")
    print("=" * 60)
    print(f"API Key: {API_KEY}")
    print("端点:")
    print("  GET    /api/skills          - 获取技能列表")
    print("  POST   /api/skills/batch    - 批量导入技能")
    print("  GET    /api/skills/<name>   - 获取单个技能")
    print("  PUT    /api/skills/<name>   - 更新技能")
    print("  DELETE /api/skills/<name>   - 删除技能")
    print("  GET    /api/skills/search   - 搜索技能")
    print("  GET    /api/categories      - 获取分类")
    print("  GET    /api/stats           - 获取统计")
    print("  GET    /health              - 健康检查")
    print("=" * 60)
    print()
    
    app.run(host='0.0.0.0', port=8000, debug=True)
