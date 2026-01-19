document.addEventListener('DOMContentLoaded', () => {
    // State
    let allTemplates = [];
    let currentTemplate = null;
    let debounceTimer = null;
    let isAdmin = false;
    let editingRuleId = null; // null means new rule
    let deletingTemplateId = null; // for modal deletion
    let sidebarOffcanvas = null;

    // DOM Elements - updated for new layout
    const elements = {
        alertTypes: document.querySelectorAll('input[name="alertType"]'),
        templateList: document.getElementById('templateList'),
        searchInput: document.getElementById('searchTemplate'),
        editorTitle: document.getElementById('editorTitle'),

        yamlEditor: document.getElementById('yamlEditor'),
        copyBtn: document.getElementById('copyBtn'),
        downloadBtn: document.getElementById('downloadBtn'),
        // Validation elements moved to header
        validationIconWrapper: document.getElementById('validationIconWrapper'),
        validationIcon: document.getElementById('validationIcon'),
        validationMsg: document.getElementById('validationMsg'),
        errorOneLine: document.getElementById('errorOneLine'),
        promqlStatus: document.getElementById('promqlStatus'),
        toast: new bootstrap.Toast(document.getElementById('liveToast')),
        // Live Test Headers
        promUrl: document.getElementById('promUrl'),
        testQueryBtn: document.getElementById('testQueryBtn'),
        queryResultArea: document.getElementById('queryResultArea'),
        queryResultContent: document.getElementById('queryResultContent'),

        // Admin Elements
        adminLoginBtn: document.getElementById('adminLoginBtn'),
        adminLogoutBtn: document.getElementById('adminLogoutBtn'),
        adminAddContainer: document.getElementById('adminAddContainer'),
        loginModal: new bootstrap.Modal(document.getElementById('loginModal')),
        loginSubmitBtn: document.getElementById('loginSubmitBtn'),
        adminPasswordInput: document.getElementById('adminPasswordInput'),
        loginErrorBanner: document.getElementById('loginErrorBanner'),

        ruleModal: new bootstrap.Modal(document.getElementById('ruleModal')),
        ruleModalTitle: document.getElementById('ruleModalTitle'),
        addNewRuleBtn: document.getElementById('addNewRuleBtn'),
        ruleSaveBtn: document.getElementById('ruleSaveBtn'),
        ruleNameInput: document.getElementById('ruleNameInput'),
        ruleJobInput: document.getElementById('ruleJobInput'),
        ruleDescInput: document.getElementById('ruleDescInput'),
        ruleTypesInput: document.getElementById('ruleTypesInput'),
        ruleYamlInput: document.getElementById('ruleYamlInput'),
        modalValidationBadge: document.getElementById('modalValidationBadge'),
        modalErrorBanner: document.getElementById('modalErrorBanner'),
        sidebarOffcanvasElem: document.getElementById('sidebarOffcanvas'),
        welcomeView: document.getElementById('welcomeView'),
        editorView: document.getElementById('editorView'),
        navbarBrand: document.querySelector('.navbar-brand'),
        confirmDeleteBtn: document.getElementById('confirmDeleteBtn'),
        deleteModal: new bootstrap.Modal(document.getElementById('deleteConfirmModal')),
        setupModal: new bootstrap.Modal(document.getElementById('setupModal')),
        setupPasswordInput: document.getElementById('setupPasswordInput'),
        setupConfirmInput: document.getElementById('setupConfirmInput'),
        setupSubmitBtn: document.getElementById('setupSubmitBtn'),
        setupErrorBanner: document.getElementById('setupErrorBanner'),
        errorModal: new bootstrap.Modal(document.getElementById('errorModal')),
        errorModalMessage: document.getElementById('errorModalMessage')
    };

    // Initialize bootstrap offcanvas
    if (elements.sidebarOffcanvasElem) {
        sidebarOffcanvas = new bootstrap.Offcanvas(elements.sidebarOffcanvasElem);
    }

    // Theme Configuration
    // =========================================================================
    // Themes are now dynamically loaded from themes.css via Flask backend
    // To add a new theme: 
    // 1. Add the theme CSS to themes.css following the pattern: html[data-theme="themename"] { ... }
    // 2. (Optional) Add an icon mapping in app.py's parse_available_themes() function
    // 3. Restart the Flask app (or rely on auto-reload in debug mode)

    const AVAILABLE_THEMES = window.AVAILABLE_THEMES || [
        { value: 'default', name: 'Default (Dark)', icon: 'bi-moon-stars' }
    ];

    function initThemeDropdown() {
        const menu = document.getElementById('themeDropdownMenu');
        if (!menu) return;

        // Build dropdown HTML
        let html = `
            <li>
                <h6 class="dropdown-header">Select Theme</h6>
            </li>
        `;

        AVAILABLE_THEMES.forEach((theme, index) => {
            // Add divider after default theme
            if (index === 1) {
                html += '<li><hr class="dropdown-divider"></li>';
            }

            const activeClass = theme.value === 'default' ? 'active' : '';
            html += `
                <li>
                    <a class="dropdown-item ${activeClass}" href="#" data-theme-value="${theme.value}">
                        <i class="bi ${theme.icon} me-2"></i>${theme.name}
                    </a>
                </li>
            `;
        });

        menu.innerHTML = html;

        // Attach event listeners to new dropdown items
        document.querySelectorAll('[data-theme-value]').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const theme = item.getAttribute('data-theme-value');
                setTheme(theme);
            });
        });
    }

    // Initialization
    // =========================================================================
    initThemeDropdown();
    fetchTemplates();
    initTheme();
    checkAdminStatus();

    // Event Listeners

    elements.alertTypes.forEach(radio => {
        radio.addEventListener('change', () => {
            renderTemplateList();
        });
    });

    elements.searchInput.addEventListener('input', () => {
        renderTemplateList();
    });

    elements.yamlEditor.addEventListener('input', () => {
        debouncedValidate();
    });



    // Custom CSS for small buttons and badges
    const style = document.createElement('style');
    style.innerHTML = `
        .btn-xxs { padding: 0.1rem 0.3rem; font-size: 0.65rem; }
        .list-group-item.active .text-muted { color: rgba(255,255,255,0.7) !important; }
        .rule-count-badge {
            display: inline-block;
            padding: 0.15rem 0.4rem;
            font-size: 0.65rem;
            font-weight: 600;
            line-height: 1;
            color: var(--primary-color);
            background-color: color-mix(in srgb, var(--primary-color) 15%, transparent);
            border: 1px solid color-mix(in srgb, var(--primary-color) 30%, transparent);
            border-radius: 10px;
        }
    `;
    document.head.appendChild(style);

    elements.copyBtn.addEventListener('click', copyToClipboard);
    elements.downloadBtn.addEventListener('click', downloadFile);
    elements.testQueryBtn.addEventListener('click', runLiveQuery);

    // Admin Listeners
    elements.adminLoginBtn.addEventListener('click', () => {
        elements.adminPasswordInput.value = '';
        elements.loginModal.show();
    });

    elements.loginSubmitBtn.addEventListener('click', handleLogin);

    // Allow Enter key to submit login
    elements.adminPasswordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleLogin();
        }
    });
    elements.adminLogoutBtn.addEventListener('click', handleLogout);
    elements.addNewRuleBtn.addEventListener('click', openAddModal);
    elements.ruleSaveBtn.addEventListener('click', saveRule);
    elements.ruleYamlInput.addEventListener('input', validateModalYaml);
    elements.setupSubmitBtn.addEventListener('click', handleSetup);
    elements.confirmDeleteBtn.addEventListener('click', () => {
        if (deletingTemplateId) {
            deleteRule(deletingTemplateId);
            elements.deleteModal.hide();
        }
    });

    // Brand logo returns to welcome
    elements.navbarBrand.addEventListener('click', (e) => {
        // Only if not clicking the toggle button specifically
        if (!e.target.closest('button')) {
            e.preventDefault();
            showView('welcome');
        }
    });

    // =========================================================================
    // Theme Logic
    // =========================================================================
    function initTheme() {
        const savedTheme = localStorage.getItem('yamalert-theme') || 'default';
        setTheme(savedTheme);
    }

    function setTheme(theme) {
        // Set attribute on html tag
        if (theme === 'default') {
            document.documentElement.removeAttribute('data-theme');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }

        // Update local storage
        localStorage.setItem('yamalert-theme', theme);

        // Update active state in dropdown
        document.querySelectorAll('[data-theme-value]').forEach(el => {
            el.classList.remove('active');
            if (el.getAttribute('data-theme-value') === theme) {
                el.classList.add('active');
            }
        });
    }

    // =========================================================================
    // Core Functions
    // =========================================================================

    async function fetchTemplates() {
        try {
            elements.templateList.innerHTML = '<div class="text-center text-muted mt-5">Loading templates...</div>';
            const res = await fetch('/api/templates');
            if (!res.ok) throw new Error('Failed to load templates');
            allTemplates = await res.json();
            renderTemplateList();
        } catch (err) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-center text-danger mt-5';
            errorDiv.textContent = 'Error: ' + err.message;
            elements.templateList.innerHTML = '';
            elements.templateList.appendChild(errorDiv);
        }
    }

    function showView(view) {
        if (view === 'editor') {
            elements.welcomeView.classList.add('d-none');
            elements.editorView.classList.remove('d-none');
        } else {
            elements.welcomeView.classList.remove('d-none');
            elements.editorView.classList.add('d-none');
            // De-select current template in sidebar
            currentTemplate = null;
            renderTemplateList();
        }
    }

    function renderTemplateList() {
        const selectedType = document.querySelector('input[name="alertType"]:checked').value;
        const searchTerm = elements.searchInput.value.toLowerCase();

        const filtered = allTemplates.filter(t => {
            const matchesType = selectedType === 'all' || (t.alert_types && t.alert_types.includes(selectedType));
            const matchesSearch = t.name.toLowerCase().includes(searchTerm) ||
                t.job.toLowerCase().includes(searchTerm) ||
                (t.description && t.description.toLowerCase().includes(searchTerm));
            return matchesType && matchesSearch;
        });

        elements.templateList.innerHTML = '';
        if (filtered.length === 0) {
            elements.templateList.innerHTML = '<div class="text-center text-muted mt-4 small">No matching templates found</div>';
            return;
        }

        filtered.forEach(t => {
            const item = document.createElement('div');
            item.className = `list-group-item p-2 mb-1 rounded border-secondary position-relative ${currentTemplate && currentTemplate.id === t.id ? 'active' : ''}`;

            let adminButtons = '';
            if (isAdmin) {
                adminButtons = `
                    <div class="admin-actions d-flex gap-1" style="z-index: 10;">
                        <button class="btn btn-xxs btn-outline-info edit-btn" data-id="${t.id}" title="Edit Template">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-xxs btn-outline-danger delete-btn" data-id="${t.id}" title="Delete Template">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                `;
            }

            // Calculate rule count
            const ruleCount = (t.rules && Array.isArray(t.rules)) ? t.rules.length : 0;

            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-center w-100 py-1">
                    <div class="flex-grow-1 text-truncate pe-2 lh-1">
                        <span class="fw-bold" style="font-size: 0.85rem;">${t.name}</span>
                        <span class="rule-count-badge ms-1">${ruleCount}</span>
                        <span class="text-muted ms-1" style="font-size: 0.7rem; opacity: 0.8;">(${t.job})</span>
                    </div>
                    ${adminButtons}
                </div>
            `;

            // Template selection click
            item.addEventListener('click', (e) => {
                // Ignore if clicking admin buttons area
                if (!e.target.closest('.admin-actions')) {
                    selectTemplate(t);
                }
            });

            if (isAdmin) {
                const editBtn = item.querySelector('.edit-btn');
                const deleteBtn = item.querySelector('.delete-btn');

                editBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    openEditModal(t);
                });

                deleteBtn.addEventListener('click', (e) => {
                    e.stopImmediatePropagation();
                    e.preventDefault();
                    deletingTemplateId = t.id;
                    elements.deleteModal.show();
                });
            }

            elements.templateList.appendChild(item);
        });
    }


    function selectTemplate(template) {
        // Hide sidebar on mobile if offcanvas is active
        if (sidebarOffcanvas && window.innerWidth < 1200) {
            sidebarOffcanvas.hide();
        }

        showView('editor');

        currentTemplate = template;
        renderTemplateList(); // Re-render to highlight active

        elements.editorTitle.textContent = template.name;

        // Use the saved group metadata if it exists, otherwise use template.id
        const groupName = (template.group_meta && template.group_meta.name) || template.id;
        const rulesBlock = {
            groups: [{
                ...template.group_meta,
                name: groupName,
                rules: template.rules
            }]
        };

        const yamlStr = jsyaml.dump(rulesBlock, { lineWidth: -1, noRefs: true });
        elements.yamlEditor.value = yamlStr;

        validate(yamlStr);
    }

    // =========================================================================
    // Logic: Validation & Editing
    // =========================================================================



    function debouncedValidate() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => validate(elements.yamlEditor.value), 500);
    }

    async function validate(content) {
        // Reset UI pending states
        elements.validationIcon.className = 'spinner-border spinner-border-sm text-secondary';
        elements.validationMsg.textContent = "Checking...";
        elements.validationMsg.className = "fw-medium text-muted";

        elements.promqlStatus.className = 'badge bg-dark border border-secondary text-muted';
        elements.promqlStatus.textContent = 'PromQL: ...';

        elements.errorOneLine.classList.add('d-none');
        elements.errorOneLine.textContent = '';

        elements.copyBtn.disabled = true;
        elements.downloadBtn.disabled = true;

        try {
            const res = await fetch('/api/validate/yaml', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: content, type: 'rule' })
            });
            const result = await res.json();

            if (result.valid) {
                // Success State
                elements.validationIcon.className = 'bi bi-check-circle-fill text-success';
                elements.validationMsg.textContent = "Valid YAML";
                elements.validationMsg.className = "fw-bold text-success";

                elements.promqlStatus.className = 'badge bg-success bg-opacity-25 text-success border border-success';
                elements.promqlStatus.textContent = `PromQL: OK (${result.promql_checked})`;

                elements.copyBtn.disabled = false;
                elements.downloadBtn.disabled = false;
            } else {
                // Failure State
                elements.validationIcon.className = 'bi bi-exclamation-circle-fill text-danger';
                elements.validationMsg.textContent = "Invalid";
                elements.validationMsg.className = "fw-bold text-danger";

                // Show first error in the banner
                elements.errorOneLine.classList.remove('d-none');
                elements.errorOneLine.textContent = result.errors[0] || "Unknown error";

                if (result.promql_invalid > 0) {
                    elements.promqlStatus.className = 'badge bg-danger bg-opacity-25 text-danger border border-danger';
                    elements.promqlStatus.textContent = `PromQL: ${result.promql_invalid} Errors`;
                }
            }
        } catch (err) {
            elements.validationIcon.className = 'bi bi-x-circle-fill text-danger';
            elements.validationMsg.textContent = "Server Error";
        }
    }

    async function runLiveQuery() {
        // 1. Get query from editor
        let query = "";
        try {
            const doc = jsyaml.load(elements.yamlEditor.value);
            // Try to find expression in first rule
            if (doc && doc.groups && doc.groups[0] && doc.groups[0].rules && doc.groups[0].rules[0]) {
                query = doc.groups[0].rules[0].expr;
            }
        } catch (e) {
            showErrorModal("Could not parse YAML to find 'expr'. Please fix YAML first.");
            return;
        }

        if (!query) {
            showErrorModal("No expression found in the first rule.");
            return;
        }

        // 2. Get URL
        const url = elements.promUrl.value || elements.promUrl.placeholder;

        // 3. UI Loading state
        elements.testQueryBtn.disabled = true;
        elements.testQueryBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...';
        elements.queryResultArea.classList.add('d-none');

        try {
            const res = await fetch('/api/proxy/promql', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url, query: query })
            });
            const result = await res.json();

            // 4. Show Result
            elements.queryResultArea.classList.remove('d-none');

            if (result.valid) {
                // Format JSON nicely
                const status = result.data.status;
                const data = result.data.data || {};
                let output = `Status: ${status}\n`;

                if (data.resultType) {
                    output += `Type: ${data.resultType}\n`;
                    const count = data.result ? data.result.length : 0;
                    output += `Count: ${count}\n\n`;

                    if (count > 0) {
                        // Show first 5 results
                        data.result.slice(0, 5).forEach((item, idx) => {
                            output += `--- Result ${idx + 1} ---\n`;
                            output += `Labels: ${JSON.stringify(item.metric)}\n`;
                            output += `Value: ${JSON.stringify(item.value || item.values)}\n`;
                        });
                        if (count > 5) output += `\n... (+${count - 5} more)`;
                    } else {
                        output += "No Data returned for this query.";
                    }
                } else {
                    output += JSON.stringify(data, null, 2);
                }
                elements.queryResultContent.textContent = output;
                elements.queryResultContent.className = "m-0 p-2 text-info small font-monospace";
            } else {
                elements.queryResultContent.textContent = "Error: " + (result.error || "Unknown error");
                elements.queryResultContent.className = "m-0 p-2 text-danger small font-monospace";
            }

        } catch (err) {
            elements.queryResultArea.classList.remove('d-none');
            elements.queryResultContent.textContent = "Network/Server Error: " + err.message;
            elements.queryResultContent.className = "m-0 p-2 text-danger small font-monospace";
        } finally {
            elements.testQueryBtn.disabled = false;
            elements.testQueryBtn.innerHTML = '<i class="bi bi-play-fill"></i> Test Query';
        }
    }

    // =========================================================================
    // Utilities
    // =========================================================================

    function copyToClipboard() {
        navigator.clipboard.writeText(elements.yamlEditor.value).then(() => {
            elements.toast.show();
        });
    }

    function downloadFile() {
        const blob = new Blob([elements.yamlEditor.value], { type: 'text/yaml' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        let filename = 'rules.yml';
        if (currentTemplate) {
            filename = `${currentTemplate.name.toLowerCase().replace(/ /g, '_')}.yml`;
        }
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    // =========================================================================
    // ADMIN FUNCTIONS
    // =========================================================================

    async function checkAdminStatus() {
        try {
            // First check if setup is needed
            const setupRes = await fetch('/api/admin/setup-required');
            const setupData = await setupRes.json();
            if (setupData.setup_required) {
                elements.setupModal.show();
                return;
            }

            const res = await fetch('/api/admin/status');
            const data = await res.json();
            updateAdminUI(data.logged_in);
        } catch (e) { console.error("Status check failed", e); }
    }

    async function handleSetup() {
        const password = elements.setupPasswordInput.value;
        const confirm = elements.setupConfirmInput.value;

        if (!password || password.length < 4) {
            showSetupError("Password must be at least 4 characters.");
            return;
        }
        if (password !== confirm) {
            showSetupError("Passwords do not match.");
            return;
        }

        try {
            const res = await fetch('/api/admin/setup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password })
            });
            const data = await res.json();
            if (res.ok) {
                elements.setupModal.hide();
                updateAdminUI(true);
                fetchTemplates();
            } else {
                showSetupError(data.error || "Setup failed");
            }
        } catch (e) {
            showSetupError("Connection error: " + e.message);
        }
    }

    function showSetupError(msg) {
        elements.setupErrorBanner.textContent = msg;
        elements.setupErrorBanner.classList.remove('d-none');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showErrorModal(msg) {
        elements.errorModalMessage.textContent = msg;
        elements.errorModal.show();
    }

    function updateAdminUI(logged_in) {
        isAdmin = logged_in;
        if (isAdmin) {
            elements.adminLoginBtn.classList.add('d-none');
            elements.adminLogoutBtn.classList.remove('d-none');
            elements.adminAddContainer.classList.remove('d-none');
        } else {
            elements.adminLoginBtn.classList.remove('d-none');
            elements.adminLogoutBtn.classList.add('d-none');
            elements.adminAddContainer.classList.add('d-none');
        }
        renderTemplateList(); // Re-render to show/hide Edit/Delete buttons
    }

    async function handleLogin() {
        const password = elements.adminPasswordInput.value;
        elements.loginErrorBanner.classList.add('d-none');

        try {
            const res = await fetch('/api/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password })
            });
            if (res.ok) {
                elements.loginModal.hide();
                updateAdminUI(true);
            } else {
                const data = await res.json();
                showLoginError(data.error || "Invalid password");
            }
        } catch (e) { showLoginError("Login error: " + e.message); }
    }

    function showLoginError(msg) {
        elements.loginErrorBanner.textContent = msg;
        elements.loginErrorBanner.classList.remove('d-none');
    }

    async function handleLogout() {
        await fetch('/api/admin/logout', { method: 'POST' });
        updateAdminUI(false);
    }

    function openAddModal() {
        editingRuleId = null;
        elements.ruleModalTitle.textContent = "Add New Template";
        elements.ruleNameInput.value = "";
        elements.ruleJobInput.value = "";
        elements.ruleDescInput.value = "";
        elements.ruleTypesInput.value = "custom";
        elements.ruleYamlInput.value = 'groups:\n  - name: example\n    rules:\n      - alert: HostHighCpuLoad\n        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100) > 80\n        for: 0m\n        labels:\n          severity: warning\n        annotations:\n          summary: "Host high CPU load (instance {{ $labels.instance }})"';

        elements.modalErrorBanner.classList.add('d-none');
        validateModalYaml();
        elements.ruleModal.show();
    }

    function openEditModal(t) {
        editingRuleId = t.id;
        elements.ruleModalTitle.textContent = `Edit: ${t.name}`;
        elements.ruleNameInput.value = t.name;
        elements.ruleJobInput.value = t.job;
        elements.ruleDescInput.value = t.description || "";
        elements.ruleTypesInput.value = (t.alert_types || []).join(", ");

        const groupName = (t.group_meta && t.group_meta.name) || t.id;
        const rulesBlock = {
            groups: [{
                ...t.group_meta,
                name: groupName,
                rules: t.rules
            }]
        };
        elements.ruleYamlInput.value = jsyaml.dump(rulesBlock, { lineWidth: -1, noRefs: true });

        elements.modalErrorBanner.classList.add('d-none');
        validateModalYaml();
        elements.ruleModal.show();
    }

    async function validateModalYaml() {
        const content = elements.ruleYamlInput.value;
        elements.modalValidationBadge.className = 'badge bg-dark text-muted';
        elements.modalValidationBadge.textContent = 'Checking...';

        try {
            const res = await fetch('/api/validate/yaml', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });
            const data = await res.json();
            if (data.valid) {
                elements.modalValidationBadge.className = 'badge bg-success';
                elements.modalValidationBadge.textContent = 'Valid YAML & PromQL';
            } else {
                elements.modalValidationBadge.className = 'badge bg-danger';
                elements.modalValidationBadge.textContent = 'Invalid';
            }
        } catch (e) {
            elements.modalValidationBadge.textContent = 'Error';
        }
    }

    async function saveRule() {
        const name = elements.ruleNameInput.value;
        const job = elements.ruleJobInput.value;
        const desc = elements.ruleDescInput.value;
        const types = elements.ruleTypesInput.value.split(',').map(s => s.trim()).filter(Boolean);
        let rulesArr = [];
        let ruleGroup = {};

        try {
            const doc = jsyaml.load(elements.ruleYamlInput.value);
            if (doc && doc.groups && doc.groups[0] && doc.groups[0].rules) {
                ruleGroup = doc.groups[0];
                rulesArr = doc.groups[0].rules;
            } else {
                throw new Error("Invalid structure. Must have 'groups' with 'rules'.");
            }
        } catch (e) {
            showModalError("YAML Error: " + e.message);
            return;
        }

        const payload = {
            name, job, description: desc, alert_types: types,
            rules: rulesArr,
            rules_logic: ruleGroup // Send the full group object
        };

        const url = editingRuleId ? `/api/admin/rules/${editingRuleId}` : '/api/admin/rules';
        const method = editingRuleId ? 'PUT' : 'POST';

        try {
            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok) {
                elements.ruleModal.hide();

                // If we edited the current template, update it locally too
                if (editingRuleId === (currentTemplate ? currentTemplate.id : null)) {
                    // Refresh currentTemplate data locally
                    const updatedRule = {
                        ...payload,
                        id: editingRuleId,
                        group_meta: { ...ruleGroup }
                    };
                    delete updatedRule.group_meta.rules; // Keep metadata only
                    currentTemplate = updatedRule;
                    elements.editorTitle.textContent = updatedRule.name;
                }

                fetchTemplates();
            } else {
                showModalError(data.errors ? data.errors.join('<br>') : data.error);
            }
        } catch (e) { showModalError("Save failed: " + e.message); }
    }

    async function deleteRule(id) {
        try {
            const res = await fetch(`/api/admin/rules/${id}`, { method: 'DELETE' });
            if (res.ok) fetchTemplates();
            else showErrorModal("Delete failed");
        } catch (e) { showErrorModal("Delete error: " + e.message); }
    }

    function showModalError(msg) {
        elements.modalErrorBanner.textContent = msg;
        elements.modalErrorBanner.classList.remove('d-none');
    }
});

