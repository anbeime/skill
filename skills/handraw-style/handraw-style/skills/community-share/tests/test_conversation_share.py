import importlib.util
import io
import json
import urllib.error
from pathlib import Path

import pytest
from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/conversation_share.py"
spec = importlib.util.spec_from_file_location("conversation_share", SCRIPT)
share = importlib.util.module_from_spec(spec)
spec.loader.exec_module(share)


class FakeAPI:
    def __init__(self):
        self.uploads = []
        self.works = []
        self.fail_upload = None
        self.uncertain = False

    def current_user(self):
        return {"username": "creator", "user_id": 7}

    def upload(self, record):
        index = len(self.uploads)
        if self.fail_upload == index:
            self.fail_upload = None
            raise RuntimeError("upload failed")
        self.uploads.append(record)
        return {"sha256": record["sha256"], "short_url": f"upload://test{index}.png"}

    def check_work_access(self):
        pass

    def create_work(self, entry):
        self.works.append(entry)
        if self.uncertain:
            raise share.PostOutcomeUnknown("response lost")
        work_id = "12345678-1234-1234-1234-123456789abc"
        return {"id": work_id, "kind": "work",
                "url": f"/forum/?view=resource&kind=work&id={work_id}"}

    def get_work(self, entry_id):
        """Mirror the resource payload the real API returns for readback."""
        entry = self.works[-1]
        styles = [a["ref"].split(":", 1)[1] for a in entry["assets"] if a.get("role") == "style"]
        layouts = [a["ref"].split(":", 1)[1] for a in entry["assets"] if a.get("role") == "layout"]
        images = [entry["cover_url"]] + [e["image"] for e in entry["content"]["examples"]]
        return {"resource": {
            "id": entry_id,
            "kind": "work",
            "prompt": entry["content"]["prompt"],
            "images": images,
            "styles": styles,
            "layout": layouts[0] if layouts else "",
        }}

    def get_work_content(self, entry_id):
        return {"content": self.works[-1]["content"]}


def draft(tmp_path, request="ig-038，主题：原样保留。\n其他你帮我设计。", count=2):
    images = []
    for i in range(count):
        path = tmp_path / f"image-{i}.png"
        Image.new("RGB", (30, 40), (i * 20, 80, 120)).save(path)
        images.append(path)
    path = tmp_path / ".handraw-share.json"
    data = share.prepare_draft(path, request, images, "我的原创系列作品", style_ids=['FA-013'], layout_ids=[])
    return path, data, images


