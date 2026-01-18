document.addEventListener('DOMContentLoaded', () => {
    // State
    let allTemplates = [];
    let currentTemplate = null;
    let debounceTimer = null;

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
        reloadBtn: document.getElementById('reloadBtn'),
        toast: new bootstrap.Toast(document.getElementById('liveToast')),
        // Live Test Headers
        promUrl: document.getElementById('promUrl'),
        testQueryBtn: document.getElementById('testQueryBtn'),
        queryResultArea: document.getElementById('queryResultArea'),
        queryResultContent: document.getElementById('queryResultContent')
    };

    // Initialization
    // =========================================================================
    fetchTemplates();
    initTheme();

    // Event Listeners
    elements.reloadBtn.addEventListener('click', () => {
        animateReload();
        fetchTemplates();
    });

    // Theme Selector
    document.querySelectorAll('[data-theme-value]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const theme = item.getAttribute('data-theme-value');
            setTheme(theme);
        });
    });

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



    elements.copyBtn.addEventListener('click', copyToClipboard);
    elements.downloadBtn.addEventListener('click', downloadFile);
    elements.testQueryBtn.addEventListener('click', runLiveQuery);

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
            elements.templateList.innerHTML = `<div class="text-center text-danger mt-5">Error: ${err.message}</div>`;
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
            // Using small text and compact padding for sidebar list
            item.className = `list-group-item p-2 mb-1 rounded border-secondary ${currentTemplate && currentTemplate.id === t.id ? 'active' : ''}`;
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-center w-100">
                    <h6 class="mb-0 text-truncate" style="font-size: 0.9rem;">${t.name}</h6>
                    <small class="text-muted ms-2" style="font-size: 0.7rem;">${t.job}</small>
                </div>
            `;
            item.onclick = () => selectTemplate(t);
            elements.templateList.appendChild(item);
        });
    }

    function selectTemplate(template) {
        currentTemplate = template;
        renderTemplateList(); // Re-render to highlight active

        const rule = template.rules[0] || {};

        elements.editorTitle.textContent = template.name;


        const rulesBlock = {
            groups: [{
                name: template.id,
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
            alert("Could not parse YAML to find 'expr'. Please fix YAML first.");
            return;
        }

        if (!query) {
            alert("No expression found in the first rule.");
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

    function animateReload() {
        const icon = elements.reloadBtn.querySelector('i');
        icon.classList.add('spin-animation');
        elements.reloadBtn.disabled = true;
        setTimeout(() => {
            elements.reloadBtn.disabled = false;
            icon.classList.remove('spin-animation');
        }, 1000);
    }
});
