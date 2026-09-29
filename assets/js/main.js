/* Ghost Stories: site behaviour. Vanilla JS, no dependencies. */
(() => {
  "use strict";

  /* ------------------------------------------------------------------
     CONFIG
     TODO: paste the ticketing link (e.g. the Mandalay Bay / 1923 box office
     page). While it is empty, every "Get Tickets" button scrolls to the
     contact form instead.
     ------------------------------------------------------------------ */
  const TICKETS_URL = "https://fareharbor.com/embeds/book/1923lv/items/463120/calendar/2026/09/?flow=875034&full-items=yes";
  const LEAD_ENDPOINT = "/api/lead";   // Vercel function: api/lead.js
  const SPEAKEASY_PASSWORD = "Houdini sent me.";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  /* Fog texture waits until everything important has loaded */
  const addFog = () => document.documentElement.classList.add("fog-ready");
  if (document.readyState === "complete") addFog(); else window.addEventListener("load", addFog, { once: true });

  /* ------------------------------------------------------------------
     Title lockups (hero, nav logo, footer logo): the subtitle spans exactly
     the width of "GHOST STORIES". Letter-spacing does the widening so the
     type keeps its height; a final scaleX corrects the last few pixels.
     Re-measured when fonts load and whenever a title changes size.
     ------------------------------------------------------------------ */
  const titleInkWidth = (title) => {
    // Widest rendered line of the title text (it wraps to two lines on phones),
    // ignoring the load-in scale animation and the trailing letter-spacing.
    const range = document.createRange();
    const walker = document.createTreeWalker(title, NodeFilter.SHOW_TEXT);
    let widest = 0;
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      range.selectNodeContents(node);
      for (const rect of range.getClientRects()) widest = Math.max(widest, rect.width);
    }
    const scale = title.offsetWidth ? title.getBoundingClientRect().width / title.offsetWidth : 1;
    const trailing = parseFloat(getComputedStyle(title).letterSpacing) || 0;
    return widest / (scale || 1) - trailing;
  };

  // All lockups are fitted together in batched read/write passes, so the page
  // lays out a handful of times per fit instead of once per style change.
  const lockups = $$("[data-lockup]").map((el) => ({
    title: $("[data-lockup-title]", el),
    sub: $("[data-lockup-sub] .lockup-fit", el),
    fittedFor: 0,
  })).filter((l) => l.title && l.sub);

  const fitAll = () => {
    // read: title widths; skip lockups whose title hasn't changed since the last fit
    const jobs = lockups
      .map((l) => ({ l, target: titleInkWidth(l.title) }))
      .filter(({ l, target }) => target > 0 && Math.abs(target - l.fittedFor) > 0.5);
    if (!jobs.length) return;
    // write: reset
    jobs.forEach(({ l }) => Object.assign(l.sub.style, { fontSize: "", letterSpacing: "0px", marginRight: "0px", transform: "", transformOrigin: "" }));
    // read: natural widths and font sizes
    jobs.forEach((job) => {
      job.natural = job.l.sub.getBoundingClientRect().width;
      job.size = parseFloat(getComputedStyle(job.l.sub).fontSize);
    });
    // write: on narrow screens the stacked title is narrower than the subtitle, so size the type down rather than squash it
    jobs.forEach((job) => {
      if (job.natural > job.target) {
        job.size = job.size * job.target / job.natural;
        job.l.sub.style.fontSize = job.size.toFixed(2) + "px";
        job.natural = job.target;
      }
      const gaps = Math.max(job.l.sub.textContent.length - 1, 1);
      job.spacing = Math.min(Math.max((job.target - job.natural) / gaps, 0), job.size * 0.9);
      job.l.sub.style.letterSpacing = job.spacing + "px";
      job.l.sub.style.marginRight = -job.spacing + "px";   // cancel the space after the last letter
    });
    // read: resulting ink widths
    jobs.forEach((job) => { job.ink = job.l.sub.getBoundingClientRect().width - job.spacing; });
    // write: a final scaleX closes the last few pixels, around the visible centre
    jobs.forEach((job) => {
      const stretch = job.target / job.ink;
      if (Math.abs(stretch - 1) > 0.002) {
        job.l.sub.style.transformOrigin = job.ink / 2 + "px 50%";
        job.l.sub.style.transform = "scaleX(" + stretch.toFixed(4) + ")";
      }
      job.l.fittedFor = job.target;
    });
  };

  if (lockups.length) {
    if ("ResizeObserver" in window) {
      // Fires once on observe, then whenever a title changes size (font swap, viewport change)
      let queued = false;
      const ro = new ResizeObserver(() => {
        if (queued) return;
        queued = true;
        requestAnimationFrame(() => { queued = false; fitAll(); });
      });
      lockups.forEach((l) => ro.observe(l.title));
    } else {
      fitAll();
      window.addEventListener("resize", fitAll);
    }
    // The subtitle font can finish loading without the title changing size, so once
    // every font is in, force one full refit regardless of the cached widths.
    if (document.fonts) document.fonts.ready.then(() => { lockups.forEach((l) => (l.fittedFor = 0)); fitAll(); });
  }

  /* Tape marquee: stretch the texture tile so a whole number of tiles fits one
     phrase list. The ticker loops by exactly one list width, so the paper, stains
     and torn edges line up at the loop point and it never visibly jumps. */
  const tape = $(".marquee--tape .marquee__track");
  if (tape) {
    const TILE_RATIO = 1600 / 150;   // width / height of assets/img/marquee-tape.webp
    const list = $(".marquee__list", tape);
    const sizeTape = () => {
      const w = list.offsetWidth, h = tape.offsetHeight;
      if (!w || !h) return;
      const tiles = Math.max(1, Math.round(w / (h * TILE_RATIO)));
      tape.style.backgroundSize = (w / tiles).toFixed(3) + "px 100%";
    };
    sizeTape();
    if ("ResizeObserver" in window) new ResizeObserver(sizeTape).observe(list);
    if (document.fonts) document.fonts.ready.then(sizeTape);
  }

  /* ------------------------------------------------------------------
     About Ghost Stories: curtain reveal, linked to scroll.
     Progress runs 0 -> 1 as the stage travels from the bottom of the screen
     to near the top. A smoothed follower gives the curtains weight, scaleX
     gathers the fabric as it opens, and a small velocity skew lets the hems
     trail. Transform-only writes; the loop runs only while the stage is near
     the screen and stops once the curtains settle.
     ------------------------------------------------------------------ */
  const stage = $("[data-curtain-stage]");
  if (stage && !reduceMotion.matches && "IntersectionObserver" in window) {
    const scene = $(".about-stage__scene", stage);
    const leftCurtain = $('[data-curtain="left"]', stage);
    const rightCurtain = $('[data-curtain="right"]', stage);
    const steps = $$("[data-stage-step]", stage);
    const THRESHOLDS = [0.4, 0.5, 0.62];                 // heading, paragraph, button (desktop)
    const phone = window.matchMedia("(max-width: 767.98px)");
    const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
    const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
    const progress = () => {
      const top = scene.getBoundingClientRect().top;
      const vh = window.innerHeight;
      return clamp((vh - top) / (vh * 0.85), 0, 1);
    };

    let current = progress();
    let near = false;
    let running = false;
    stage.classList.add("is-armed");

    // Fully open, each curtain stays as a gathered drape this wide (matches --drape in styles.css)
    let finalScale = 0.12;
    const measure = () => {
      const drape = window.innerWidth < 768 ? 16 : window.innerWidth * 0.06;
      finalScale = clamp(drape / (leftCurtain.offsetWidth || 1), 0.03, 0.3);
      // Phones: the text sits above the stage, so the curtains cover only the stage
      const top = phone.matches ? scene.offsetTop + "px" : "";
      leftCurtain.style.top = rightCurtain.style.top = top;
    };

    const render = (velocity) => {
      const e = easeInOut(current);
      const skew = clamp(velocity * 60, -1.4, 1.4);          // hems trail the pull slightly
      const scale = (1 - e * (1 - finalScale)).toFixed(4);   // fabric bunches toward its own edge
      leftCurtain.style.transform = `scaleX(${scale}) skewX(${skew.toFixed(2)}deg)`;
      rightCurtain.style.transform = `scaleX(${scale}) skewX(${(-skew).toFixed(2)}deg)`;
      if (!phone.matches) steps.forEach((el, i) => { if (e >= THRESHOLDS[i]) el.classList.add("is-shown"); });
    };

    // Time-based follow (same heavy feel at 60Hz or 120Hz); ~90% of the way in ~0.55s
    const TAU = 240;
    let last = 0;
    const tick = (now) => {
      const dt = last ? Math.min(now - last, 64) : 16;
      last = now;
      const target = near ? progress() : current;
      const prev = current;
      current += (target - current) * (1 - Math.exp(-dt / TAU));
      if (Math.abs(target - current) < 0.0002) current = target;
      render((current - prev) * (16 / dt));
      if (near || current !== target) requestAnimationFrame(tick);
      else { running = false; last = 0; }
    };

    // Phones: reveal the copy as soon as it enters the screen, independent of the curtains
    new IntersectionObserver(([entry], obs) => {
      if (!phone.matches || !entry.isIntersecting) return;
      steps.forEach((el) => el.classList.add("is-shown"));
      obs.disconnect();
    }, { rootMargin: "0px 0px -8% 0px" }).observe($(".about-stage__content", stage));

    measure();
    render(0);
    window.addEventListener("resize", () => { measure(); render(0); });
    if (document.fonts) document.fonts.ready.then(() => { measure(); render(0); });   // text height can shift the stage
    new IntersectionObserver(([entry]) => {
      near = entry.isIntersecting;
      if (near && !running) { running = true; requestAnimationFrame(tick); }
    }, { rootMargin: "120px 0px" }).observe(stage);
  }

  /* Buttons whose right edge lines up with the end of the longest text line above
     them ([data-align-end] = selector of that text block, inside the same parent). */
  const alignEnds = $$("[data-align-end]").map((wrap) => ({
    wrap, btn: wrap.firstElementChild, text: $(wrap.dataset.alignEnd, wrap.parentElement),
  })).filter((a) => a.btn && a.text);
  if (alignEnds.length) {
    const inkRight = (el) => {
      const range = document.createRange();
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      let right = 0;
      for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        if (!n.textContent.trim()) continue;
        range.selectNodeContents(n);
        for (const r of range.getClientRects()) right = Math.max(right, r.right);
      }
      return right;
    };
    const alignAll = () => {
      alignEnds.forEach((a) => (a.btn.style.marginLeft = ""));
      if (window.innerWidth < 768) return;   // phones: buttons are centred in CSS
      const reads = alignEnds.map((a) => ({ a, ink: inkRight(a.text), left: a.wrap.getBoundingClientRect().left, w: a.btn.offsetWidth }));
      reads.forEach(({ a, ink, left, w }) => { a.btn.style.marginLeft = Math.max(0, ink - left - w) + "px"; });
    };
    alignAll();
    if (document.fonts) document.fonts.ready.then(alignAll);
    if ("ResizeObserver" in window) {
      let queued = false;
      const ro = new ResizeObserver(() => { if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; alignAll(); }); } });
      alignEnds.forEach((a) => ro.observe(a.text));
    } else window.addEventListener("resize", alignAll);
  }

  /* Reviews: "Read more" only where the text is clamped; like toggle; share */
  const reviewsSection = $("#reviews");
  if (reviewsSection) {
    const syncMore = () => $$(".review", reviewsSection).forEach((r) => {
      if (r.classList.contains("is-open")) return;
      const text = $(".review__text", r);
      $(".review__more", r).toggleAttribute("data-off", text.scrollHeight <= text.clientHeight + 1);
    });
    syncMore();
    if (document.fonts) document.fonts.ready.then(syncMore);
    window.addEventListener("resize", syncMore);
    $$(".review__more", reviewsSection).forEach((btn) => btn.addEventListener("click", () => {
      const review = btn.closest(".review");
      const open = review.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", String(open));
      btn.textContent = open ? "Show less" : "Read more";
    }));
    $$(".review__like", reviewsSection).forEach((btn) => btn.addEventListener("click", () => {
      btn.setAttribute("aria-pressed", String(btn.getAttribute("aria-pressed") !== "true"));
    }));
    const REVIEWS_URL = "https://www.google.com/maps/place/Ghost+Stories+-+An+Intimate+Seance+Show/@36.0938718,-115.1760433,17z/data=!4m8!3m7!1s0x80c8c5b77abc5e0b:0xf2f57c3ba20cd418!8m2!3d36.0938718!4d-115.1760433!9m1!1b1!16s%2Fg%2F11vrwvc741";
    $$("[data-share-review]", reviewsSection).forEach((btn) => btn.addEventListener("click", async () => {
      try {
        if (navigator.share) await navigator.share({ title: "Ghost Stories reviews", url: REVIEWS_URL });
        else { await navigator.clipboard.writeText(REVIEWS_URL); btn.lastChild.textContent = "Link copied"; setTimeout(() => (btn.lastChild.textContent = "Share"), 2000); }
      } catch { /* share sheet dismissed */ }
    }));
  }

  /* Section reveals ([data-reveal-group]): children with [data-reveal] fade up in
     sequence (--d delays in the markup) the first time the section is on screen. */
  if (!reduceMotion.matches && "IntersectionObserver" in window) {
    $$("[data-reveal-group]").forEach((group) => {
      group.classList.add("is-armed");
      new IntersectionObserver(([entry], obs) => {
        if (!entry.isIntersecting) return;
        group.classList.add("is-shown");
        obs.disconnect();
      }, { threshold: 0.18 }).observe(group);
    });
  }

  /* FAQ: first five questions, "View all FAQs" reveals the rest */
  const faqToggle = $("[data-faq-toggle]");
  if (faqToggle) {
    const extra = $$("[data-faq-more]");
    faqToggle.addEventListener("click", () => {
      const open = faqToggle.getAttribute("aria-expanded") !== "true";
      extra.forEach((q) => { q.hidden = !open; if (!open) q.open = false; });
      faqToggle.setAttribute("aria-expanded", String(open));
      faqToggle.textContent = open ? "Show fewer FAQs" : "View all FAQs";
      if (open && extra[0]) $("summary", extra[0]).focus();
    });
  }

  /* Year */
  $$("[data-year]").forEach((el) => (el.textContent = new Date().getFullYear()));

  /* Tickets */
  if (TICKETS_URL) {
    $$("[data-tickets]").forEach((a) => {
      a.href = TICKETS_URL;
      a.target = "_blank";
      a.rel = "noopener";
    });
  }

  /* ------------------------------------------------------------------
     Navigation: smoky blur once the hero top leaves the viewport
     ------------------------------------------------------------------ */
  const nav = $("[data-nav]");
  const sentinel = $("[data-hero-sentinel]");
  if (nav && sentinel && "IntersectionObserver" in window) {
    new IntersectionObserver(([entry]) => {
      nav.classList.toggle("is-scrolled", !entry.isIntersecting);
    }, { rootMargin: "-72px 0px 0px 0px" }).observe(sentinel);
  } else if (nav) {
    nav.classList.add("is-scrolled");
  }

  /* Mobile menu */
  const toggle = $("[data-menu-toggle]");
  if (nav && toggle) {
    const label = $(".sr-only", toggle);
    const setOpen = (open) => {
      nav.toggleAttribute("data-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      label.textContent = open ? "Close menu" : "Open menu";
      document.documentElement.style.overflow = open ? "hidden" : "";
    };
    toggle.addEventListener("click", () => setOpen(!nav.hasAttribute("data-open")));
    $$("#site-menu a").forEach((a) => a.addEventListener("click", () => setOpen(false)));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && nav.hasAttribute("data-open")) { setOpen(false); toggle.focus(); }
    });
    window.matchMedia("(min-width: 1024px)").addEventListener("change", (e) => e.matches && setOpen(false));
  }

  /* Current section in the nav */
  const navLinks = $$("[data-nav-link]");
  const sections = navLinks.map((a) => a.getAttribute("href")).filter((h) => h.startsWith("#")).map((h) => $(h)).filter(Boolean);   // on sub-pages links are "/#top" etc.: nothing to track
  if (sections.length && "IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        navLinks.forEach((a) => a.setAttribute("aria-current", String(a.getAttribute("href") === "#" + entry.target.id)));
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    sections.forEach((s) => io.observe(s));
  }

  /* ------------------------------------------------------------------
     Materialize: headings resolve from blur, word by word.
     Ported from the 21st.dev "Text Blur Reveal" component (React + Motion)
     to WAAPI. Keeps nested <strong> so the mixed-weight trick survives.
     ------------------------------------------------------------------ */
  const splitWords = (node) => {
    [...node.childNodes].forEach((child) => {
      if (child.nodeType === Node.TEXT_NODE) {
        const frag = document.createDocumentFragment();
        child.textContent.split(/(\s+)/).forEach((part) => {
          if (!part) return;
          if (/^\s+$/.test(part)) { frag.append(part); return; }
          const span = document.createElement("span");
          span.className = "mat-word mat-pending";
          span.textContent = part;
          frag.append(span);
        });
        child.replaceWith(frag);
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        splitWords(child);
      }
    });
  };

  const materialize = (el) => {
    $$(".mat-word", el).forEach((word, i) => {
      word.classList.remove("mat-pending");
      word.animate(
        [
          { opacity: 0, filter: "blur(10px)", transform: "translateY(-12px)" },
          { opacity: 0.5, filter: "blur(5px)", transform: "translateY(2px)", offset: 0.5 },
          { opacity: 1, filter: "blur(0px)", transform: "none" },
        ],
        { duration: 1000, delay: i * 90, easing: "cubic-bezier(0.23, 1, 0.32, 1)", fill: "backwards" }
      );
    });
  };

  const matTargets = $$("[data-materialize]");
  if (!reduceMotion.matches && "IntersectionObserver" in window && Element.prototype.animate) {
    matTargets.forEach(splitWords);
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        obs.unobserve(entry.target);
        materialize(entry.target);
      });
    }, { threshold: 0.35 });
    matTargets.forEach((el) => io.observe(el));
  }

  /* ------------------------------------------------------------------
     Séance quote: spelled out letter by letter, as if by planchette
     ------------------------------------------------------------------ */
  const spell = $("[data-spell]");
  if (spell && !reduceMotion.matches && "IntersectionObserver" in window) {
    const text = spell.textContent;
    spell.textContent = "";
    const readable = document.createElement("span");   // screen readers get the whole quote at once
    readable.className = "sr-only";
    readable.textContent = text;
    spell.append(readable);
    const chars = [...text].map((ch) => {
      const s = document.createElement("span");
      s.className = "spell-char";
      s.setAttribute("aria-hidden", "true");
      s.textContent = ch;
      spell.append(s);
      return s;
    });
    new IntersectionObserver(([entry], obs) => {
      if (!entry.isIntersecting) return;
      obs.disconnect();
      let i = 0;
      const next = () => {
        if (i >= chars.length) return;
        const c = chars[i++];
        c.classList.add("is-on");
        setTimeout(() => c.classList.add("is-settled"), 700);
        // spirits hesitate at spaces and punctuation
        const pause = /[\s]/.test(c.textContent) ? 110 : /[.,…?!]/.test(c.textContent) ? 260 : 38 + Math.random() * 40;
        setTimeout(next, pause);
      };
      next();
    }, { threshold: 0.6 }).observe(spell);
  }

  /* ------------------------------------------------------------------
     Video dialog (trailer + clips)
     ------------------------------------------------------------------ */
  const dialog = $("[data-video-dialog]");
  if (dialog && typeof dialog.showModal === "function") {
    const video = $("[data-video]", dialog);
    const title = $("[data-video-title]", dialog);
    $$("[data-video-open]").forEach((btn) => {
      const open = () => {
        video.src = btn.dataset.videoSrc;
        title.textContent = btn.dataset.videoTitle || "";
        dialog.showModal();
        video.play().catch(() => {});
      };
      btn.addEventListener("click", () => {
        if (!("videoLaunch" in btn.dataset) || reduceMotion.matches) { dialog.classList.remove("is-from-origin"); open(); return; }
        // Play button: ring burst, then the player grows out of the button
        btn.classList.remove("is-launching"); void btn.offsetWidth; btn.classList.add("is-launching");
        setTimeout(() => {
          const b = btn.getBoundingClientRect();
          dialog.classList.add("is-from-origin");
          open();
          const d = dialog.getBoundingClientRect();
          dialog.style.setProperty("--ox", `${b.left + b.width / 2 - d.left}px`);
          dialog.style.setProperty("--oy", `${b.top + b.height / 2 - d.top}px`);
        }, 260);
        setTimeout(() => btn.classList.remove("is-launching"), 800);
      });

    });
    dialog.addEventListener("close", () => { video.pause(); video.removeAttribute("src"); video.load(); dialog.classList.remove("is-from-origin"); });
    dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
  }

  /* ------------------------------------------------------------------
     Gallery lightbox: full photo, arrows / swipe / keyboard, no captions
     ------------------------------------------------------------------ */
  const lightbox = $("[data-lightbox]");
  const shots = $$("[data-lightbox-open]");
  if (lightbox && shots.length && typeof lightbox.showModal === "function") {
    const img = $("[data-lightbox-img]", lightbox);
    let set = [];      // the photos in the clicked group: the gallery, or one review's photos
    let index = 0;
    let opener = null;
    let swiped = false;
    const show = (i) => {
      index = (i + set.length) % set.length;
      img.src = set[index].dataset.full;
      img.alt = $("img", set[index]).alt;
      img.style.animation = "none"; void img.offsetWidth; img.style.animation = "";  // replay the fade
      new Image().src = set[(index + 1) % set.length].dataset.full;                // warm the next photo
    };
    shots.forEach((btn) => btn.addEventListener("click", () => {
      opener = btn;
      set = shots.filter((s) => s.dataset.lightboxOpen === btn.dataset.lightboxOpen);
      lightbox.toggleAttribute("data-single", set.length < 2);
      show(set.indexOf(btn));
      lightbox.showModal();
    }));
    $("[data-lightbox-close]", lightbox).addEventListener("click", () => lightbox.close());
    $$("[data-lightbox-step]", lightbox).forEach((b) => b.addEventListener("click", () => show(index + Number(b.dataset.lightboxStep))));
    lightbox.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") show(index + 1);
      if (e.key === "ArrowLeft") show(index - 1);
    });
    let startX = null;
    lightbox.addEventListener("pointerdown", (e) => { startX = e.clientX; swiped = false; });
    lightbox.addEventListener("pointerup", (e) => {
      if (startX === null) return;
      const dx = e.clientX - startX;
      startX = null;
      if (set.length > 1 && Math.abs(dx) > 50 && !e.target.closest(".lightbox__btn")) { swiped = true; show(index + (dx < 0 ? 1 : -1)); }
    });
    lightbox.addEventListener("click", (e) => {
      if (swiped) { swiped = false; return; }
      if (e.target === lightbox) lightbox.close();   // click outside the photo
    });
    lightbox.addEventListener("close", () => { img.removeAttribute("src"); if (opener) opener.focus(); });
  }

  /* Encounter CTAs pre-select the event type in the form */
  $$("[data-event-type]").forEach((a) => {
    a.addEventListener("click", () => {
      const select = $("#f-type");
      if (select) select.value = a.dataset.eventType;
    });
  });

  /* ------------------------------------------------------------------
     Lead forms -> Netlify function -> GoHighLevel
     ------------------------------------------------------------------ */
  const messages = {
    name: "Tell us who is calling.",
    email: "Enter an email address like name@example.com.",
    event_type: "Choose the kind of evening you are planning.",
    event_date: "Choose a date that hasn’t already passed.",
  };

  const showError = (form, input, msg) => {
    const err = $("#" + input.id + "-err", form) || $("#" + input.id + "-err");
    input.setAttribute("aria-invalid", msg ? "true" : "false");
    if (!err) return;
    if (msg) { input.setAttribute("aria-describedby", err.id); err.textContent = msg; err.hidden = false; }
    else { input.removeAttribute("aria-describedby"); err.textContent = ""; err.hidden = true; }
  };

  const validate = (form) => {
    let firstBad = null;
    $$("input[name]:not([name=company]), select[name]", form).forEach((input) => {
      let msg = "";
      if (input.name === "email" && input.value && !input.validity.valid) msg = messages.email;
      if (input.required && !input.value.trim()) msg = messages[input.name] || "This field is required.";
      if (input.name === "event_date" && input.value) {
        const today = new Date(); today.setHours(0, 0, 0, 0);
        if (new Date(input.value + "T00:00:00") < today) msg = messages.event_date;
      }
      showError(form, input, msg);
      if (msg && !firstBad) firstBad = input;
    });
    if (firstBad) firstBad.focus();
    return !firstBad;
  };

  $$("[data-lead-form]").forEach((form) => {
    const status = $("[data-status]", form);
    const submit = $("[data-submit]", form);
    const label = $(".btn__label", submit);
    const idle = label.textContent;

    $$("input, select", form).forEach((input) =>
      input.addEventListener(input.tagName === "SELECT" ? "change" : "blur", () => {
        if (input.getAttribute("aria-invalid") === "true") validate(form);
      })
    );

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      status.textContent = ""; status.classList.remove("is-error");
      if (!validate(form)) return;

      const data = Object.fromEntries(new FormData(form).entries());
      data.form_type = form.dataset.formType;
      data.page = location.pathname;

      submit.setAttribute("aria-busy", "true");
      label.textContent = form.dataset.formType === "newsletter" ? "Joining…" : "Summoning…";

      try {
        const res = await fetch(LEAD_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(body.error || "Request failed");

        if (form.dataset.formType === "newsletter") {
          form.reset();
          status.textContent = "You’re on the list. Watch your inbox for a knock.";
        } else {
          const success = $("[data-success]");
          form.hidden = true;
          success.hidden = false;
          success.focus();
        }
      } catch (err) {
        status.classList.add("is-error");
        status.textContent = "The message didn’t make it through. Try again, or email info@1923lv.com.";
      } finally {
        submit.removeAttribute("aria-busy");
        label.textContent = idle;
      }
    });
  });

  /* ------------------------------------------------------------------
     Easter egg: rest on the planchette for three seconds
     ------------------------------------------------------------------ */
  const planchette = $("[data-planchette]");
  if (planchette) {
    const btn = $("button", planchette);
    const secret = $("[data-planchette-secret]", planchette);
    let timer;
    const start = () => {
      clearTimeout(timer);
      planchette.classList.add("is-holding");
      timer = setTimeout(() => {
        secret.textContent = `Whisper at the door: “${SPEAKEASY_PASSWORD}”`;
        secret.classList.add("is-revealed");
        planchette.classList.remove("is-holding");
      }, 3000);
    };
    const stop = () => { clearTimeout(timer); planchette.classList.remove("is-holding"); };
    btn.addEventListener("pointerenter", start);
    btn.addEventListener("pointerleave", stop);
    btn.addEventListener("pointerdown", start);          // touch: press and hold
    btn.addEventListener("pointerup", (e) => e.pointerType !== "mouse" && stop());
    btn.addEventListener("focus", start);                // keyboard: focus and wait
    btn.addEventListener("blur", stop);
    btn.addEventListener("contextmenu", (e) => e.preventDefault());
  }

  /* Easter egg: someone is still watching the console */
  setTimeout(() => {
    console.log("%cAre you still there?", "color: rgba(201,171,129,.4); font: italic 14px Georgia, serif; letter-spacing: .25em; padding: 8px 0;");
  }, 6660);
})();
