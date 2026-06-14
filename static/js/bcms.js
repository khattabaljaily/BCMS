// EnjazBCMS — Beauty Center Management System
// =============================================

// ── Global Spinner ─────────────────────────────────────────────────────────
const GSpinner = (function () {
    var _el = null, _count = 0, _safety = null;
    function _getEl() { return _el || (_el = document.getElementById('global-spinner')); }
    function _doHide() { var s = _getEl(); if (s) s.classList.remove('active'); }
    function show() {
        _count++;
        var s = _getEl(); if (s) s.classList.add('active');
        clearTimeout(_safety); _safety = setTimeout(forceHide, 15000);
    }
    function hide() { _count = Math.max(0, _count - 1); if (_count === 0) { clearTimeout(_safety); _doHide(); } }
    function forceHide() { clearTimeout(_safety); _count = 0; _doHide(); }
    return { show: show, hide: hide, forceHide: forceHide };
})();

// Mobile-friendly replacement for inline <select> status controls in table-cards
function transformAppointmentSelectsForMobile() {
    var mobile = window.matchMedia('(max-width:600px)').matches;
    document.querySelectorAll('.table-wrap td select, .cx-table-wrap td select').forEach(function(sel) {
        var frm = sel.closest('form');
        if (!frm) return;
        if (mobile) {
            if (sel.dataset.mobileized) return;
            // hide native select and add button
            sel.style.display = 'none';
            var td = sel.parentNode;
            if (td && td.classList) td.classList.add('mobile-status-cell');
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn--ghost btn--sm mobile-status-btn';
            var selected = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : '';
            btn.textContent = selected;
            btn.title = selected;
            btn.style.whiteSpace = 'nowrap';
            sel.parentNode.insertBefore(btn, sel);
            btn.addEventListener('click', function() {
                // build a simple modal with options
                var overlay = document.createElement('div');
                overlay.className = 'confirm-overlay';
                var box = document.createElement('div');
                box.className = 'confirm-box';
                box.innerHTML = '<h5 class="confirm-title">تغيير الحالة</h5><div style="margin:8px 0 12px;">اختر الحالة الجديدة:</div>';
                var actions = document.createElement('div'); actions.className = 'confirm-actions';
                Array.from(sel.options).forEach(function(opt) {
                    var b = document.createElement('button');
                    b.type = 'button';
                    b.className = 'btn btn--ghost btn--sm';
                    b.style.margin = '6px';
                    b.style.whiteSpace = 'normal';
                    b.style.wordWrap = 'break-word';
                    b.style.overflow = 'visible';
                    b.style.minWidth = '100px';
                    b.style.padding = '10px 12px';
                    b.style.fontSize = '14px';
                    b.style.lineHeight = '1.5';
                    b.textContent = opt.text;
                    b.title = opt.text;
                    b.dataset.val = opt.value;
                    b.addEventListener('click', function() {
                        sel.value = this.dataset.val;
                        // submit the form
                        frm.submit();
                    });
                    actions.appendChild(b);
                });
                var cancel = document.createElement('button');
                cancel.type = 'button'; cancel.className = 'btn btn--ghost btn--sm'; cancel.textContent = 'إلغاء';
                cancel.style.margin = '6px';
                cancel.addEventListener('click', function() { overlay.classList.remove('open'); setTimeout(function(){ overlay.remove(); document.body.style.overflow=''; },200); });
                actions.appendChild(cancel);
                box.appendChild(actions);
                overlay.appendChild(box);
                document.body.appendChild(overlay);
                document.body.style.overflow = 'hidden';
                requestAnimationFrame(function(){ overlay.classList.add('open'); });
                overlay.addEventListener('click', function(e){ if (e.target === overlay) { overlay.classList.remove('open'); setTimeout(function(){ overlay.remove(); document.body.style.overflow=''; },200); } });
            });
            sel.dataset.mobileized = '1';
        } else {
            if (sel.dataset.mobileized) {
                sel.style.display = '';
                var btn = sel.parentNode.querySelector('.mobile-status-btn'); if (btn) btn.remove();
                if (sel.parentNode && sel.parentNode.classList) sel.parentNode.classList.remove('mobile-status-cell');
                delete sel.dataset.mobileized;
            }
        }
    });
}

