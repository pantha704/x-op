const rnd = (a, b) => a + Math.floor(Math.random() * (b - a));
async function fastReply(url, text) {
  await tools["cloakbrowsermcp"].cloak_navigate({ page_id: "page_edbf6bbe", url });
  await tools["cloakbrowsermcp"].cloak_wait({ page_id: "page_edbf6bbe", timeout_ms: rnd(4000, 5500) });
  const js = `(async () => {
    const sleep = ms => new Promise(res => setTimeout(res, ms));
    const a = document.querySelector('article[data-testid="tweet"]');
    if (!a) return 'no-article';
    if (!a.querySelector('[data-testid="unlike"]')) { const l = a.querySelector('[data-testid="like"]'); if (l) l.click(); }
    await sleep(400);
    const box = document.querySelector('[data-testid="tweetTextarea_0"], div[role="textbox"]');
    if (!box) return 'no-box';
    box.focus();
    document.execCommand('insertText', false, ` + JSON.stringify(text) + `);
    await sleep(450);
    const btns = [...document.querySelectorAll('button')].filter(b => (b.innerText||'').trim() === 'Reply' && !b.disabled);
    const btn = btns[btns.length - 1];
    if (!btn) return 'no-btn';
    btn.click();
    await sleep(3000);
    const errToast = /Something went wrong/i.test(document.body.textContent||'');
    const boxNow = document.querySelector('[data-testid="tweetTextarea_0"]');
    const cleared = !boxNow || !boxNow.textContent.trim();
    if (errToast) return 'THROTTLED';
    return cleared ? 'hit' : 'uncertain';
  })()`;
  let r = await tools["cloakbrowsermcp"].cloak_evaluate({ page_id: "page_edbf6bbe", expression: js });
  await tools["cloakbrowsermcp"].cloak_wait({ page_id: "page_edbf6bbe", timeout_ms: rnd(4000, 8000) });
  return { u: url.split('/')[3], out: r.result };
}
const t = [
  ["https://x.com/14aehyun/status/2101582081155609074", "the eyebrow raise should be illegal in at least 12 countries"],
  ["https://x.com/sunloverhuh/status/2101548553076187352", "the fancam that broke the timeline"],
  ["https://x.com/AnimeDailyRepz/status/2101538230382268678", "health first, the series can wait, we will be here"],
  ["https://x.com/cortis_C00kie09/status/2101528649921106403", "the adaptation pipeline in one image"],
  ["https://x.com/ianpicts/status/2101540054858613119", "the real life buff is unfair"],
  ["https://x.com/jakeyclub/status/2101581617571487895", "the whole family in stem, jake chose chaos instead"]
];
const results = [];
for (const [url, text] of t) {
  const r = await fastReply(url, text);
  results.push(r);
  if (r.out === 'THROTTLED') break;
}
return results;