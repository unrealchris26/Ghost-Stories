"""Build every page except the homepage, reusing index.html's header, icons and footer
so the whole site stays in sync. Run from the project root after editing the nav or
footer in index.html, or any copy below:   python _source/build_pages.py

Every page gets: its own <title>, description, canonical URL, Open Graph / Twitter tags,
a visible breadcrumb + BreadcrumbList schema, and any page-specific JSON-LD.
Clean URLs: each page is written as <folder>/index.html (e.g. /faq/).
It also rewrites sitemap.xml.

To add a Haunted Las Vegas article: append a dict to ARTICLES (slug, title, desc,
date, body) and run this script. The hub page and sitemap update automatically."""
import datetime
import html as H
import json
import os
import re

SITE = "https://ghoststories.vegas"
OG_IMG = SITE + "/assets/img/og-image.jpg"
TICKETS = "https://fareharbor.com/embeds/book/1923lv/items/463120/calendar/2026/09/?flow=875034&amp;full-items=yes"
MAP_EMBED = "https://maps.google.com/maps?cid=5652075586288388436&amp;hl=en&amp;output=embed"
MAP_LINK = "https://www.google.com/maps?cid=5652075586288388436"
TODAY = datetime.date.today().isoformat()

src = open("index.html", encoding="utf-8").read()
sprite = re.search(r"  <!-- Icon sprite.*?</svg>\n", src, re.S).group(0)
chrome = re.search(r"  <!-- 1\. Utility bar -->.*?</header>\n", src, re.S).group(0)
footer = re.search(r"  <!-- 16\. Footer -->.*?</footer>\n", src, re.S).group(0)
# Section anchors on sub-pages must point back to the home page.
to_home = lambda html: re.sub(r'(<a [^>]*?href=")#', r'\g<1>/#', html)
chrome, footer = to_home(chrome), to_home(footer)

SOCIAL = """  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{url}">

  <!-- Open Graph -->
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="Ghost Stories">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{og_img}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Ghost Stories: Is Seeing Really Believing? — Kent Axell at 1923 Prohibition Bar">
  <meta property="og:locale" content="en_US">

  <!-- Twitter / X -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{og_title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{og_img}">

  <!-- Theme & icons -->
  <meta name="theme-color" content="#0B1315">
  <link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">"""
HEAD = """  <link rel="preload" href="/assets/fonts/cormorant-garamond-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/assets/css/styles.css">
  <script src="/assets/js/main.js" defer></script>"""

SITEMAP = []   # (url, lastmod, priority)


def plain(s):
    return H.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def ld(data):
    return '  <script type="application/ld+json">\n  ' + json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\n  ") + "\n  </script>"


def url_for(path):
    return SITE + "/" + (path.strip("/") + "/" if path.strip("/") else "")


def map_facade(title="Map: 1923 Prohibition Bar at Mandalay Bay, Las Vegas"):
    return f'''<div class="map-facade" data-map-facade data-src="{MAP_EMBED}" data-title="{title}">
          <button class="map-facade__btn" type="button"><svg class="icon" aria-hidden="true"><use href="#i-pin"/></svg><span>Show the map</span></button>
        </div>
        <p class="map-link"><a class="link" href="{MAP_LINK}" target="_blank" rel="noopener">Open 1923 Prohibition Bar in Google Maps</a></p>'''


NAP = """<address class="nap">
          <strong>1923 Prohibition Bar</strong><br>
          Mandalay Bay Resort &amp; Casino<br>
          3930 S Las Vegas Blvd #101<br>
          Las Vegas, NV 89119<br>
          <a href="tel:+17025868925">(702) 586-8925</a> &middot; <a href="mailto:info@1923lv.com">info@1923lv.com</a>
        </address>"""