// run on load and on resize (debounced)
document.addEventListener('DOMContentLoaded', transformAppointmentSelectsForMobile);
var _resizeTimer = null;
window.addEventListener('resize', function() { clearTimeout(_resizeTimer); _resizeTimer = setTimeout(transformAppointmentSelectsForMobile, 120); });

// Hide on page load and bfcache restore (back/forward nav)
window.addEventListener('pageshow', function () { GSpinner.forceHide(); });
window.addEventListener('load',     function () { GSpinner.forceHide(); });

// Show on navigation link clicks
document.addEventListener('click', function (e) {
    var link = e.target.closest('a[href]');
    if (!link) return;
    var href = link.getAttribute('href') || '';
    if (!href || href === '#' || /^(javascript:|mailto:|tel:|#)/i.test(href)) return;
    if (link.target === '_blank') return;
    if (link.hasAttribute('data-no-spinner')) return;
    if (/\/(export|download|template|backup)[_\/]|[?&](export|download)=/i.test(href)) return;
    GSpinner.show();
}, true);

// Show on page-navigation form submissions (not AJAX — those call e.preventDefault)
document.addEventListener('submit', function (e) {
    if (!e.defaultPrevented) GSpinner.show();
});

// ── BCMS Utilities ─────────────────────────────────────────────────────────
const BCMS = {

    // ── Toast notifications ────────────────────────────────────────────────
    toast: function (message, type) {
        type = type || 'success';
        var iconMap = {
            success: 'fa-check-circle',
            error:   'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info:    'fa-info-circle'
        };
        var container = document.getElementById('global-alerts');
        if (!container) return;
        var toast = document.createElement('div');
        toast.className = 'bcms-toast bcms-toast--' + type;
        toast.setAttribute('role', 'status');
        toast.innerHTML =
            '<div class="bcms-toast__icon"><i class="fas ' + (iconMap[type] || iconMap.info) + '"></i></div>' +
            '<div class="bcms-toast__msg">' + message + '</div>' +
            '<button type="button" class="bcms-toast__close" aria-label="إغلاق"><i class="fas fa-times"></i></button>';
        container.prepend(toast);
        requestAnimationFrame(function () { toast.classList.add('show'); });
        var close = function () {
            toast.classList.remove('show');
            toast.classList.add('hide');
            setTimeout(function () { toast.remove(); }, 220);
        };
        toast.querySelector('.bcms-toast__close').addEventListener('click', close);
        setTimeout(close, 4500);
    },

    // ── Confirm / Delete modal ──────────────────────────────────────────────
    confirmAction: function (message, title) {
        return new Promise(function (resolve) {
            var overlay = document.createElement('div');
            overlay.className = 'confirm-overlay';
            overlay.innerHTML =
                '<div class="confirm-box">' +
                    '<div class="confirm-icon"><i class="fas fa-trash-alt"></i></div>' +
                    '<h5 class="confirm-title">' + (title || 'تأكيد الحذف') + '</h5>' +
                    '<p class="confirm-desc">' + message + '<br><small>لا يمكن التراجع عن هذا الإجراء.</small></p>' +
                    '<div class="confirm-actions">' +
                        '<button type="button" class="btn btn--ghost btn--sm" id="_bcmsNo">إلغاء</button>' +
                        '<button type="button" class="btn btn--danger btn--sm" id="_bcmsYes">نعم، احذف</button>' +
                    '</div>' +
                '</div>';
            document.body.appendChild(overlay);
            document.body.style.overflow = 'hidden';
            requestAnimationFrame(function () { overlay.classList.add('open'); });

            function cleanup() {
                overlay.classList.remove('open');
                setTimeout(function () { overlay.remove(); document.body.style.overflow = ''; }, 200);
            }
            overlay.querySelector('#_bcmsYes').addEventListener('click', function () { cleanup(); resolve(true); });
            overlay.querySelector('#_bcmsNo').addEventListener('click',  function () { cleanup(); resolve(false); });
            overlay.addEventListener('click', function (e) { if (e.target === overlay) { cleanup(); resolve(false); } });
        });
    },

    confirmDelete: function (message) {
        return BCMS.confirmAction(message || 'هل أنت متأكد من الحذف؟', 'تأكيد الحذف');
    },

    alertModal: function (message, title) {
        return new Promise(function (resolve) {
            var overlay = document.createElement('div');
            overlay.className = 'confirm-overlay';
            overlay.innerHTML =
                '<div class="confirm-box">' +
                    '<div class="confirm-icon"><i class="fas fa-info-circle"></i></div>' +
                    '<h5 class="confirm-title">' + (title || 'تنبيه') + '</h5>' +
                    '<p class="confirm-desc">' + message + '</p>' +
                    '<div class="confirm-actions">' +
                        '<button type="button" class="btn btn--primary btn--sm" id="_bcmsOk">حسناً</button>' +
                    '</div>' +
                '</div>';
            document.body.appendChild(overlay);
            document.body.style.overflow = 'hidden';
            requestAnimationFrame(function () { overlay.classList.add('open'); });

            function cleanup() {
                overlay.classList.remove('open');
                setTimeout(function () { overlay.remove(); document.body.style.overflow = ''; }, 200);
            }
            overlay.querySelector('#_bcmsOk').addEventListener('click', function () { cleanup(); resolve(true); });
            overlay.addEventListener('click', function (e) { if (e.target === overlay) { cleanup(); resolve(false); } });
        });
    },

    confirmFormSubmit: function (form, message) {
        if (!form) return false;
        if (!window.BCMS || typeof BCMS.confirmAction !== 'function') {
            return confirm(message);
        }
        BCMS.confirmAction(message || 'هل أنت متأكد من هذا الإجراء؟', 'تأكيد').then(function (result) {
            if (result) form.submit();
        });
        return false;
    },

    showExpenseCategoryInput: function () {
        var select = document.getElementById('expense-category-select');
        var input = document.getElementById('expense-category-input');
        var wrapper = document.getElementById('expense-category-input-wrapper');
        if (!select || !input || !wrapper) return;
        select.removeAttribute('name');
        input.setAttribute('name', 'category');
        wrapper.style.display = 'block';
        input.focus();
    },

    clearExpenseCategoryInput: function () {
        var select = document.getElementById('expense-category-select');
        var input = document.getElementById('expense-category-input');
        var wrapper = document.getElementById('expense-category-input-wrapper');
        if (!select || !input || !wrapper) return;
        input.value = '';
        input.removeAttribute('name');
        select.setAttribute('name', 'category');
        wrapper.style.display = 'none';
    },

    confirmExpenseCategory: function () {
        var select = document.getElementById('expense-category-select');
        var input = document.getElementById('expense-category-input');
        var wrapper = document.getElementById('expense-category-input-wrapper');
        if (!select || !input || !wrapper) return;
        var val = input.value.trim();
        if (!val) { input.focus(); return; }
        // Add the new category as a selected option in the dropdown and switch back
        var existing = select.querySelector('option[value="' + val.replace(/"/g, '\\"') + '"]');
        if (!existing) {
            var opt = document.createElement('option');
            opt.value = val;
            opt.textContent = val;
            select.appendChild(opt);
        }
        select.value = val;
        input.value = '';
        input.removeAttribute('name');
        select.setAttribute('name', 'category');
        wrapper.style.display = 'none';
    },

    ensureExpenseCategorySelection: function () {
        var select = document.getElementById('expense-category-select');
        var input = document.getElementById('expense-category-input');
        if (!select || !input) return;
        if (input.value.trim() === '') {
            input.removeAttribute('name');
            select.setAttribute('name', 'category');
        }
    },

    // ── Simple modal ───────────────────────────────────────────────────────
    openModal: function (id) {
        var m = document.getElementById(id);
        if (!m) return;
        // ensure overlay is moved to the end of document.body so it stacks above any existing modals
        try { document.body.appendChild(m); } catch (err) {}
        try { m.style.display = 'flex'; } catch (err) {}
        m.classList.add('open');
        document.body.style.overflow = 'hidden';
    },

    closeModal: function (id) {
        var m = document.getElementById(id);
        if (!m) return;
        m.classList.remove('open');
        document.body.style.overflow = '';
        // hide after transition so inline display:none doesn't block future opens
        setTimeout(function () { try { m.style.display = 'none'; } catch (err) {} }, 220);
    },

    // ── Get CSRF token from page ───────────────────────────────────────────────
    getCsrf: function () {
        var inp = document.querySelector('[name=csrfmiddlewaretoken]');
        return inp ? inp.value : '';
    },

    // ── AJAX delete: confirm → POST → remove row from DOM + toast ─────────────
    // rowId: string id of the <tr> to remove (also removes matching cx-card-{id})
    ajaxDelete: function (url, confirmMsg, rowId) {
        BCMS.confirmDelete(confirmMsg || 'هل أنت متأكد من الحذف؟').then(function (confirmed) {
            if (!confirmed) return;
            GSpinner.show();
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': BCMS.getCsrf(),
                },
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                GSpinner.hide();
                if (data.success) {
                    if (rowId) {
                        var fade = function (el) {
                            if (!el) return;
                            el.style.transition = 'opacity .18s';
                            el.style.opacity = '0';
                            setTimeout(function () { el.remove(); }, 200);
                        };
                        fade(document.getElementById(rowId));
                        fade(document.getElementById(rowId.replace(/^row-/, 'card-')));
                        var _rid = rowId;
                        setTimeout(function () {
                            try { document.dispatchEvent(new CustomEvent('bcms:recordDeleted', { detail: { row_id: _rid } })); } catch (e) {}
                        }, 250);
                    }
                    BCMS.toast(data.message || 'تم الحذف بنجاح', 'success');
                } else {
                    BCMS.toast(data.error || 'تعذر الحذف', 'error');
                }
            })
            .catch(function () { GSpinner.hide(); BCMS.toast('خطأ في الاتصال بالخادم', 'error'); });
        });
    },

    // ── AJAX form submit: POST → JSON → toast + close modal or reload ─────────
    // options: { onSuccess(json), onError(json), msgSuccess, msgError, autoReload }
    // By default autoReload is disabled to avoid hiding the toast quickly; enable per-form
    // by adding `data-auto-reload="1"` to the <form> or pass { autoReload: true }.
    ajaxForm: function (formEl, options) {
        if (!formEl || formEl._ajaxBound) return;
        formEl._ajaxBound = true;
        options = options || {};
        var autoReload = (options.hasOwnProperty('autoReload')) ? options.autoReload : (formEl.dataset.autoReload === '1');
        formEl.addEventListener('submit', function (e) {
            e.preventDefault();
            var btn = formEl.querySelector('button[type=submit]');
            if (btn) BCMS.showLoading(btn);
            GSpinner.show();
            fetch(formEl.getAttribute('action') || window.location.href, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': BCMS.getCsrf(),
                },
                body: new FormData(formEl),
                credentials: 'same-origin',
            })
            .then(function (r) { return r.json(); })
            .then(function (json) {
                GSpinner.hide();
                if (btn) BCMS.hideLoading(btn);
                if (json.success) {
                    BCMS.toast(json.message || options.msgSuccess || 'تم الحفظ بنجاح', 'success');
                    // dispatch a global event so pages can react and update tables in-place
                    try { document.dispatchEvent(new CustomEvent('bcms:recordChanged', { detail: json })); } catch (e) {}
                    // default in-place row replacement when server returns row_id and row_html
                    if (json.row_id && json.row_html) {
                        try {
                            var existing = document.getElementById(json.row_id);
                            if (existing && existing.parentNode) {
                                var wrap = document.createElement('tbody');
                                wrap.innerHTML = json.row_html.trim();
                                var newRow = wrap.firstElementChild;
                                if (newRow) existing.parentNode.replaceChild(newRow, existing);
                                // also replace matching card view if provided
                                var card = document.getElementById(json.row_id.replace(/^row-/, 'card-'));
                                if (card && json.card_html) {
                                    var cw = document.createElement('div'); cw.innerHTML = json.card_html.trim();
                                    if (cw.firstElementChild) card.parentNode.replaceChild(cw.firstElementChild, card);
                                }
                            } else {
                                // insert new row at top if table exists
                                var tb = document.querySelector('table tbody');
                                if (tb) tb.insertAdjacentHTML('afterbegin', json.row_html);
                            }
                            // re-run table labeling
                            document.dispatchEvent(new Event('bcms:tableRefresh'));
                        } catch (e) { console.error('BCMS.ajaxForm: error replacing row_html', e, json); }
                    } else {
                        // fallback: if no row_html provided, try to refresh the main table body from the server
                        try {
                            var tableEl = document.querySelector('.cx-table');
                            if (tableEl) {
                                fetch(window.location.href, { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' })
                                    .then(function (r) { return r.text(); })
                                    .then(function (html) {
                                        try {
                                            var wrapper = document.createElement('div'); wrapper.innerHTML = html;
                                            var newTbody = wrapper.querySelector('.cx-table tbody');
                                            if (newTbody) {
                                                var curTbody = document.querySelector('.cx-table tbody');
                                                if (curTbody && curTbody.parentNode) curTbody.parentNode.replaceChild(newTbody, curTbody);
                                                document.dispatchEvent(new Event('bcms:tableRefresh'));
                                            }
                                        } catch (e) { console.error('BCMS.ajaxForm: error parsing fallback table HTML', e); }
                                    }).catch(function () { /* ignore */ });
                            }
                        } catch (e) { console.error('BCMS.ajaxForm: fallback table refresh error', e); }
                    }
                    if (options.onSuccess) {
                        options.onSuccess(json);
                    } else {
                        var overlay = formEl.closest('.modal-overlay');
                        if (overlay) BCMS.closeModal(overlay.id);
                        if (autoReload) setTimeout(function () { window.location.reload(); }, 350);
                    }
                } else {
                    BCMS.toast(json.error || options.msgError || 'حدث خطأ أثناء الحفظ', 'error');
                    if (options.onError) options.onError(json);
                }
            })
            .catch(function () {
                GSpinner.hide();
                if (btn) BCMS.hideLoading(btn);
                BCMS.toast('حدث خطأ في الاتصال بالخادم', 'error');
            });
        });
    },

    // ── Load remote modal HTML and open it (expects server to return modal markup)
    loadRemoteModal: function (url) {
        // ensure we request the modal variant so server can return a partial
        if (url.indexOf('?') === -1) url = url + '?modal=1'; else url = url + '&modal=1';
        GSpinner.show();
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) { return r.text(); })
            .then(function (html) {
                GSpinner.hide();
                // insert into body
                var div = document.createElement('div');
                div.innerHTML = html;
                var overlay = div.querySelector('.modal-overlay');
                // move children to body after we have a reference to the modal overlay
                Array.from(div.children).forEach(function (ch) { document.body.appendChild(ch); });
                if (overlay) {
                    var id = overlay.id;
                    BCMS.openModal(id);
                    // attach AJAX submit handler for forms inside modal
                    var form = overlay.querySelector('form');
                    if (form) BCMS._attachModalFormHandler(form, overlay);
                }
            }).catch(function (err) { GSpinner.hide(); BCMS.toast('تعذر تحميل النموذج','error'); });
    },

    _attachModalFormHandler: function (form, overlay) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var btn = form.querySelector('button[type=submit]');
            BCMS.showLoading(btn);
            var data = new FormData(form);
            // determine whether this modal/form should trigger a page reload after success
            var doReload = (form.dataset.autoReload === '1') || (overlay && overlay.dataset.autoReload === '1');
            fetch(form.action, {
                method: 'POST',
                body: data,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': BCMS.getCsrf(),
                },
                credentials: 'same-origin',
            })
                .then(function (r) { return r.json(); })
                .then(function (json) {
                    BCMS.hideLoading(btn);
                    if (json && json.success) {
                        BCMS.toast('تم الحفظ', 'success');
                        try { document.dispatchEvent(new CustomEvent('bcms:recordChanged', { detail: json })); } catch (e) { console.error('BCMS._attachModalFormHandler: dispatch error', e, json); }
                        if (json.row_id && json.row_html) {
                            try {
                                var existing = document.getElementById(json.row_id);
                                if (existing && existing.parentNode) {
                                    var wrap = document.createElement('tbody');
                                    wrap.innerHTML = json.row_html.trim();
                                    var newRow = wrap.firstElementChild;
                                    if (newRow) existing.parentNode.replaceChild(newRow, existing);
                                    var card = document.getElementById(json.row_id.replace(/^row-/, 'card-'));
                                    if (card && json.card_html) {
                                        var cw = document.createElement('div'); cw.innerHTML = json.card_html.trim();
                                        if (cw.firstElementChild) card.parentNode.replaceChild(cw.firstElementChild, card);
                                    }
                                } else {
                                    var tb = document.querySelector('table tbody');
                                    if (tb) tb.insertAdjacentHTML('afterbegin', json.row_html);
                                }
                                document.dispatchEvent(new Event('bcms:tableRefresh'));
                            } catch (e) { console.error('BCMS._attachModalFormHandler: error replacing row_html', e, json); }
                        } else {
                            // fallback: refresh main table body
                            try {
                                var tableEl = document.querySelector('.cx-table');
                                if (tableEl) {
                                    fetch(window.location.href, { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' })
                                        .then(function (r) { return r.text(); })
                                        .then(function (html) {
                                            try {
                                                var wrapper = document.createElement('div'); wrapper.innerHTML = html;
                                                var newTbody = wrapper.querySelector('.cx-table tbody');
                                                if (newTbody) {
                                                    var curTbody = document.querySelector('.cx-table tbody');
                                                    if (curTbody && curTbody.parentNode) curTbody.parentNode.replaceChild(newTbody, curTbody);
                                                    document.dispatchEvent(new Event('bcms:tableRefresh'));
                                                }
                                            } catch (e) { console.error('BCMS._attachModalFormHandler: error parsing fallback table HTML', e); }
                                        }).catch(function () {});
                                }
                            } catch (e) { console.error('BCMS._attachModalFormHandler: fallback table refresh error', e); }
                        }
                        // close modal and refresh table
                        var id = overlay.id; BCMS.closeModal(id);
                        if (doReload) setTimeout(function () { window.location.reload(); }, 220);
                    } else {
                        BCMS.toast('حدث خطأ أثناء الحفظ', 'error');
                    }
                }).catch(function () { BCMS.hideLoading(btn); BCMS.toast('حدث خطأ أثناء الحفظ','error'); });
        });
    },

    // ── Flush Django messages as toasts ────────────────────────────────────
    flushMessages: function () {
        var msgs = window.__bcmsPendingMessages || [];
        for (var i = 0; i < msgs.length; i++) {
            BCMS.toast(msgs[i].message, msgs[i].type);
        }
    },

    // ── AJAX loading state on buttons ──────────────────────────────────────
    showLoading: function (btn) {
        btn.disabled = true;
        btn._origHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التحميل...';
    },

    hideLoading: function (btn) {
        btn.disabled = false;
        if (btn._origHtml !== undefined) btn.innerHTML = btn._origHtml;
    }
};

