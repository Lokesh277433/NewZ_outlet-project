(function () {
    'use strict';

    // Mobile nav toggle
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function () {
            const open = navLinks.classList.toggle('open');
            navToggle.setAttribute('aria-expanded', open);
        });
    }

    // Copy link
    document.querySelectorAll('.copy-link-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const url = btn.dataset.url;
            navigator.clipboard.writeText(url).then(function () {
                const orig = btn.textContent;
                btn.textContent = 'Copied!';
                setTimeout(function () { btn.textContent = orig; }, 2000);
            });
        });
    });

    // Bookmark toggle
    document.querySelectorAll('.bookmark-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const url = btn.dataset.url;
            const csrf = getCookie('csrftoken');
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrf,
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    btn.classList.toggle('bookmarked', data.bookmarked);
                    btn.textContent = data.bookmarked ? 'Saved' : 'Save';
                });
        });
    });

    // Comment form AJAX
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(commentForm);
            const csrf = getCookie('csrftoken');
            fetch(commentForm.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrf,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.success) {
                        const list = document.getElementById('comment-list');
                        const empty = list.querySelector('.comment-empty');
                        if (empty) empty.remove();
                        const li = document.createElement('li');
                        li.className = 'comment';
                        li.innerHTML = '<strong>' + escapeHtml(data.comment.user) + '</strong> ' +
                            '<time>' + escapeHtml(data.comment.created_at) + '</time>' +
                            '<p>' + escapeHtml(data.comment.body) + '</p>';
                        list.prepend(li);
                        commentForm.reset();
                    }
                });
        });
    }

    // Search suggest
    const searchInput = document.getElementById('search-input');
    const searchSuggest = document.getElementById('search-suggest');
    let suggestTimer;
    if (searchInput && searchSuggest) {
        searchInput.addEventListener('input', function () {
            clearTimeout(suggestTimer);
            const q = searchInput.value.trim();
            if (q.length < 2) {
                searchSuggest.hidden = true;
                return;
            }
            suggestTimer = setTimeout(function () {
                fetch('/search/suggest/?q=' + encodeURIComponent(q))
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (!data.results.length) {
                            searchSuggest.hidden = true;
                            return;
                        }
                        searchSuggest.innerHTML = data.results.map(function (item) {
                            return '<a href="' + item.url + '">' +
                                '<strong>' + escapeHtml(item.title) + '</strong> ' +
                                '<span style="color:#888">' + escapeHtml(item.category) + '</span></a>';
                        }).join('');
                        searchSuggest.hidden = false;
                    });
            }, 300);
        });

        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !searchSuggest.contains(e.target)) {
                searchSuggest.hidden = true;
            }
        });
    }

    const passwordForm = document.getElementById('password-change-form');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const status = document.getElementById('password-change-status');
            passwordForm.querySelectorAll('.field-error[data-field]').forEach(function (el) {
                el.textContent = '';
            });
            const formData = new FormData(passwordForm);
            fetch(passwordForm.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            })
                .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
                .then(function (result) {
                    if (!status) return;
                    status.hidden = false;
                    if (result.data.success) {
                        status.className = 'alert alert-success';
                        status.textContent = result.data.message;
                        passwordForm.reset();
                    } else {
                        status.className = 'alert alert-error';
                        status.textContent = 'Could not update password.';
                        const errors = result.data.errors || {};
                        Object.keys(errors).forEach(function (field) {
                            const el = passwordForm.querySelector('.field-error[data-field="' + field + '"]');
                            if (el) el.textContent = errors[field];
                        });
                    }
                })
                .catch(function () {
                    if (!status) return;
                    status.hidden = false;
                    status.className = 'alert alert-error';
                    status.textContent = 'Could not update password. Try again.';
                });
        });
    }

    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? match[2] : '';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
