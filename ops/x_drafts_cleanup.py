#!/usr/bin/env python3
"""Delete the 5 OLD plain quote drafts from X drafts (match by text; hublot only the one WITHOUT the JJK url).
Safety: aborts if selection count != 5 before deleting."""
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8932/mcp"

OLD_TEXTS = [
    "three leagues and five ballons",
    "the one piece psyop",
    "the chiikawa dub casting call",
    "imagine beating the boss",
    "hublot did a full tokyo takeover",  # only the one WITHOUT a JJK url inside
]

JS_OPEN_DRAFTS = """
JSON.stringify((function(){
  var b = document.querySelectorAll('[role="button"],button,a');
  for (var i=0;i<b.length;i++){
    if ((b[i].innerText||'').trim() === 'Drafts') { b[i].dispatchEvent(new MouseEvent('click',{bubbles:true})); return {ok:true}; }
  }
  return {ok:false};
})())
"""

JS_EDIT_POINTER = """
JSON.stringify((function(){
  var d = document.querySelector('[role="dialog"]') || document;
  var all = d.querySelectorAll('*');
  var el = null;
  for (var i=0;i<all.length;i++){
    if ((all[i].innerText||'').trim() === 'Edit' && all[i].children.length === 0) { el = all[i]; break; }
  }
  if (!el) return {ok:false};
  var target = el.closest('[role="button"]') || el.closest('button') || el;
  ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
    target.dispatchEvent(new MouseEvent(t, {bubbles:true, cancelable:true, view:window}));
  });
  return {ok:true};
})())
"""

JS_SELECT_OLD = """
JSON.stringify((function(){
  var targets = __TARGETS__;
  var d = document.querySelector('[role="dialog"]') || document;
  var cards = d.querySelectorAll('[data-testid="unsentTweet"]');
  var selected = [];
  for (var i=0;i<cards.length;i++){
    var txt = (cards[i].innerText||'');
    for (var j=0;j<targets.length;j++){
      if (txt.indexOf(targets[j]) !== -1) {
        // hublot guard: skip the card that contains the JJK url (that's the NEW quote draft)
        if (targets[j].indexOf('hublot') !== -1 && txt.indexOf('JJK_Times') !== -1) continue;
        var cb = cards[i].querySelector('[role="checkbox"], input[type="checkbox"]');
        var clickTarget = cb || cards[i];
        ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
          clickTarget.dispatchEvent(new MouseEvent(t, {bubbles:true, cancelable:true, view:window}));
        });
        selected.push(targets[j].slice(0,30));
        break;
      }
    }
  }
  return {selected: selected, count: selected.length};
})())
"""

JS_FIND_DELETE = """
JSON.stringify((function(){
  var d = document.querySelector('[role="dialog"]') || document;
  var out = [];
  var all = d.querySelectorAll('*');
  for (var i=0;i<all.length;i++){
    var t = (all[i].innerText||'').trim();
    if (/^(delete|delete all|remove)$/i.test(t) && all[i].children.length <= 1) {
      out.push({t:t, tag:all[i].tagName});
      if (out.length>5) break;
    }
  }
  var checked = d.querySelectorAll('[role="checkbox"][aria-checked="true"], input[type="checkbox"]:checked').length;
  return {deleteControls: out, checkedCount: checked};
})())
"""

JS_CLICK_DELETE = """
JSON.stringify((function(){
  var d = document.querySelector('[role="dialog"]') || document;
  var all = d.querySelectorAll('*');
  for (var i=0;i<all.length;i++){
    var t = (all[i].innerText||'').trim();
    if (/^(delete|delete all)$/i.test(t) && all[i].children.length <= 1) {
      var target = all[i].closest('[role="button"]') || all[i].closest('button') || all[i];
      ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(ev){
        target.dispatchEvent(new MouseEvent(ev, {bubbles:true, cancelable:true, view:window}));
      });
      return {ok:true, t:t};
    }
  }
  return {ok:false};
})())
"""

JS_CONFIRM = """
JSON.stringify((function(){
  var c = document.querySelector('[data-testid="confirmationSheetConfirm"]');
  if (c) { c.click(); return {ok:true}; }
  var d = document.querySelector('[role="dialog"]') || document;
  var all = d.querySelectorAll('[role="button"],button');
  for (var i=0;i<all.length;i++){
    var t=(all[i].innerText||'').trim();
    if (/^(delete|confirm|yes)/i.test(t)) { all[i].click(); return {ok:true, t:t}; }
  }
  return {ok:false};
})())
"""

JS_COUNT = """
JSON.stringify((function(){
  var d = document.querySelector('[role="dialog"]') || document;
  return {drafts: d.querySelectorAll('[data-testid="unsentTweet"]').length};
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
            await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_OPEN_DRAFTS})
            await asyncio.sleep(2.5)
            await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_EDIT_POINTER})
            await asyncio.sleep(2.0)
            before = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_COUNT})
            print("drafts before:", before[:120])
            sel = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_SELECT_OLD.replace("__TARGETS__", json.dumps(OLD_TEXTS))})
            print("selected:", sel[:400])
            try:
                cnt = json.loads(json.loads(sel).get("result", "{}")).get("count")
            except Exception:
                cnt = None
            if cnt != 5:
                print(f"ABORT: selected {cnt} != 5 - not deleting")
                try:
                    await call(s, "cloak_close_page", {"page_id": page})
                except Exception:
                    pass
                return
            await asyncio.sleep(1.2)
            fd = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_FIND_DELETE})
            print("delete controls:", fd[:400])
            dl = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_CLICK_DELETE})
            print("delete click:", dl[:200])
            await asyncio.sleep(1.5)
            cf = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_CONFIRM})
            print("confirm:", cf[:200])
            await asyncio.sleep(2.5)
            after = await call(s, "cloak_evaluate", {"page_id": page, "expression": JS_COUNT})
            print("drafts after:", after[:120])
            try:
                await call(s, "cloak_close_page", {"page_id": page})
            except Exception:
                pass

asyncio.run(main())