// Flush Django messages + attach AJAX to always-present modals
document.addEventListener('DOMContentLoaded', function () {
    BCMS.flushMessages();
    // Client modal is included sitewide via base.html
    var clientForm = document.getElementById('client-form');
    if (clientForm) BCMS.ajaxForm(clientForm);
});

// Close modals when overlay clicked or [data-close-modal] clicked
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('open');
        document.body.style.overflow = '';
        // hide after transition so inline display:none doesn't block future opens
        setTimeout(function () { try { e.target.style.display = 'none'; } catch (err) {} }, 220);
    }
    var closer = e.target.closest('[data-close-modal]');
    if (closer) BCMS.closeModal(closer.dataset.closeModal);
});

// Backwards-compatible global modal helpers for inline onclick usage
window.openModal = function (id) {
    var m = document.getElementById(id);
    if (!m) return;
    try { m.style.display = 'flex'; } catch (err) {}
    if (typeof BCMS !== 'undefined' && BCMS.openModal) {
        BCMS.openModal(id);
    }
};

window.closeModal = function (id) {
    var m = document.getElementById(id);
    if (!m) return;
    if (typeof BCMS !== 'undefined' && BCMS.closeModal) {
        BCMS.closeModal(id);
    }
    // hide overlay after transition
    setTimeout(function () { try { m.style.display = 'none'; } catch (err) {} }, 250);
};

