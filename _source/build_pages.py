"""Regenerate privacy.html, terms.html and 404.html so their header, icons and
footer stay in sync with index.html. Run from the project root after editing
the nav or footer in index.html:  python _source/build_pages.py"""
import re

src = open("index.html", encoding="utf-8").read()
SITE = "https://ghoststories.vegas"
OG_IMG = SITE + "/assets/img/og-image.jpg"
SOCIAL = """  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{url}">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
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
sprite = re.search(r"  <!-- Icon sprite.*?</svg>\n", src, re.S).group(0)
chrome = re.search(r"  <!-- 1\. Utility bar -->.*?</header>\n", src, re.S).group(0)
footer = re.search(r"  <!-- 16\. Footer -->.*?</footer>\n", src, re.S).group(0)
# Section anchors on sub-pages must point back to the home page.
to_home = lambda html: re.sub(r'(<a [^>]*?href=")#', r'\g<1>/#', html)
chrome, footer = to_home(chrome), to_home(footer)
footer = re.sub(r'\s*<div class="planchette".*?</p>\s*</div>\n', "\n", footer, flags=re.S)


def page(fname, title, desc, heading, sub, updated, body, robots="index,follow", og_title=""):
    stamp = f'<p class="legal__updated">Last updated {updated}</p>' if updated else ""
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{title}</title>
  <meta name="description" content="{desc}">
{SOCIAL.format(robots=robots, url=SITE + "/" + ("" if fname == "index.html" else fname), og_title=og_title or title, desc=desc, og_img=OG_IMG)}
{HEAD}
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
{sprite}{chrome}
  <main id="main" class="legal">
    <div class="container">
      <header class="legal__head">
        <h1 class="h2">{heading}</h1>
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
    open(fname, "w", encoding="utf-8", newline="\n").write(html)
    print("wrote", fname)


PRIVACY = """        <!-- TODO: have this reviewed by counsel before launch. -->
        <p>This policy explains what personal information Kent Axell ("we", "us") collects through this website, why, and what you can do about it. It covers the Ghost Stories website and the forms on it.</p>

        <h2>What we collect</h2>
        <ul>
          <li><strong>Booking and séance enquiries:</strong> your name, email address, phone number (optional), event date, type of event, and anything you write in the message field.</li>
          <li><strong>Newsletter sign-ups:</strong> your email address.</li>
          <li><strong>Technical data:</strong> our host keeps standard server logs (IP address, browser type, pages requested) for security and reliability.</li>
        </ul>
        <p>We do not use advertising cookies or cross-site tracking on this website.</p>

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

NOT_FOUND = """        <p class="lede center">Whatever was here has crossed over.</p>
        <p class="center">The page you were looking for doesn’t exist, or it only appears after midnight.</p>
        <p class="center"><a class="btn btn--gold" href="/">Return to the Séance</a></p>"""

page("privacy.html", "Privacy Policy | Ghost Stories | 1923 Prohibition Bar, Las Vegas",
     "How Kent Axell collects, uses and protects personal information submitted through the Ghost Stories website.",
     "Privacy <strong>Policy</strong>", "What we keep, and why", "September 28, 2026", PRIVACY, og_title="Privacy Policy · Ghost Stories")
page("terms.html", "Terms &amp; Conditions | Ghost Stories | 1923 Prohibition Bar, Las Vegas",
     "Terms for using the Ghost Stories website and booking the show, private séances and group events.",
     "Terms &amp; <strong>Conditions</strong>", "The fine print, by candlelight", "September 28, 2026", TERMS, og_title="Terms &amp; Conditions · Ghost Stories")
page("404.html", "Page Not Found | Ghost Stories", "This page has crossed over.",
     "Nothing <strong>Here</strong>", "Error 404", "", NOT_FOUND, robots="noindex")
