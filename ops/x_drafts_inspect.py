#!/usr/bin/env python3
"""Click the real Drafts button, dump drawer. Read-only v5."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

JS_BUTTONS = """
JSON.stringify((function(){
  var out=[];
  var b = document.querySelectorAll('[role="button"],button,a');
  for (var i=0;i<b.length;i++){
    var t=(b[i].innerText||'').trim();
    if (/draft/i.test(t)) out.push({tag:b[i].tagName, text:t.slice(0,30), testid:b[i].getAttribute('data-testid')||'', href:b[i].getAttribute('href')||''});
  }
  return out;
})())
"""

JS_CLICK_BTN = """
JSON.stringify((function(){
  var b = document.querySelectorAll('[role="button"],button,a');
  for (var i=0;i<b.length;i++){
    var t=(b[i].innerText||'').trim();
    if (/^drafts?$/i.test(t)) {
      b[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
      return {ok:true, tag:b[i].tagName, testid:b[i].getAttribute('data-testid')||''};
    }
  }
  return {ok:false};
})())
"""

JS_PAGE_TEXT = """
JSON.stringify((function(){
  var d = document.querySelector('[role="dialog"]');
  var txt = d ? d.innerText : document.body.innerText;
  return {len: (txt||'').length, text: (txt||'').slice(0,2000)};
})())
"""

async def call(s, name, args=None):
    res = await s.call_tool(name, args or {})
    return "\n".join([getattr(c, "text", None) or str(c) for c in (getattr(res, "content", []) or [])])

async def main():
    async with streamable_http_client(URL) as ctx:
        r, w = ctx[0], ctx[1]
        async with ClientSession(r, w) as s:
            await s.initialize()
            np = json.loads(await call(s, "cloak_new_page", {"url": "about:blank"}))
            page = np.get("page_id") or np.get("id")
            await call(s, "cloak_navigate", {"page_id": page, "url": "https://x.com/compose/post"})
            await asyncio.sleep(4.0)
            print("DRAFT CONTROLS:", (await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_BUTTONS}))[:600])
            print("CLICK:", (await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_CLICK_BTN}))[:300])
            await asyncio.sleep(3.0)
            print("AFTER:")
            print((await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_PAGE_TEXT}))[:2600])
            try:
                await call(s, "cloak_close_page", {"page_id": page})
            except Exception:
                pass

asyncio.run(main())