// ── Client modal helpers (available globally)
BCMS.openAddClient = function () {
    document.getElementById('client-modal-title').textContent = 'عميل جديد';
    document.getElementById('client-pk').value = '';
    document.getElementById('client-name').value = '';
    document.getElementById('client-phone').value = '';
    document.getElementById('client-email').value = '';
    document.getElementById('client-birthdate').value = '';
    document.getElementById('client-referral').value = '';
    document.getElementById('client-notes').value = '';
    BCMS.openModal('client-modal');
};

BCMS.openEditClient = function (pk, name, phone, email, gender, birthdate, referral, notes) {
    document.getElementById('client-modal-title').textContent = 'تعديل العميل';
    document.getElementById('client-pk').value = pk;
    document.getElementById('client-name').value = name;
    document.getElementById('client-phone').value = phone;
    document.getElementById('client-email').value = email || '';
    document.getElementById('client-birthdate').value = birthdate || '';
    document.getElementById('client-referral').value = referral || '';
    document.getElementById('client-notes').value = notes || '';
    BCMS.openModal('client-modal');
};

window.openAddClient = function () { if (window.BCMS && BCMS.openAddClient) return BCMS.openAddClient(); };
window.openEditClient = function (pk, name, phone, email, gender, birthdate, referral, notes) { if (window.BCMS && BCMS.openEditClient) return BCMS.openEditClient(pk, name, phone, email, gender, birthdate, referral, notes); };

