// Vercel Function: POST /api/lead
// Receives the newsletter ("Join the List") form and forwards it to a GoHighLevel
// inbound webhook. The webhook URL is secret-ish (anyone holding it can create
// contacts), so it lives in a Vercel environment variable, never in the repo:
//
//   GHL_WEBHOOK_URL   Vercel > Project > Settings > Environment Variables
//
// Payload sent to GHL (map these in the workflow's Inbound Webhook trigger):
//   email, source ("ghost-stories-site"), form_type ("newsletter"), page, submitted_at

const SOURCE = "ghost-stories-site";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const clean = (v, max = 500) => String(v ?? "").trim().slice(0, max);

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Method not allowed" });
  }

  const url = process.env.GHL_WEBHOOK_URL;
  if (!url) {
    console.error("lead: GHL_WEBHOOK_URL is not set");
    return res.status(500).json({ error: "Sign-up is not configured yet." });
  }

  let data = req.body || {};
  if (typeof data === "string") {
    try { data = JSON.parse(data); } catch { return res.status(400).json({ error: "Invalid request body." }); }
  }

  // Honeypot: bots fill the hidden "company" field. Pretend success.
  if (clean(data.company)) return res.status(200).json({ ok: true });

  const email = clean(data.email, 254).toLowerCase();
  if (!EMAIL_RE.test(email)) return res.status(422).json({ error: "A valid email is required." });

  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        source: SOURCE,
        form_type: clean(data.form_type, 40) || "newsletter",
        page: clean(data.page, 200),
        submitted_at: new Date().toISOString(),
      }),
    });
    if (!r.ok) {
      console.error("lead: GHL webhook responded", r.status, await r.text());
      return res.status(502).json({ error: "Could not save your sign-up." });
    }
    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error("lead: request to GHL webhook failed", err);
    return res.status(502).json({ error: "Could not reach the sign-up service." });
  }
};