def page(path, title, desc, h1, sub, body, crumbs=(), schemas=(), og_title="", robots="index,follow",
         og_type="website", updated="", priority="0.6", lastmod=None, main_class="legal"):
    """path: folder like 'faq' (written to faq/index.html), or a file like '404.html'."""
    is_file = path.endswith(".html")
    url = SITE + "/" + path if is_file else url_for(path)
    out = path if is_file else os.path.join(path, "index.html")
    trail = [("Home", "/")] + list(crumbs)
    crumbs_html = ""
    if crumbs:
        items = "".join(f'<li><a href="{href}">{name}</a></li>' for name, href in trail[:-1])
        crumbs_html = f'''<nav class="crumbs" aria-label="Breadcrumb"><ol>{items}<li aria-current="page">{trail[-1][0]}</li></ol></nav>'''
        schemas = list(schemas) + [{
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": plain(n), "item": SITE + hr}
                                for i, (n, hr) in enumerate(trail)],
        }]
    stamp = f'<p class="legal__updated">Last updated {updated}</p>' if updated else ""
    ld_html = "\n".join(ld(s) for s in schemas)
    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{title}</title>
  <meta name="description" content="{desc}">
{SOCIAL.format(robots=robots, url=url, og_title=og_title or title, desc=desc, og_img=OG_IMG, og_type=og_type)}
{ld_html}
{HEAD}
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
{sprite}{chrome}
  <main id="main" class="{main_class}">
    <div class="container">
      <header class="legal__head">
        {crumbs_html}
        <h1 class="h2">{h1}</h1>
        <p class="section-head__sub">{sub}</p>
        <svg class="divider" aria-hidden="true"><use href="#i-divider"/></svg>
        {stamp}
      </header>
      <div class="legal__body">
{body}
      </div>
    </div>
  </main>