window.__bcmsNativeConfirm = window.__bcmsNativeConfirm || window.confirm;
window.confirm = function (message) {
    if (typeof BCMS !== 'undefined' && typeof BCMS.confirmAction === 'function') {
        var active = document.activeElement;
        var form = active && active.form;
        if (!form) {
            return window.__bcmsNativeConfirm ? window.__bcmsNativeConfirm(message) : false;
        }
        BCMS.confirmAction(message || 'هل أنت متأكد من هذا الإجراء؟', 'تأكيد').then(function (result) {
            if (result) form.submit();
        });
        return false;
    }
    return window.__bcmsNativeConfirm ? window.__bcmsNativeConfirm(message) : false;
};

// ── Sidebar toggle ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    var toggleBtn = document.getElementById('sidebar-toggle');
    var sidebar   = document.getElementById('sidebar');
    if (!toggleBtn || !sidebar) return;

    toggleBtn.style.display = 'flex';

    var overlay = document.createElement('div');
    overlay.id = 'sidebar-overlay';
    overlay.style.cssText = 'display:none;position:fixed;inset:0;z-index:199;background:rgba(0,0,0,.4)';
    document.body.appendChild(overlay);

    function isMobile() { return window.matchMedia('(max-width: 768px)').matches; }
    function open()  {
      sidebar.classList.add('open');
      sidebar.classList.remove('closed');
      if (isMobile()) {
        overlay.style.display = 'block';
        document.body.style.overflow = 'hidden';
      } else {
        overlay.style.display = 'none';
        document.body.style.overflow = '';
      }
    }
    function close() {
      sidebar.classList.remove('open');
      sidebar.classList.add('closed');
      overlay.style.display = 'none';
      document.body.style.overflow = '';
    }

    toggleBtn.addEventListener('click', function () { sidebar.classList.contains('open') ? close() : open(); });
    overlay.addEventListener('click', close);
});

