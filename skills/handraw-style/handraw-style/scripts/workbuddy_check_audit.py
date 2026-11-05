"""Autonomous script to check the review result of handraw-skill on WorkBuddy."""
import asyncio
import json
import sys
import urllib.request
import websockets
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


async def check_audit():
    print(f"[{Path(__file__).name}] Connecting to Chrome CDP at 127.0.0.1:9221...")
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9221/json').read().decode('utf-8'))
    wb_tab = next((t for t in tabs if 'workbuddy.cn' in t.get('url', '')), None)
    if not wb_tab:
        raise RuntimeError("No WorkBuddy tab found in Chrome!")
    
    ws_url = wb_tab['webSocketDebuggerUrl']

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

        await eval_js("window.location.href = 'https://open.workbuddy.cn/skill/all'")
        await asyncio.sleep(2.5)

        # Specifically inspect the os_6905591d924fd407 card
        js = """
        (() => {
            const cards = Array.from(document.querySelectorAll('div, tr, section')).filter(el => 
                el.innerText && el.innerText.includes('os_6905591d924fd407')
            );
            if (cards.length === 0) return { error: 'Card os_6905591d924fd407 not found' };
            let targetCard = cards[0];
            for (const c of cards) {
                if (c.innerText.length < targetCard.innerText.length) {
                    targetCard = c;
                }
            }
            return {
                text: targetCard.innerText,
                hasRecallBtn: Boolean(Array.from(targetCard.querySelectorAll('button')).find(b => b.innerText.includes('撤回'))),
                hasRejectBtn: Boolean(Array.from(targetCard.querySelectorAll('button')).find(b => b.innerText.includes('驳回原因'))),
                hasResubmitBtn: Boolean(Array.from(targetCard.querySelectorAll('button')).find(b => b.innerText.includes('重新提交')))
            };
        })()
        """
        card_data = await eval_js(js)
        print("\n=== TARGET SKILL STATUS (os_6905591d924fd407) ===")
        print(card_data)

        text = card_data.get('text', '')
        if '审核中' in text or card_data.get('hasRecallBtn'):
            print("\n🟢 STATUS: UNDER REVIEW (审核中) - All automated static tests PASSED!")
            return 'IN_REVIEW'
        elif '已发布' in text or '已通过' in text:
            print("\n🎉 STATUS: PUBLISHED (已发布 / 已通过)!")
            return 'PUBLISHED'
        elif '已驳回' in text:
            print("\n🔴 STATUS: REJECTED (已驳回)")
            return 'REJECTED'
        else:
            return 'UNKNOWN'


if __name__ == "__main__":
    result = asyncio.run(check_audit())
    print("Final result:", result)
