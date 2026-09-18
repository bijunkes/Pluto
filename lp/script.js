/**
 * script.js — Pluto site behavior
 * Classic (non-module) script so the site opens correctly straight from
 * disk (file://) as well as from a server. Depends on data.js (PLUTO_DATA)
 * being loaded first, and on the Lucide icon script for <i data-lucide>.
 */

(function () {
    "use strict";

    var prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    /* ----------------------------------------------------------------------
     * Small helpers
     * -------------------------------------------------------------------- */

    function el(tag, className, html) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (html !== undefined) node.innerHTML = html;
        return node;
    }

    function initials(name) {
        var parts = name.trim().split(/\s+/);
        var first = parts[0] ? parts[0][0] : "";
        var last = parts.length > 1 ? parts[parts.length - 1][0] : "";
        return (first + last).toUpperCase();
    }

    function icon(name, extra) {
        return '<i data-lucide="' + name + '"' + (extra || "") + "></i>";
    }

    /* ----------------------------------------------------------------------
     * Navbar: scroll state + mobile menu
     * -------------------------------------------------------------------- */

    function initNav() {
        var navbar = document.querySelector(".navbar");
        var toggle = document.querySelector(".nav-toggle");
        var mobile = document.querySelector(".nav-mobile");
        if (!navbar) return;

        function onScroll() {
            navbar.classList.toggle("is-scrolled", window.scrollY > 12);
        }
        onScroll();
        window.addEventListener("scroll", onScroll, { passive: true });

        if (toggle && mobile) {
            toggle.addEventListener("click", function () {
                var isOpen = mobile.classList.toggle("is-open");
                toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
                document.body.style.overflow = isOpen ? "hidden" : "";
                var iconEl = toggle.querySelector("i");
                if (iconEl) iconEl.setAttribute("data-lucide", isOpen ? "x" : "menu");
                if (window.lucide) window.lucide.createIcons();
            });

            mobile.querySelectorAll("a").forEach(function (link) {
                link.addEventListener("click", function () {
                    mobile.classList.remove("is-open");
                    toggle.setAttribute("aria-expanded", "false");
                    document.body.style.overflow = "";
                    var iconEl = toggle.querySelector("i");
                    if (iconEl) iconEl.setAttribute("data-lucide", "menu");
                    if (window.lucide) window.lucide.createIcons();
                });
            });
        }
    }

    /* ----------------------------------------------------------------------
     * Ambient particles (hero + final CTA)
     * -------------------------------------------------------------------- */

    function initParticles() {
        if (prefersReducedMotion) return;
        document.querySelectorAll(".particles").forEach(function (field) {
            var count = parseInt(field.getAttribute("data-count") || "16", 10);
            for (var i = 0; i < count; i++) {
                var p = el("span", "particle");
                p.style.left = Math.random() * 100 + "%";
                p.style.bottom = Math.random() * 60 + "%";
                p.style.animationDuration = 6 + Math.random() * 8 + "s";
                p.style.animationDelay = Math.random() * 8 + "s";
                field.appendChild(p);
            }
        });
    }

    /* ----------------------------------------------------------------------
     * Scroll reveal
     * -------------------------------------------------------------------- */

    function initReveal() {
        var targets = document.querySelectorAll(".reveal");
        if (prefersReducedMotion || !("IntersectionObserver" in window)) {
            targets.forEach(function (t) { t.classList.add("is-visible"); });
            return;
        }
        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15, rootMargin: "0px 0px -60px 0px" }
        );
        targets.forEach(function (t) { observer.observe(t); });
    }

    /* ----------------------------------------------------------------------
     * Architecture line draw
     * -------------------------------------------------------------------- */

    function initArchReveal() {
        var arch = document.querySelector(".arch");
        if (!arch) return;
        if (prefersReducedMotion || !("IntersectionObserver" in window)) {
            arch.classList.add("is-visible");
            return;
        }
        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        arch.classList.add("is-visible");
                        observer.unobserve(arch);
                    }
                });
            },
            { threshold: 0.2 }
        );
        observer.observe(arch);
    }

    /* ----------------------------------------------------------------------
     * Animated stat counters
     * -------------------------------------------------------------------- */

    function animateCount(node, target, duration) {
        if (prefersReducedMotion) {
            node.textContent = String(target).padStart(2, "0");
            return;
        }
        var start = null;
        function step(ts) {
            if (start === null) start = ts;
            var progress = Math.min((ts - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var value = Math.round(eased * target);
            node.textContent = String(value).padStart(2, "0");
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    function initStats() {
        var row = document.querySelector(".stats-row");
        if (!row) return;
        var values = row.querySelectorAll(".stat-value");
        if (!("IntersectionObserver" in window)) {
            values.forEach(function (v) {
                v.textContent = String(v.dataset.value).padStart(2, "0");
            });
            return;
        }
        var done = false;
        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting && !done) {
                        done = true;
                        values.forEach(function (v) {
                            animateCount(v, parseInt(v.dataset.value, 10), 1200);
                        });
                        observer.unobserve(row);
                    }
                });
            },
            { threshold: 0.4 }
        );
        observer.observe(row);
    }

    /* ----------------------------------------------------------------------
     * Render: Team
     * -------------------------------------------------------------------- */

    function avatarMarkup(member, small) {
        if (member.photo) {
            return '<img src="' + member.photo + '" alt="Foto de ' + member.name + '" />';
        }
        return (
            '<div class="avatar-fallback">' +
            '<span class="avatar-initials">' + initials(member.name) + "</span>" +
            (small ? "" : "<small>Foto em breve</small>") +
            "</div>"
        );
    }

    function socialLinks(member, iconOnly) {
        return (
            '<div class="team-links">' +

            '<a class="team-link" href="' + member.linkedin +
            '" target="_blank" rel="noopener noreferrer" ' +
            'aria-label="LinkedIn de ' + member.name + '">' +
            '<i class="fa-brands fa-linkedin"></i>' +
            '</a>' +

            '<a class="team-link" href="' + member.github +
            '" target="_blank" rel="noopener noreferrer" ' +
            'aria-label="GitHub de ' + member.name + '">' +
            '<i class="fa-brands fa-github"></i>' +
            '</a>' +

            '</div>'
        );
    }

    function renderTeam() {
        var gridWrap = document.getElementById("team-grid");
        if (!gridWrap) return;

        gridWrap.innerHTML = "";

        PLUTO_DATA.team.forEach(function (member, i) {
            var card = el("div", "team-card reveal");

            card.style.setProperty("--i", i);

            card.innerHTML =
                '<div class="avatar">' +
                avatarMarkup(member, true) +
                "</div>" +
                "<h3>" +
                member.name +
                "</h3>" +
                '<p class="team-role">' +
                member.role +
                "</p>" +
                '<p class="team-desc">' +
                member.description +
                "</p>" +
                socialLinks(member, true);

            gridWrap.appendChild(card);
        });
    }

    /* ----------------------------------------------------------------------
     * Render: Tech stack
     * -------------------------------------------------------------------- */

    function renderTech() {
        var wrap = document.getElementById("tech-grid");
        if (!wrap) return;
        PLUTO_DATA.techCategories.forEach(function (cat) {
            var block = el("div", "tech-category");
            var chips = cat.items
                .map(function (item) { return '<span class="tech-chip">' + item + "</span>"; })
                .join("");
            block.innerHTML =
                '<div class="tech-category-head">' + icon(cat.icon) + "<h3>" + cat.title + "</h3></div>" +
                '<div class="chip-list">' + chips + "</div>";
            wrap.appendChild(block);
        });
    }

    /* ----------------------------------------------------------------------
     * Render: Architecture
     * -------------------------------------------------------------------- */

    function archNodeMarkup(node) {
        return (
            '<div class="arch-node" tabindex="0">' +
            icon(node.icon) +
            "<span>" + node.label + "</span>" +
            '<span class="arch-tooltip">' + node.tooltip + "</span>" +
            "</div>"
        );
    }

    function renderArchitecture() {
        var wrap = document.getElementById("arch");
        if (!wrap) return;
        var html = "";
        PLUTO_DATA.architecture.forEach(function (node) {
            if (node.branch) {
                html += '<div class="branch-fork"></div>';
                html += '<div class="arch-branch">';
                node.items.forEach(function (b) { html += archNodeMarkup(b); });
                html += "</div>";
                html += '<div class="branch-join"></div>';
            } else {
                html += archNodeMarkup(node);
            }
        });
        wrap.innerHTML = html;
    }

    /* ----------------------------------------------------------------------
     * Render: Context metadata
     * -------------------------------------------------------------------- */

    function renderContext() {
        var wrap = document.getElementById("meta-grid");
        if (!wrap) return;
        wrap.innerHTML = PLUTO_DATA.context
            .map(function (row) {
                return (
                    '<div class="meta-row"><span class="meta-label">' +
                    row.label +
                    '</span><span class="meta-value">' +
                    row.value +
                    "</span></div>"
                );
            })
            .join("");
    }

    /* ----------------------------------------------------------------------
     * Render: Stats
     * -------------------------------------------------------------------- */

    function renderStats() {
        var wrap = document.getElementById("stats-row");
        if (!wrap) return;
        wrap.innerHTML = PLUTO_DATA.stats
            .map(function (s) {
                return (
                    '<div class="stat-item"><div class="stat-value" data-value="' +
                    s.value +
                    '">00</div><div class="stat-label">' +
                    s.label +
                    "</div></div>"
                );
            })
            .join("");
    }

    /* ----------------------------------------------------------------------
     * Render: Team mini links (redes section)
     * -------------------------------------------------------------------- */

    function renderTeamMini() {
        var wrap = document.getElementById("team-mini");
        if (!wrap) return;
        wrap.innerHTML = PLUTO_DATA.team
            .map(function (m) {
                return (
                    '<a href="' + m.linkedin + '" target="_blank" rel="noopener noreferrer">' +
                    '<span class="mini-avatar">' + initials(m.name) + "</span>" +
                    m.name.split(" ")[0] +
                    "</a>"
                );
            })
            .join("");
    }

    /* ----------------------------------------------------------------------
     * Hero chip chart bars (randomized once, purely decorative)
     * -------------------------------------------------------------------- */

    function initMiniCharts() {
        document.querySelectorAll("[data-bars]").forEach(function (bar) {
            var heights = bar.getAttribute("data-bars").split(",");
            bar.innerHTML = heights
                .map(function (h) { return '<span style="height:' + h + '%"></span>'; })
                .join("");
        });
    }

    /* ----------------------------------------------------------------------
     * Footer year
     * -------------------------------------------------------------------- */

    function initYear() {
        var y = document.getElementById("year");
        if (y) y.textContent = new Date().getFullYear();
    }

    /* ----------------------------------------------------------------------
     * Boot
     * -------------------------------------------------------------------- */

    document.addEventListener("DOMContentLoaded", function () {
        renderTeam();
        renderTech();
        renderArchitecture();
        renderContext();
        renderStats();
        renderTeamMini();
        initMiniCharts();
        initNav();
        initParticles();
        initYear();

        if (window.lucide) window.lucide.createIcons();

        initReveal();
        initArchReveal();
        initStats();
    });
})();