function copyStoreLink(url) {
  navigator.clipboard.writeText(url).then(function () {
    BCMS.toast('تم نسخ رابط المتجر!', 'success');
  }).catch(function () {
    /* fallback for browsers that deny clipboard without HTTPS */
    var ta = document.createElement('textarea');
    ta.value = url;
    ta.style.cssText = 'position:fixed;opacity:0;top:0;right:0;';
    document.body.appendChild(ta);
    ta.focus(); ta.select();
    try { document.execCommand('copy'); BCMS.toast('تم نسخ الرابط!', 'success'); }
    catch (e)  { BCMS.toast('تعذر النسخ — انسخ الرابط يدوياً: ' + url, 'warning'); }
    document.body.removeChild(ta);
  });
}

/* ── Auto-label table cells from thead headers (for mobile cards) ── */
(function () {
  function labelTables() {
    document.querySelectorAll(
      '.table-wrap > table, .cx-table-wrap > table'
    ).forEach(function (table) {
      var headers = Array.from(
        table.querySelectorAll('thead th')
      ).map(function (th) { return th.textContent.trim(); });
      if (!headers.length) return;
      table.querySelectorAll('tbody tr').forEach(function (row) {
        var cells = row.querySelectorAll('td');
        /* Only label rows that have the same count as headers or fewer */
        cells.forEach(function (td, i) {
          if (headers[i] && !td.hasAttribute('colspan')) {
            td.setAttribute('data-label', headers[i]);
          }
        });
      });
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', labelTables);
  } else {
    labelTables();
  }
  /* Re-label after any AJAX table refresh if the app dispatches this event */
  document.addEventListener('bcms:tableRefresh', labelTables);
})();
