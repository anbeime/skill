import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import conversation_share as share
import conversation_share_ui as ui


class FakeAPI:
    def __init__(self): self.uploads, self.works = [], []
    def current_user(self): return {'username': 'creator', 'user_id': 7}
    def check_work_access(self): pass
    def upload(self, record):
        self.uploads.append(record)
        return {'sha256': record['sha256'], 'short_url': 'upload://test.png'}
    def create_work(self, entry):
        self.works.append(entry)
        work_id = '12345678-1234-1234-1234-123456789abc'
        return {'id': work_id, 'kind': 'work',
                'url': f'/forum/?view=resource&kind=work&id={work_id}'}
    def get_work(self, entry_id):
        entry = self.works[-1]
        styles = [a['ref'].split(':', 1)[1] for a in entry['assets'] if a.get('role') == 'style']
        layouts = [a['ref'].split(':', 1)[1] for a in entry['assets'] if a.get('role') == 'layout']
        return {'resource': {
            'id': entry_id, 'kind': 'work',
            'prompt': entry['content']['prompt'],
            'images': [entry['cover_url']] + [e['image'] for e in entry['content']['examples']],
            'styles': styles, 'layout': layouts[0] if layouts else '',
        }}
    def get_work_content(self, entry_id): return {'content': self.works[-1]['content']}


@pytest.fixture
def page(tmp_path):
    image = tmp_path / 'output.png'
    Image.new('RGB', (30, 40), 'orange').save(image)
    path = tmp_path / '.share.json'
    original = '  原始指令\n<script>保留文字，不执行</script>  '
    share.prepare_draft(path, original, [image], '测试分享预览页面', style_ids=['FA-013'], layout_ids=[])
    cache = tmp_path / 'registry'
    token = ui.register_draft(path, cache)
    api = FakeAPI()
    server = ui.ShareServer(('127.0.0.1', 0), cache, lambda: api)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}', token, api, path, original
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_opening_preview_loading_info_and_images_never_publishes(page):
    origin, token, api, path, original = page
    html = urllib.request.urlopen(f'{origin}/share/{token}').read().decode()
    assert '<button id="publish"' in html
    assert '分享到作品广场' in html and 'addEventListener(\'click\'' in html
    assert 'textContent=d.shared_prompt' in html
    info = json.load(urllib.request.urlopen(f'{origin}/api/share/{token}'))
    assert info['original_request'] == original and info['status'] == 'ready'
    assert info['shared_prompt'].startswith(original)
    assert info['shared_prompt']==original+'\n【画风：FA-013 】'
    assert 'api_key' not in json.dumps(info)
    assert urllib.request.urlopen(origin + info['images'][0]['src']).read().startswith(b'\x89PNG')
    assert not api.uploads and not api.works


def test_publish_requires_same_origin_post_and_explicit_action_header(page):
    origin, token, api, path, original = page
    endpoint = f'{origin}/api/share/{token}/publish'
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(endpoint)
    assert error.value.code == 404
    for headers in [{}, {'Origin': 'https://evil.example', 'X-Handraw-Share': token}]:
        request = urllib.request.Request(endpoint, data=b'{}', headers={'Content-Type': 'application/json', **headers})
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(request)
        assert error.value.code == 403
    assert not api.uploads and not api.works


def test_real_publish_action_returns_post_and_repeat_click_is_idempotent(page):
    origin, token, api, path, original = page
    def click():
        request = urllib.request.Request(f'{origin}/api/share/{token}/publish', data=b'{}',
            headers={'Content-Type': 'application/json', 'Origin': origin, 'X-Handraw-Share': token})
        return json.load(urllib.request.urlopen(request))
    first, second = click(), click()
    assert first['url'] == second['url'] and first['verified']
    assert len(api.uploads) == len(api.works) == 1 and original in api.works[0]['content']['prompt']
    assert api.works[0]['content']['prompt']==original+'\n【画风：FA-013 】'
    info = json.load(urllib.request.urlopen(f'{origin}/api/share/{token}'))
    assert info['status'] == 'published' and info['work_url'] == first['url']


def test_unregistered_or_path_traversal_links_are_not_served(page):
    origin, token, api, path, original = page
    for suffix in ['/share/' + 'b' * 32, '/share/../../credentials.json']:
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(origin + suffix)
        assert error.value.code == 404
    assert not api.works


def test_preview_uses_original_request_even_for_previous_intermediate_draft(page):
    origin, token, api, path, original = page
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(schema_version=2, share_instruction='不要分享的二阶段提示词')
    share.write_json(path, data)
    info = json.load(urllib.request.urlopen(f'{origin}/api/share/{token}'))
    assert info['original_request'] == original
    assert 'share_instruction' not in info and '二阶段' not in json.dumps(info,ensure_ascii=False)
    assert not api.uploads and not api.works


def test_old_forum_receipt_is_labeled_separately_from_work_square(page):
    origin,token,api,path,original=page
    data=json.loads(path.read_text(encoding='utf-8'))
    data.update(status='published',receipt={'url':'https://handraw-style.com/t/topic/246'})
    share.write_json(path,data)
    info=json.load(urllib.request.urlopen(f'{origin}/api/share/{token}'))
    assert info['work_url'] is None
    assert info['legacy_forum_url']=='https://handraw-style.com/t/topic/246'
    assert not api.uploads and not api.works
