"""Autonomous script to resubmit handraw-skill v1.0.3 to WorkBuddy after midnight."""
import asyncio
import json
import os
import sys
import urllib.request
import websockets
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = str(ROOT / "dist" / "handraw-skill-workbuddy-v1.0.3.zip")
AVATAR_PATH = str(ROOT / "images" / "avatar.png")

assert os.path.exists(ZIP_PATH), f"Zip not found: {ZIP_PATH}"
assert os.path.exists(AVATAR_PATH), f"Avatar not found: {AVATAR_PATH}"


async def run_resubmit():
    print(f"[{Path(__file__).name}] Connecting to Chrome CDP at 127.0.0.1:9221...")
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9221/json').read().decode('utf-8'))
    wb_tab = next((t for t in tabs if 'workbuddy.cn' in t.get('url', '')), None)
    if not wb_tab:
        raise RuntimeError("No WorkBuddy tab found in Chrome!")
    
    ws_url = wb_tab['webSocketDebuggerUrl']
    print(f"Connected to WorkBuddy tab: {wb_tab.get('title')}")

    async with websockets.connect(ws_url, max_size=20_000_000) as ws:
        msg_id = 1

        async def call(method, params=None):
            nonlocal msg_id
            msg_id += 1
            curr_id = msg_id
            await ws.send(json.dumps({'id': curr_id, 'method': method, 'params': params or {}}))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get('id') == curr_id:
                    return resp.get('result', {})

        async def eval_js(expr):
            res = await call('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
            return res.get('result', {}).get('value')

        print("1. Navigating to https://open.workbuddy.cn/skill/all...")
        await eval_js("window.location.href = 'https://open.workbuddy.cn/skill/all'")
        await asyncio.sleep(3.0)

        # Close any leftover modal if present
        await eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('我知道了'));
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(1.0)

        print("2. Finding '手绘skill' card and clicking '重新提交'...")
        click_res = await eval_js("""
        (() => {
            // Find card containing '手绘skill' or 'os_6905591d924fd407'
            const cards = document.querySelectorAll('div, tr, section');
            for (const c of cards) {
                if (c.innerText && (c.innerText.includes('手绘skill') || c.innerText.includes('os_6905591d924fd407'))) {
                    const btn = Array.from(c.querySelectorAll('button')).find(b => b.innerText.includes('重新提交'));
                    if (btn && !btn.disabled) {
                        btn.click();
                        return 'clicked 重新提交 on 手绘skill card';
                    }
                }
            }
            // Fallback: click first enabled '重新提交' button
            const allBtns = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('重新提交') && !b.disabled);
            if (allBtns.length > 0) {
                allBtns[0].click();
                return 'clicked first available 重新提交';
            }
            return 'not found';
        })()
        """)
        print("Click result:", click_res)
        await asyncio.sleep(3.0)

        # Check if modal '同一资产每日提交上限为3次' popped up
        page_text = await eval_js("document.body.innerText")
        if '同一资产每日提交上限为3次' in page_text:
            print("ERROR: Daily limit modal still present! It might not have reset yet.")
            return False

        curr_url = await eval_js("window.location.href")
        print("Current URL:", curr_url)

        # Step 1: Upload zip
        print("3. Uploading handraw-skill-workbuddy-v1.0.3.zip on Step 1...")
        doc = await call('DOM.getDocument')
        file_input = await call('DOM.querySelector', {
            'nodeId': doc['root']['nodeId'],
            'selector': 'input[type="file"]'
        })
        if not file_input or not file_input.get('nodeId'):
            raise RuntimeError("File input not found on Step 1!")
            
        node_id = file_input['nodeId']
        await call('DOM.setFileInputFiles', {
            'nodeId': node_id,
            'files': [ZIP_PATH]
        })
        print(f"Set file {ZIP_PATH} on input. Waiting for parsing...")

        parsed = False
        for sec in range(12):
            await asyncio.sleep(1.0)
            text = await eval_js("document.body.innerText")
            if '解析失败' in text:
                print("PARSING ERROR:", text)
                raise RuntimeError("Package parsing failed!")
            if 'handraw-skill-workbuddy-v1.0.3.zip' in text or '重新上传' in text:
                print(f"Package uploaded and parsed successfully ({sec}s)!")
                parsed = True
                break

        if not parsed:
            raise RuntimeError("Timeout waiting for package parsing!")

        # Click 继续 to Step 2
        print("4. Clicking '继续' to go to Step 2...")
        await eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === '继续');
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(2.5)

        # Step 2: Information form
        print("5. On Step 2. Verifying and filling information form...")
        step2_text = await eval_js("document.body.innerText")
        print("Step 2 summary snippet:\n", '\n'.join([l.strip() for l in step2_text.splitlines() if l.strip()][:25]))

        # Check avatar
        has_avatar = await eval_js("Boolean(document.querySelector('img[src*=\"data:image\"], img[src*=\"blob:\"]'))")
        print("Has avatar:", has_avatar)
        if not has_avatar:
            # Upload avatar
            print("Uploading avatar...")
            doc = await call('DOM.getDocument')
            img_input = await call('DOM.querySelector', {
                'nodeId': doc['root']['nodeId'],
                'selector': 'input[type="file"][accept*="image"]'
            })
            if img_input and img_input.get('nodeId'):
                await call('DOM.setFileInputFiles', {
                    'nodeId': img_input['nodeId'],
                    'files': [AVATAR_PATH]
                })
                await asyncio.sleep(2.0)
                # Confirm crop if crop modal appears
                await eval_js("""
                (() => {
                    const okBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('确定') || b.innerText.includes('完成'));
                    if (okBtn) okBtn.click();
                })()
                """)
                await asyncio.sleep(1.5)

        # Check and select categories if needed
        await eval_js("""
        (() => {
            // Select 内容创作 and 工具 - 图片处理
            const spans = Array.from(document.querySelectorAll('span, label, div'));
            for (const s of spans) {
                if (s.innerText === '内容创作' || s.innerText === '图片处理') {
                    s.click();
                }
            }
        })()
        """)
        await asyncio.sleep(1.0)

        # Click 继续 to Step 3
        print("6. Clicking '继续' to go to Step 3...")
        await eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === '继续');
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(2.5)

        # Step 3: Final Submit
        print("7. On Step 3. Clicking final '提交' / '提交审核'...")
        submit_res = await eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === '提交' || b.innerText.trim() === '提交审核');
            if (btn && !btn.disabled) {
                btn.click();
                return 'clicked 提交';
            }
            return 'submit button not found or disabled';
        })()
        """)
        print("Submit button click result:", submit_res)
        await asyncio.sleep(4.0)

        # Verify final status
        print("8. Verifying submission status on /skill/all...")
        await eval_js("window.location.href = 'https://open.workbuddy.cn/skill/all'")
        await asyncio.sleep(3.0)

        final_text = await eval_js("document.body.innerText")
        lines = [l.strip() for l in final_text.splitlines() if l.strip()]
        for idx, l in enumerate(lines):
            if any(k in l for k in ['手绘skill', '审核中', 'v1.0.3', 'os_6905591d924fd407']):
                print(f"[{idx}] {l}")

        if '审核中' in final_text and '手绘skill' in final_text:
            print("\n🎉 SUCCESS: '手绘skill' v1.0.3 submitted and now UNDER REVIEW!")
            return True
        else:
            print("\nWARNING: Status did not show '审核中', check manually.")
            return False


if __name__ == "__main__":
    success = asyncio.run(run_resubmit())
    sys.exit(0 if success else 1)
