// Netlify Function: receives the booking and newsletter forms and upserts the
// contact into GoHighLevel (LeadConnector API v2).
//
// Env vars (Netlify > Site configuration > Environment variables):
//   GHL_TOKEN        Private Integration token (or location API key) with contacts.write
//   GHL_LOCATION_ID  The sub-account / location ID
//
// Custom fields expected in GHL (Settings > Custom Fields), keyed exactly:
//   event_date, event_type, event_details

const GHL_API = "https://services.leadconnectorhq.com";
const SOURCE = "ghost-stories-site";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });

const clean = (value, max = 2000) => String(value ?? "").trim().slice(0, max);

async function readBody(req) {
  const type = req.headers.get("content-type") || "";
  if (type.includes("application/json")) return req.json();
  const form = await req.formData();
  return Object.fromEntries(form.entries());
}

export default async (req) => {
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  const { GHL_TOKEN, GHL_LOCATION_ID } = process.env;
  if (!GHL_TOKEN || !GHL_LOCATION_ID) {
    console.error("lead: GHL_TOKEN or GHL_LOCATION_ID is not set");
    return json({ error: "Form is not configured yet." }, 500);
  }

  let data;
  try {
    data = await readBody(req);
  } catch {
    return json({ error: "Invalid request body." }, 400);
  }

  // Honeypot: bots fill the hidden "company" field. Pretend success.
  if (clean(data.company)) return json({ ok: true });

  const formType = data.form_type === "newsletter" ? "newsletter" : "booking";
  const email = clean(data.email, 254).toLowerCase();
  if (!EMAIL_RE.test(email)) return json({ error: "A valid email is required." }, 422);

  const name = clean(data.name, 120);
  if (formType === "booking" && !name) return json({ error: "Name is required." }, 422);
  const [firstName = "", ...rest] = name.split(/\s+/).filter(Boolean);

  const eventDate = clean(data.event_date, 10);
  const eventType = clean(data.event_type, 60);
  const eventDetails = clean(data.event_details, 4000);

  const customFields = [
    eventDate && { key: "event_date", field_value: eventDate },
    eventType && { key: "event_type", field_value: eventType },
    eventDetails && { key: "event_details", field_value: eventDetails },
  ].filter(Boolean);

  const tags = formType === "newsletter"
    ? ["ghost-stories", "newsletter"]
    : ["ghost-stories", "booking-inquiry", eventType && `event: ${eventType.toLowerCase()}`].filter(Boolean);

  const payload = {
    locationId: GHL_LOCATION_ID,
    email,
    source: SOURCE,
    tags,
    ...(firstName && { firstName }),
    ...(rest.length && { lastName: rest.join(" ") }),
    ...(clean(data.phone) && { phone: clean(data.phone, 40) }),
    ...(customFields.length && { customFields }),
  };

  try {
    const res = await fetch(`${GHL_API}/contacts/upsert`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${GHL_TOKEN}`,
        Version: "2021-07-28",
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      console.error("lead: GHL responded", res.status, await res.text());
      return json({ error: "Could not save your message." }, 502);
    }
    return json({ ok: true });
  } catch (err) {
    console.error("lead: request to GHL failed", err);
    return json({ error: "Could not reach the booking system." }, 502);
  }
};