def test_prepare_preserves_exact_request_and_makes_no_network_call(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("prepare must never use the network")
    monkeypatch.setattr(share.urllib.request, "build_opener", forbidden)
    original = '  ig-038，主题：第一行\r\n```text\r\n不要改写这句话\r\n```\r\n末尾空格  '
    path, data, images = draft(tmp_path, original)
    assert data["original_request"] == original
    assert json.loads(path.read_text(encoding="utf-8"))["original_request"] == original
    assert data["uploads"] == [] and data["status"] == "ready"
    assert data["original_request_sha256"] == share.digest(original.encode("utf-8"))


def test_publish_uploads_all_images_and_posts_only_original_request(tmp_path):
    path, data, _ = draft(tmp_path, count=4)
    api = FakeAPI()
    receipt = share.publish_draft(path, api)
    assert len(api.uploads) == 4 and len(api.works) == 1
    body = api.works[0]["content"]["prompt"]
    assert data["original_request"] in body
    assert len(api.works[0]['content']['examples']) == 3
    assert api.works[0]['cover_url'].endswith('test0.png')
    assert "风格名称" not in body and "api_key" not in body
    assert api.works[0]['kind'] == 'work' and api.works[0]['price'] == 0
    assert api.works[0]['assets'] == [{'ref':'official:FA-013','role':'style'}]
    # The receipt now carries the server-issued canonical work address, and the
    # payload must carry a stable requestId so a retry cannot duplicate the work.
    assert receipt["verified"] and receipt['associations_verified']
    assert '/forum/?view=resource&kind=work&id=' in receipt["url"], receipt["url"]
    assert api.works[0]['requestId'].startswith('skill-'), api.works[0].get('requestId')


def test_repeat_click_returns_original_post_without_reupload(tmp_path):
    path, data, _ = draft(tmp_path)
    api = FakeAPI()
    first = share.publish_draft(path, api)
    second = share.publish_draft(path, api)
    assert first == second and len(api.works) == 1 and len(api.uploads) == 2
    assert "查看已分享作品" in share.button(path, json.loads(path.read_text(encoding="utf-8")))


def test_intermediate_metadata_in_old_draft_is_never_shared(tmp_path):
    path, data, _ = draft(tmp_path, "我要做一张适合发小红书的图片。你帮我设计下")
    data.update(schema_version=2, share_recipe={'theme': '不要分享的二阶段主题'},
                share_instruction='不要分享的二阶段提示词')
    share.write_json(path, data)
    api = FakeAPI()
    share.publish_draft(path, api)
    body = api.works[0]['content']['prompt']
    assert data['original_request'] in body
    assert '二阶段' not in body and 'Skill 复刻指令' not in body


def test_failed_upload_resumes_without_reuploading_successful_images(tmp_path):
    path, _, _ = draft(tmp_path, count=3)
    api = FakeAPI()
    api.fail_upload = 1
    with pytest.raises(RuntimeError, match="upload failed"):
        share.publish_draft(path, api)
    assert len(api.uploads) == 1 and not api.works
    receipt = share.publish_draft(path, api)
    assert receipt["success"] and len(api.uploads) == 3 and len(api.works) == 1


def test_uncertain_post_does_not_create_duplicate_on_retry(tmp_path):
    path, _, _ = draft(tmp_path)
    api = FakeAPI()
    api.uncertain = True
    with pytest.raises(share.PostOutcomeUnknown):
        share.publish_draft(path, api)
    with pytest.raises(share.PostOutcomeUnknown):
        share.publish_draft(path, api)
    assert len(api.works) == 1
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "publication_uncertain"


def test_changed_image_or_request_is_rejected_before_upload(tmp_path):
    path, data, images = draft(tmp_path)
    Image.new("RGB", (30, 40), "red").save(images[0])
    api = FakeAPI()
    with pytest.raises(ValueError, match="图片已更改"):
        share.publish_draft(path, api)
    assert not api.uploads and not api.works
    data["original_request"] += "parsed prompt replacement"
    share.write_json(path, data)
    with pytest.raises(ValueError, match="原始指令"):
        share.publish_draft(path, api)


def test_markdown_fence_does_not_allow_original_instruction_to_escape(tmp_path):
    original = '```\n# 这仍然是原始指令\n```\n[原样保留](https://example.com)'
    _, data, _ = draft(tmp_path, original)
    data["uploads"] = [{"short_url": "upload://one.png"}]
    body = share.markdown_body(data)
    assert f"````text\n{share.shared_prompt(data)}\n````" in body
    assert share.shared_prompt(data).startswith(original)


def test_original_message_is_unchanged_and_actual_ids_are_appended_in_same_prompt(tmp_path):
    path, data, _ = draft(tmp_path, '  帮我做一张图\r\n保留空格  ')
    original_hash = data['original_request_sha256']
    data = share.annotate_draft(path, ['fa-013', 'FA-013', 'FA-002'], ['ig-038'])
    assert data['original_request_sha256'] == original_hash
    assert data['original_request'] == '  帮我做一张图\r\n保留空格  '
    assert share.shared_prompt(data) == data['original_request']+'\n【画风：FA-013、FA-002 】 【图型：IG-038 】'
    api = FakeAPI()
    share.publish_draft(path, api)
    assert share.shared_prompt(data) == api.works[0]['content']['prompt']
    assert '核心风格特征' not in api.works[0]['content']['prompt']
    assert api.works[0]['assets'][-1] == {'ref':'official:IG-038','role':'layout'}
    before = path.read_bytes()
    with pytest.raises(ValueError, match='待发布'):
        share.annotate_draft(path, ['FA-013'], [])
    assert path.read_bytes() == before


def test_unused_and_unrecorded_layouts_have_no_public_label(tmp_path):
    path, data, _ = draft(tmp_path)
    data.pop('resolved_layout_ids')
    data.pop('resolved_ids_sha256')
    assert share.id_note(data) == '【画风：FA-013 】'
    data = share.annotate_draft(path, ['FA-013'], [])
    assert share.id_note(data) == '【画风：FA-013 】'
    assert data['uploads'] == [] and data['receipt'] is None


def test_prompt_omits_empty_tags_and_keeps_only_actual_ids(tmp_path):
    path,data,_=draft(tmp_path)
    data=share.annotate_draft(path,[],[])
    assert share.shared_prompt(data)==data['original_request']
    data=share.annotate_draft(path,[],['IG-038'])
    assert share.shared_prompt(data)==data['original_request']+'\n【图型：IG-038 】'
    assert '备注' not in share.shared_prompt(data) and '未使用' not in share.shared_prompt(data)


def test_invalid_or_tampered_ids_are_rejected_before_upload(tmp_path):
    path, data, _ = draft(tmp_path)
    before = path.read_bytes()
    with pytest.raises(ValueError, match='未收录'):
        share.annotate_draft(path, ['FA-999'], [])
    assert path.read_bytes() == before
    data = share.annotate_draft(path, ['FA-013'], [])
    data['resolved_style_ids'] = ['FA-002']
    share.write_json(path, data)
    api = FakeAPI()
    with pytest.raises(ValueError, match='编号已更改'):
        share.publish_draft(path, api)
    assert not api.uploads and not api.works


def test_draft_is_idempotent_but_cannot_be_overwritten_with_other_work(tmp_path):
    path, data, images = draft(tmp_path)
    assert share.prepare_draft(path, data["original_request"], images, data["title"])["draft_id"] == data["draft_id"]
    with pytest.raises(ValueError, match="其他内容"):
        share.prepare_draft(path, "另一份完全不同的创作指令", images)


def test_share_entry_uses_a_real_url_and_does_not_assume_host_directives(tmp_path):
    path, data, _ = draft(tmp_path)
    url = 'http://127.0.0.1:18763/share/' + 'a' * 32
    codex = share.button(path, data, page_url=url)
    assert codex == f'[分享到网站]({url})'
    assert "api_key" not in codex and data["original_request"] not in codex
    claude = share.button(path, data, "claude")
    assert "回复“分享到网站”" in claude and ":codex-followup" not in claude


def test_publish_lock_blocks_concurrent_duplicate_click(tmp_path):
    path, _, _ = draft(tmp_path)
    path.with_name(path.name + ".publish.lock").write_text("busy", encoding="utf-8")
    api = FakeAPI()
    with pytest.raises(RuntimeError, match="正在发布"):
        share.publish_draft(path, api)
    assert not api.uploads and not api.works


def test_api_credentials_stay_in_headers_and_use_fixed_official_origin(monkeypatch):
    captured = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b'{"user":{"username":"creator","id":7}}'
    class Opener:
        def open(self, request, timeout):
            captured.append(request)
            return Response()
    monkeypatch.setattr(share.urllib.request, "build_opener", lambda *args: Opener())
    api = share.CommunityAPI("test-personal-key-123456789")
    assert api.current_user()["username"] == "creator"
    request = captured[0]
    assert request.full_url == "https://handraw-style.com/api/boot"
    assert request.get_header("Api-key") == "test-personal-key-123456789"
    assert not request.has_header("Api-username")
    assert "test-personal-key" not in request.full_url


def test_other_account_cannot_resume_previous_uploads(tmp_path):
    path, data, _ = draft(tmp_path)
    data["account"] = {"username": "someone-else", "user_id": 99}
    share.write_json(path, data)
    api = FakeAPI()
    with pytest.raises(ValueError, match="其他账号"):
        share.publish_draft(path, api)
    assert not api.uploads and not api.works


def test_work_api_sends_native_entry_with_asset_links_not_forum_raw(monkeypatch, tmp_path):
    path, data, _ = draft(tmp_path)
    data['uploads'] = [{'short_url':'upload://image0.png'}, {'url':'https://static.handraw-style.com/uploads/image1.png'}]
    payload = share.work_payload(data)
    captured = []
    api = share.CommunityAPI('test-personal-key-123456789')
    def request(method, endpoint, body, content_type):
        captured.append((method,endpoint,json.loads(body)))
        return {'id':'12345678-1234-1234-1234-123456789abc','kind':'work'}
    monkeypatch.setattr(api,'request',request)
    api.create_work(payload)
    assert captured[0][0:2] == ('POST','/api/entries')
    entry = captured[0][2]['entry']
    assert entry['kind']=='work' and entry['price']==0 and not entry['paid_opt_in']
    assert entry['assets']==[{'ref':'official:FA-013','role':'style'}]
    assert entry['cover_url']=='/uploads/short-url/image0.png'
    assert entry['content']['examples'][0]['image']=='https://static.handraw-style.com/uploads/image1.png'
    assert 'raw' not in entry and 'category' not in entry


def test_work_api_uncertain_creation_blocks_replay(monkeypatch):
    api=share.CommunityAPI('test-personal-key-123456789')
    class Opener:
        def open(self,request,timeout):
            raise urllib.error.HTTPError(request.full_url,500,'server error',{},None)
    monkeypatch.setattr(share.urllib.request,'build_opener',lambda *args:Opener())
    with pytest.raises(share.PostOutcomeUnknown):
        api.create_work({'kind':'work'})


def test_api_validation_error_is_readable_and_credentials_are_redacted(monkeypatch):
    key='test-personal-key-123456789'
    api=share.CommunityAPI(key)
    class Opener:
        def open(self,request,timeout):
            body=json.dumps({'errors':[f"此标题已被<a href='/t/246'>其他话题</a>使用。 {key}"]}).encode('utf-8')
            raise urllib.error.HTTPError(request.full_url,422,'invalid',{},io.BytesIO(body))
    monkeypatch.setattr(share.urllib.request,'build_opener',lambda *args:Opener())
    with pytest.raises(share.APIRejected) as error:
        api.create_work({'kind':'work'})
    assert 'HTTP 422' in str(error.value) and '此标题已被其他话题使用' in str(error.value)
    assert '<a' not in str(error.value) and key not in str(error.value)


def test_missing_ids_or_too_many_images_never_upload(tmp_path):
    path,data,_=draft(tmp_path,count=10)
    api=FakeAPI()
    with pytest.raises(ValueError,match='最多8张附图'):
        share.publish_draft(path,api)
    data['images']=data['images'][:1]
    data['resolved_layout_ids']=None
    data.pop('resolved_ids_sha256')
    share.write_json(path,data)
    with pytest.raises(ValueError,match='补充实际'):
        share.publish_draft(path,api)
    assert not api.uploads and not api.works


def test_bad_image_url_is_rejected_without_falling_back_to_forum(tmp_path):
    path,data,_=draft(tmp_path)
    data['uploads']=[{'url':'https://evil.example/image.png'}]*2
    with pytest.raises(ValueError,match='本站'):
        share.work_payload(data)


def test_forum_receipt_is_never_reported_as_work_square_success(tmp_path):
    path,data,_=draft(tmp_path)
    data.update(status='published',receipt={'url':'https://handraw-style.com/t/topic/246','verified':True})
    share.write_json(path,data)
    api=FakeAPI()
    with pytest.raises(ValueError,match='论坛帖'):
        share.publish_draft(path,api)
    assert not api.uploads and not api.works
    assert '旧版记录' in share.button(path,data)


def test_readback_with_missing_assets_does_not_claim_verified_associations(tmp_path):
    path,_,_=draft(tmp_path)
    api=FakeAPI()
    original_get=api.get_work
    def without_styles(entry_id):
        detail=original_get(entry_id)
        detail["resource"]["styles"]=[]
        detail["resource"]["layout"]=""
        return detail
    api.get_work=without_styles
    receipt=share.publish_draft(path,api)
    assert receipt['destination']=='work_square'
    assert not receipt['verified'] and not receipt['associations_verified']