{footer}</body>
</html>
"""
    if not is_file:
        os.makedirs(path, exist_ok=True)
    open(out, "w", encoding="utf-8", newline="\n").write(doc)
    if "noindex" not in robots:
        SITEMAP.append((url, lastmod or TODAY, priority))
    print("wrote", out)


# ======================================================================
# Private séances
# ======================================================================
PRIVATE = f"""        <!-- TODO: add group sizes, pricing guidance and any minimums once confirmed with the venue. -->
        <p class="lede">When the nightly show ends, the hidden chamber at 1923 Prohibition Bar can stay open for you.</p>
        <p>A private séance in Las Vegas with Kent Axell is built around your group: the stories you want to hear, the questions you bring to the table, and the occasion you are celebrating. It takes place inside 1923 Prohibition Bar, the candlelit speakeasy at Mandalay Bay Resort &amp; Casino where <a class="link" href="/">Ghost Stories</a> is performed each week.</p>

        <h2>What happens at a private séance</h2>
        <p>Your group gathers around the séance table after the public audience has gone. Kent opens with true ghost stories chosen for the room, then moves into mind reading and personal readings woven into the séance itself. Nothing is scripted to the minute: the evening follows the people at the table. Curious how a séance works? Read <a class="link" href="/haunted-las-vegas/what-happens-at-a-seance/">what happens at a séance</a>.</p>

        <h2>Who books a private séance</h2>
        <ul>
          <li><strong>Birthdays and milestone nights:</strong> a guest of honor gets a moment of their own in the séance.</li>
          <li><strong>Bachelorette and bachelor parties:</strong> a haunted night out that is intimate, adult and memorable.</li>
          <li><strong>Anniversaries and date nights:</strong> something neither of you has done before.</li>
          <li><strong>Corporate and group bookings:</strong> a Las Vegas team event that gets quiet colleagues talking, ideal for conventions and client entertaining.</li>
        </ul>

        <h2>How booking works</h2>
        <ol>
          <li>Email or call with your preferred date, group size and occasion.</li>
          <li>We reply within one business day with availability and a clear, all-in quote.</li>
          <li>Your date is confirmed once you receive written confirmation and any deposit is paid.</li>
        </ol>
        <p class="cta-row"><a class="btn btn--gold" href="mailto:info@1923lv.com?subject=Private%20S%C3%A9ance%20Inquiry">Request a Private Séance</a> <a class="btn btn--ghost" href="tel:+17025868925">Call (702) 586-8925</a></p>
        <p>Every guest must be 21 or over. See the <a class="link" href="/faq/">Ghost Stories FAQ</a> for dress code, parking and arrival details, or <a class="link" href="/about-kent-axell/">learn more about Kent Axell</a>.</p>

        <h2>Where to find us</h2>
        {NAP}
        {map_facade()}"""

page("private-seances", "Private Séances in Las Vegas | Ghost Stories at 1923 Prohibition Bar",
     "Book a private séance in Las Vegas with mentalist Kent Axell: after-hours sessions for birthdays, bachelorette parties and corporate groups at 1923 Prohibition Bar, Mandalay Bay.",
     "Private Séances in <strong>Las Vegas</strong>", "After hours at 1923 Prohibition Bar", PRIVATE,
     crumbs=[("Private Séances", "/private-seances/")], og_title="Private Séances in Las Vegas · Ghost Stories", priority="0.8")

# ======================================================================
# FAQ (homepage questions + more; FAQPage schema matches the visible text)
# ======================================================================
FAQS = [
    ("What can I expect from Ghost Stories?", "An intimate evening of true ghost stories, mind reading and psychological illusion, held in a hidden chamber inside 1923 Prohibition Bar. It is mysterious and unsettling rather than gory, and most guests laugh as often as they gasp."),
    ("Is Ghost Stories scary?", "It is unsettling, not gory. There are no jump scares and no actors in masks. The chills come from the stories and from what happens in the room, and most guests laugh as often as they gasp."),
    ("What time should I arrive for the show?", "Please arrive about 15 minutes before showtime to check in, find your seat and order a drink before the lights go down."),
    ("What are the showtimes?", "Ghost Stories plays Fridays at 6:00 PM, Saturdays at 6:00 PM and Sundays at 8:00 PM. Check the ticket calendar for current dates."),
    ("How long is the performance?", "About 100 minutes, with an intermission."),
    ("Is Ghost Stories suitable for all ages?", "Ghost Stories is for guests 21 and over. Please bring a valid photo ID, as the bar checks at the door."),
    ("What's the dress code at 1923 Prohibition Bar?", "Speakeasy smart is encouraged: dark velvet, a good jacket or something a little vintage. Anything you would wear to a nice cocktail bar is welcome."),
    ("Do I need to purchase tickets in advance?", "Yes, we recommend it. The audience is kept small, so shows often sell out. Tickets start at $79, with VIP seats and group offers available."),
    ("How many people are in the audience?", "Seating is limited to about 40 guests, so every seat is close to the séance table."),
    ("Where is the Ghost Stories show performed?", "In a secret hidden chamber inside 1923 Prohibition Bar at Mandalay Bay Resort & Casino, 3930 S Las Vegas Blvd, Las Vegas."),
    ("Where do I park at Mandalay Bay?", "Mandalay Bay has self-parking and valet on site. Check Mandalay Bay's website for current rates, and allow a few extra minutes to walk to 1923 Prohibition Bar."),
    ("Can I enjoy drinks during the show?", "Yes. 1923 Prohibition Bar serves its craft cocktails and drinks before and during the show."),
    ("Is the show interactive?", "Yes. Kent invites guests to take part in mind reading and the séance. Volunteers are always invited, never forced, and you can simply watch if you prefer."),
    ("Are the ghosts real?", "Ghost Stories is theatrical entertainment. Kent Axell blends true stories with psychological illusion and suggestion, and does not claim supernatural powers. Whether you leave a believer or a skeptic is up to you."),
    ("Can I book a private séance?", 'Yes. Private séances run after hours for small groups, from birthdays and bachelorette parties to corporate teams. See <a class="link" href="/private-seances/">private séances in Las Vegas</a> for how booking works.'),
    ("Can I get a refund on my ticket?", "Public tickets are sold through our ticketing partner, and its refund and exchange policy applies. If a performance is cancelled you will be offered a new date or a refund."),
]
faq_items = "\n".join(f'''          <details class="qa">
            <summary>{q}<svg class="icon" aria-hidden="true"><use href="#i-chevron"/></svg></summary>
            <div class="qa__body"><p>{a}</p></div>
          </details>''' for q, a in FAQS)
FAQ_BODY = f"""        <!-- TODO: confirm arrival time, parking and refund wording with the venue. -->
        <p class="lede">Everything you need to know before your night at Ghost Stories Las Vegas.</p>
        <div class="faq__list faq__list--page">
{faq_items}
        </div>
        <p>Still have a question? Email <a class="link" href="mailto:info@1923lv.com">info@1923lv.com</a> or call <a class="link" href="tel:+17025868925">(702) 586-8925</a>.</p>
        <p class="cta-row"><a class="btn btn--gold" href="{TICKETS}" target="_blank" rel="noopener" data-tickets>Get Tickets</a></p>"""
faq_schema = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": plain(q), "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in FAQS]}
page("faq", "Ghost Stories FAQ: Tickets, Dress Code & Parking | Las Vegas Séance Show",
     "Answers about Ghost Stories Las Vegas: is it scary, the dress code at 1923 Prohibition Bar, age limit, showtimes, parking at Mandalay Bay and private séances.",
     "Questions <strong>Answered</strong>", "Ghost Stories FAQ", FAQ_BODY,
     crumbs=[("FAQ", "/faq/")], schemas=[faq_schema], og_title="Ghost Stories FAQ · Las Vegas Séance Show", priority="0.7")

# ======================================================================
# About Kent Axell
# ======================================================================
ABOUT = f"""        <!-- TODO: add Kent's real background: where he trained, career highlights, press and past shows. Nothing below invents credits. -->
        <figure class="about-portrait">
          <img src="/assets/img/medium-kent-axell-portrait.webp" width="820" height="1334" loading="lazy" decoding="async"
               alt="Kent Axell, Las Vegas mentalist and psychological illusionist, holding an ornate silver skull">
        </figure>
        <p class="lede">Kent Axell has spent his career studying the moment a person decides something is real.</p>
        <p>A psychological illusionist and mentalist based in Las Vegas, Kent blends psychological intuition, misdirection and storytelling into experiences that feel impossible and deeply personal at the same time. His performances are built for small rooms, where every guest can see exactly what happens and still cannot explain it.</p>

        <h2>Creator of Ghost Stories</h2>
        <p>In <a class="link" href="/">Ghost Stories: Is Seeing Really Believing?</a> Kent turns that craft toward the oldest question there is. What happens when a story is told so well, in a room so dark, that you stop asking whether it is true? The show pairs true ghost stories with mind reading and a séance, performed for about 40 guests in a hidden chamber at 1923 Prohibition Bar inside Mandalay Bay.</p>
        <p>Every performance is different, because every audience brings its own ghosts.</p>

        <h2>Private séances and events</h2>
        <p>Kent also leads after-hours <a class="link" href="/private-seances/">private séances in Las Vegas</a> for birthdays, bachelorette parties, anniversaries and corporate groups, shaped around the people at the table.</p>

        <h2>See Kent live in Las Vegas</h2>
        <p>Ghost Stories plays Fridays and Saturdays at 6:00 PM and Sundays at 8:00 PM. <a class="link" href="/faq/">Read the FAQ</a> before your visit, or explore the stories behind the show in <a class="link" href="/haunted-las-vegas/">Haunted Las Vegas</a>.</p>
        <p class="cta-row"><a class="btn btn--gold" href="{TICKETS}" target="_blank" rel="noopener" data-tickets>Get Tickets</a></p>"""
person = {
    "@context": "https://schema.org", "@type": "Person", "@id": SITE + "/about-kent-axell/#person",
    "name": "Kent Axell", "jobTitle": "Psychological Illusionist",
    "description": "Las Vegas mentalist and psychological illusionist, creator of Ghost Stories: Is Seeing Really Believing?",
    "url": SITE + "/about-kent-axell/", "image": SITE + "/assets/img/medium-kent-axell-portrait.webp",
    "worksFor": {"@id": SITE + "/#organization"},
    "homeLocation": {"@type": "Place", "name": "Las Vegas, NV"},
    # TODO: add Kent's own social profiles to sameAs
}
page("about-kent-axell", "Kent Axell | Las Vegas Mentalist & Creator of Ghost Stories",
     "Meet Kent Axell, the Las Vegas mentalist and psychological illusionist behind Ghost Stories, the séance show at 1923 Prohibition Bar inside Mandalay Bay.",
     "Kent Axell, <strong>Las Vegas Mentalist</strong>", "Psychological illusionist, creator of Ghost Stories", ABOUT,
     crumbs=[("About Kent Axell", "/about-kent-axell/")], schemas=[person], og_title="Kent Axell · Las Vegas Mentalist", og_type="profile", priority="0.7")

# ======================================================================
# Haunted Las Vegas: hub + articles (drafts)
# ======================================================================
ARTICLES = [
    {
        "slug": "the-real-haunted-history-of-las-vegas",
        "title": "The Real Haunted History of Las Vegas",
        "desc": "From the mob era to the Strip's oldest legends: a short guide to the haunted history of Las Vegas and the stories locals still tell.",
        "date": "2026-09-30",
        "body": """        <p class="lede">Las Vegas is a young city with an old habit of keeping secrets.</p>
        <p>The city began in 1905 as a railroad stop in the Mojave Desert. Within a few decades it had become a place people came to reinvent themselves, and sometimes to disappear. That mix of fortune, risk and reinvention is exactly the kind of ground ghost stories grow in.</p>

        <h2>The mob era</h2>
        <p>The Flamingo, opened in 1946 by Benjamin "Bugsy" Siegel, helped turn a desert town into the Las Vegas Strip. Siegel was killed in Beverly Hills the following year, and according to local legend, some guests and staff say they have felt his presence near the hotel's garden ever since.</p>
        <p>Downtown, the former federal courthouse and post office, completed in 1933, is now the Mob Museum. The building once hosted hearings into organized crime, and it is a favourite stop for anyone chasing the city's darker history.</p>

        <h2>Haunted Las Vegas today</h2>
        <p>Las Vegas even has a museum dedicated to the paranormal: Zak Bagans' The Haunted Museum, which opened in 2017 in a historic house near downtown. Its collection of reportedly haunted objects draws visitors who come to test their nerves.</p>
        <p>For a more intimate encounter, <a class="link" href="/">Ghost Stories</a> brings true ghost stories into a candlelit speakeasy at Mandalay Bay, where mentalist <a class="link" href="/about-kent-axell/">Kent Axell</a> invites the audience to decide for themselves what is real.</p>""",
    },
    {
        "slug": "what-happens-at-a-seance",
        "title": "What Happens at a Séance?",
        "desc": "Candles, a circle of hands and a question for the other side: what really happens at a séance, where the tradition came from, and what to expect at Ghost Stories.",
        "date": "2026-09-30",
        "body": """        <p class="lede">A séance is, at heart, a group of people sitting in the dark, agreeing to listen.</p>
        <p>The word comes from the French for "a sitting". Modern séances trace back to 1848, when the Fox sisters of Hydesville, New York claimed to communicate with a spirit through a series of knocks. Their story launched the Spiritualist movement, and within a few years séance circles were meeting in parlours across America and Europe.</p>

        <h2>Why séances boomed in the 1920s</h2>
        <p>After the First World War and the 1918 flu pandemic, millions of families were grieving, and interest in contacting the dead surged. Mediums filled theatres and private rooms alike. The magician Harry Houdini spent much of the 1920s investigating mediums and exposing fraudulent ones, and after his death in 1926 his wife held a séance for him every Halloween for a decade.</p>

        <h2>What a séance looks like</h2>
        <ul>
          <li>Guests sit in a circle, often with hands joined or resting on the table.</li>
          <li>The room is dimmed, usually lit by candles.</li>
          <li>A medium or host guides the group, asking questions and interpreting what follows.</li>
        </ul>

        <h2>The séance at Ghost Stories</h2>
        <p>At <a class="link" href="/">Ghost Stories</a> in Las Vegas, the séance is theatre: a blend of true stories, psychological illusion and audience participation led by <a class="link" href="/about-kent-axell/">Kent Axell</a>. No one is forced to take part, and the only thing you need to bring is curiosity. Groups can also book a <a class="link" href="/private-seances/">private séance</a> after hours.</p>""",
    },
    {
        "slug": "speakeasies-spirits-and-the-1920s",
        "title": "Speakeasies, Spirits and the 1920s",
        "desc": "Why the Prohibition era and the séance craze went hand in hand, and how 1923 Prohibition Bar at Mandalay Bay brings that world back to Las Vegas.",
        "date": "2026-09-30",
        "body": """        <p class="lede">In the 1920s, two kinds of spirits were forbidden, and people went looking for both behind closed doors.</p>
        <p>National Prohibition began in 1920 and lasted until 1933. Bars went underground as speakeasies: hidden rooms behind unmarked doors, where you needed the right word to get in. At the same time, séances were at the height of their popularity. Both offered the same thrill: something secret, a little dangerous, and shared only with the people in the room.</p>

        <h2>Las Vegas during Prohibition</h2>
        <p>Early Las Vegas was never quite as dry as the law intended. Downtown's Block 16 was known for its saloons, and drinking carried on there through the Prohibition years. The city's reputation for looking the other way started early.</p>

        <h2>1923 Prohibition Bar</h2>
        <p>Today, 1923 Prohibition Bar inside Mandalay Bay recreates that world: velvet booths, vintage films and craft cocktails, tucked away from the casino floor. It is also home to <a class="link" href="/">Ghost Stories</a>, where a hidden chamber inside the bar becomes a séance room for about 40 guests.</p>
        <p>Read the <a class="link" href="/faq/">Ghost Stories FAQ</a> to plan your visit, including the dress code (speakeasy smart is encouraged).</p>""",
    },
]

for a in ARTICLES:
    art_url = SITE + f"/haunted-las-vegas/{a['slug']}/"
    article_schema = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": a["title"], "description": a["desc"],
        "image": [OG_IMG], "datePublished": a["date"], "dateModified": a["date"],
        "author": {"@type": "Organization", "name": "Ghost Stories", "url": SITE + "/"},
        "publisher": {"@id": SITE + "/#organization"},
        "mainEntityOfPage": art_url,
    }
    nice_date = datetime.date.fromisoformat(a["date"]).strftime("%B %-d, %Y") if os.name != "nt" else datetime.date.fromisoformat(a["date"]).strftime("%B %d, %Y").replace(" 0", " ")
    body = f"""        <!-- TODO: DRAFT article. Review and fact-check before launch. -->
        <p class="article-meta">Published {nice_date} &middot; Haunted Las Vegas</p>
{a["body"]}
        <p class="cta-row"><a class="btn btn--gold" href="{TICKETS}" target="_blank" rel="noopener" data-tickets>Get Tickets</a> <a class="btn btn--ghost" href="/haunted-las-vegas/">More Haunted Las Vegas</a></p>"""
    page(f"haunted-las-vegas/{a['slug']}", f"{a['title']} | Haunted Las Vegas | Ghost Stories", a["desc"],
         a["title"], "Haunted Las Vegas", body,
         crumbs=[("Haunted Las Vegas", "/haunted-las-vegas/"), (a["title"], f"/haunted-las-vegas/{a['slug']}/")],
         schemas=[article_schema], og_type="article", priority="0.6", lastmod=a["date"])

hub_items = "\n".join(f'''          <li class="article-list__item">
            <h2><a href="/haunted-las-vegas/{a['slug']}/">{a['title']}</a></h2>
            <p>{a['desc']}</p>
            <p><a class="link" href="/haunted-las-vegas/{a['slug']}/">Read “{a['title']}”</a></p>
          </li>''' for a in ARTICLES)
HUB = f"""        <!-- TODO: DRAFT hub. Articles below are drafts for review. -->
        <p class="lede">True stories, séance history and the haunted side of Las Vegas, from the team behind <a class="link" href="/">Ghost Stories</a>.</p>
        <ul class="article-list">
{hub_items}
        </ul>"""
hub_schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Haunted Las Vegas", "url": SITE + "/haunted-las-vegas/",
              "hasPart": [{"@type": "Article", "headline": a["title"], "url": SITE + f"/haunted-las-vegas/{a['slug']}/"} for a in ARTICLES]}
page("haunted-las-vegas", "Haunted Las Vegas: Ghost Stories, Séances & Speakeasy History",
     "Explore haunted Las Vegas: real ghost stories, séance history and the speakeasy era, from the team behind Ghost Stories at 1923 Prohibition Bar, Mandalay Bay.",
     "Haunted <strong>Las Vegas</strong>", "Stories from the other side", HUB,
     crumbs=[("Haunted Las Vegas", "/haunted-las-vegas/")], schemas=[hub_schema], og_title="Haunted Las Vegas · Ghost Stories", priority="0.7")

# ======================================================================
# Legal
# ======================================================================
PRIVACY = """        <!-- TODO: have this reviewed by counsel before launch. -->
        <p>This policy explains what personal information Kent Axell ("we", "us") collects through this website, why, and what you can do about it. It covers the Ghost Stories website and the forms on it.</p>

        <h2>What we collect</h2>
        <ul>
          <li><strong>Enquiries you send us:</strong> your name, email address, phone number and anything you include about your event, when you email or call about a private séance or group booking.</li>
          <li><strong>Newsletter sign-ups:</strong> your email address.</li>
          <li><strong>Technical data:</strong> our host keeps standard server logs (IP address, browser type, pages requested) for security and reliability.</li>
        </ul>
        <p>We do not use advertising cookies or cross-site tracking on this website. Maps are only loaded from Google when you choose to show them.</p>

        <h2>How we use it</h2>
        <ul>
          <li>To reply to your enquiry, prepare a quote and arrange a booking.</li>
          <li>To send the newsletter you asked for: new dates, secret shows and related news.</li>
          <li>To keep the website secure and working.</li>
        </ul>
        <p>Our legal basis is your consent (newsletter), the steps needed to enter into a booking with you (enquiries), and our legitimate interest in running a secure website (logs).</p>

        <h2>Who processes it</h2>
        <ul>
          <li><strong>HighLevel / LeadConnector</strong> stores enquiries and newsletter contacts in our customer relationship system.</li>
          <li><strong>Vercel</strong> hosts the website and runs the form handler that passes your details to HighLevel.</li>
        </ul>
        <p>We never sell your personal information or share it with anyone else for their marketing. Ticket purchases are handled by the venue or its ticketing partner under their own privacy policy.</p>

        <h2>How long we keep it</h2>
        <p>Enquiries are kept for up to three years after our last contact with you, so we can recognise repeat bookings. Newsletter contacts are kept until you unsubscribe. Server logs are kept for a short period set by our host.</p>

        <h2>Your rights</h2>
        <p>You can ask to see, correct or delete the information we hold about you, or object to how we use it. You can unsubscribe from the newsletter at any time with the link in every email. Depending on where you live (for example California or the EU/UK), you may have further rights under local law. We will respond within 30 days.</p>

        <h2>Age</h2>
        <p>Ghost Stories is for guests aged 21 and over. This website is not directed at children and we do not knowingly collect their information.</p>

        <h2>Contact</h2>
        <p>Email <a href="mailto:info@1923lv.com">info@1923lv.com</a> or call <a href="tel:+17025868925">(702) 586-8925</a> with any privacy question or request.</p>

        <h2>Changes</h2>
        <p>If this policy changes, the new version will be posted here with a new date at the top.</p>"""

TERMS = """        <!-- TODO: have this reviewed by counsel and the venue before launch. -->
        <p>These terms apply to your use of this website and to enquiries and bookings made through it. By using the site you agree to them.</p>

        <h2>The show</h2>
        <p>Ghost Stories is a work of theatrical entertainment. It combines storytelling, psychological illusion, suggestion and showmanship. Kent Axell does not claim to possess supernatural or psychic powers, and nothing in the show should be taken as a real séance or as medical, legal, financial or psychological advice.</p>

        <h2>Tickets</h2>
        <ul>
          <li>Public tickets are sold by the venue or its ticketing partner, and their terms of sale, refund and exchange policies apply.</li>
          <li>Show times, running times and the programme may change. If a performance is cancelled you will be offered a new date or a refund through the point of sale.</li>
          <li>Latecomers may be seated at a suitable moment, or not at all, so the room is not disturbed.</li>
        </ul>

        <h2>Age and conduct</h2>
        <ul>
          <li>All guests must be 21 or over and carry valid photo ID.</li>
          <li>Please drink responsibly. The venue may refuse entry or service at its discretion.</li>
          <li>Guests who disrupt the performance may be asked to leave without a refund.</li>
        </ul>

        <h2>Audience participation</h2>
        <p>Volunteers are invited, never required. If you join Kent on stage or at the table you agree to take part in good faith and to follow his instructions for your comfort and safety. You may stop at any time.</p>

        <h2>Photography and recording</h2>
        <p>Personal photography during the performance is not permitted unless announced. The show may be photographed or filmed for promotional use; if you would rather not appear, tell a member of staff before the show.</p>

        <h2>Private séances and group bookings</h2>
        <p>Quotes sent after an enquiry are valid for 14 days. A booking is confirmed only when you receive written confirmation and any deposit has been paid. Cancellation terms are set out in each booking confirmation.</p>

        <h2>Website content</h2>
        <p>All text, photography, video and design on this website belong to Kent Axell or are used with permission. Please do not copy or reuse them without written consent. Reviews are quoted from public Google reviews.</p>

        <h2>Liability</h2>
        <p>We work to keep this website accurate but provide it "as is". To the extent permitted by law, we are not liable for indirect losses arising from use of the site. Nothing in these terms limits rights you have as a consumer.</p>

        <h2>Contact</h2>
        <p>Questions about these terms: <a href="mailto:info@1923lv.com">info@1923lv.com</a>.</p>"""

page("privacy", "Privacy Policy | Ghost Stories | 1923 Prohibition Bar, Las Vegas",
     "How Kent Axell collects, uses and protects personal information submitted through the Ghost Stories website.",
     "Privacy <strong>Policy</strong>", "What we keep, and why", PRIVACY, crumbs=[("Privacy Policy", "/privacy/")],
     og_title="Privacy Policy · Ghost Stories", updated="September 30, 2026", priority="0.2", lastmod="2026-09-30")
page("terms", "Terms &amp; Conditions | Ghost Stories | 1923 Prohibition Bar, Las Vegas",
     "Terms for using the Ghost Stories website and booking the show, private séances and group events.",
     "Terms &amp; <strong>Conditions</strong>", "The fine print, by candlelight", TERMS, crumbs=[("Terms &amp; Conditions", "/terms/")],
     og_title="Terms &amp; Conditions · Ghost Stories", updated="September 28, 2026", priority="0.2", lastmod="2026-09-28")

NOT_FOUND = f"""        <p class="lede center">Whatever was here has crossed over.</p>
        <p class="center">The page you were looking for doesn’t exist, or it only appears after midnight. Try one of these instead:</p>
        <ul class="link-list">
          <li><a class="link" href="/">Ghost Stories: the Las Vegas séance show</a></li>
          <li><a class="link" href="/#showtimes">Showtimes and tickets</a></li>
          <li><a class="link" href="/private-seances/">Private séances in Las Vegas</a></li>
          <li><a class="link" href="/faq/">Frequently asked questions</a></li>
          <li><a class="link" href="/haunted-las-vegas/">Haunted Las Vegas</a></li>
        </ul>
        <p class="center"><a class="btn btn--gold" href="/">Return to the Séance</a></p>"""
page("404.html", "Page Not Found | Ghost Stories", "This page has passed to the other side.",
     "This page has passed to <strong>the other side</strong>", "Error 404", NOT_FOUND, robots="noindex")

# ======================================================================
# sitemap.xml (homepage first)
# ======================================================================
home_mod = datetime.date.fromtimestamp(os.path.getmtime("index.html")).isoformat()
rows = [(SITE + "/", home_mod, "1.0")] + SITEMAP
xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
xml += "".join(f"  <url><loc>{u}</loc><lastmod>{m}</lastmod><priority>{pr}</priority></url>\n" for u, m, pr in rows)
xml += "</urlset>\n"
open("sitemap.xml", "w", encoding="utf-8", newline="\n").write(xml)
print("wrote sitemap.xml with", len(rows), "URLs")
