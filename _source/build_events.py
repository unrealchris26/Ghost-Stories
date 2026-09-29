"""Rewrite the homepage's TheaterEvent JSON-LD with the next few weeks of individual
performances. Google's event rich results need a specific startDate per show, so a
weekly "eventSchedule" alone is not enough.

Run from the project root, and re-run at least monthly (or before each deploy) so the
listed dates stay in the future:   python _source/build_events.py

Edit SHOWS / WEEKS / PRICE below when the schedule or price changes."""
import datetime as dt
import json
import re

SITE = "https://ghoststories.vegas"
TICKETS = "https://fareharbor.com/embeds/book/1923lv/items/463120/calendar/2026/09/?flow=875034&full-items=yes"
SHOWS = {4: "18:00", 5: "18:00", 6: "20:00"}   # weekday (Mon=0): start time  -> Fri 6pm, Sat 6pm, Sun 8pm
DURATION_MIN = 100
WEEKS = 6
PRICE = "79"


def nth_sunday(year, month, n):
    d = dt.date(year, month, 1)
    d += dt.timedelta(days=(6 - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def las_vegas_offset(day):
    """US Pacific time: daylight time from the 2nd Sunday of March to the 1st Sunday of November."""
    return "-07:00" if nth_sunday(day.year, 3, 2) <= day < nth_sunday(day.year, 11, 1) else "-08:00"


venue = {
    "@type": "Place", "name": "1923 Prohibition Bar",
    "address": {"@type": "PostalAddress", "streetAddress": "3930 S Las Vegas Blvd #101, Mandalay Bay Resort & Casino",
                "addressLocality": "Las Vegas", "addressRegion": "NV", "postalCode": "89119", "addressCountry": "US"},
}
today = dt.date.today()
events = []
for i in range(1, WEEKS * 7 + 1):
    day = today + dt.timedelta(days=i)
    if day.weekday() not in SHOWS:
        continue
    h, m = map(int, SHOWS[day.weekday()].split(":"))
    start = dt.datetime.combine(day, dt.time(h, m))
    end = start + dt.timedelta(minutes=DURATION_MIN)
    off = las_vegas_offset(day)
    events.append({
        "@context": "https://schema.org",
        "@type": "TheaterEvent",
        "name": "Ghost Stories: Is Seeing Really Believing?",
        "description": "An intimate evening of true ghost stories, psychological illusion, and a séance with Kent Axell at 1923 Prohibition Bar inside Mandalay Bay, Las Vegas. Ages 21+.",
        "startDate": start.strftime("%Y-%m-%dT%H:%M") + off,
        "endDate": end.strftime("%Y-%m-%dT%H:%M") + off,
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "typicalAgeRange": "21-",
        "url": SITE + "/",
        "image": [SITE + "/assets/img/og-image.jpg"],
        "location": venue,
        "performer": {"@type": "Person", "name": "Kent Axell", "url": SITE + "/about-kent-axell/"},
        "organizer": {"@type": "Organization", "name": "Ghost Stories", "url": SITE + "/"},
        # TODO: ticket URL (currently the FareHarbor booking calendar)
        "offers": {"@type": "Offer", "url": TICKETS, "price": PRICE, "priceCurrency": "USD",
                   "availability": "https://schema.org/InStock", "validFrom": today.isoformat()},
    })

block = '  <script type="application/ld+json">\n  ' + json.dumps(events, ensure_ascii=False, indent=2).replace("\n", "\n  ") + "\n  </script>"
p = "index.html"
h = open(p, encoding="utf-8").read()
h, n = re.subn(r'  <script type="application/ld\+json">\n(?:(?!</script>).)*?"TheaterEvent"(?:(?!</script>).)*?</script>', lambda m: block, h, count=1, flags=re.S)
if n != 1:
    raise SystemExit("TheaterEvent block not found in index.html")
open(p, "w", encoding="utf-8", newline="\n").write(h)
print(f"wrote {len(events)} performances: {events[0]['startDate']} ... {events[-1]['startDate']}")
