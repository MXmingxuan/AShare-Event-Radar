document.addEventListener('DOMContentLoaded', () => {
    // ========== DOM References ==========
    const form = document.getElementById('radar-form');
    const btn = document.getElementById('generateBtn');
    const emptyState = document.getElementById('emptyState');
    const loadingState = document.getElementById('loadingState');
    const reportContainer = document.getElementById('reportContainer');
    const steps = document.querySelectorAll('.loading-steps .step');

    const configForm = document.getElementById('config-form');
    const apiKeyInput = document.getElementById('apiKey');
    const modelSelect = document.getElementById('modelSelect');
    const saveMsg = document.getElementById('saveMsg');

    const navBtns = document.querySelectorAll('.nav-btn');
    const viewSections = document.querySelectorAll('.view-section');
    const radarFormSection = document.getElementById('radar-form');

    // ========== Tab Navigation ==========
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.target;

            // Toggle active nav button
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Toggle visible view
            viewSections.forEach(v => {
                v.classList.remove('active');
                v.classList.add('hidden');
            });
            const target = document.getElementById(targetId);
            if (target) {
                target.classList.remove('hidden');
                target.classList.add('active');
            }

            // Show/hide the sidebar form (only visible on radar tab)
            if (targetId === 'view-radar') {
                radarFormSection.style.display = 'block';
            } else {
                radarFormSection.style.display = 'none';
            }
        });
    });

    // ========== Settings: Load from localStorage ==========
    function loadSettings() {
        const savedKey = localStorage.getItem('radar_api_key') || '';
        const savedModel = localStorage.getItem('radar_model') || 'MiniMax-M2.7';
        apiKeyInput.value = savedKey;
        modelSelect.value = savedModel;
    }
    loadSettings();

    // ========== Settings: Save to localStorage ==========
    configForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const key = apiKeyInput.value.trim();
        const model = modelSelect.value;

        localStorage.setItem('radar_api_key', key);
        localStorage.setItem('radar_model', model);

        // Show success feedback
        saveMsg.textContent = '✅ 配置已安全保存至浏览器本地存储！';
        saveMsg.classList.remove('hidden');
        setTimeout(() => saveMsg.classList.add('hidden'), 3000);
    });

    // ========== Radar: Submit Analysis ==========
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const symbol = document.getElementById('symbol').value;
        const daysBack = document.getElementById('daysBack').value;

        // Retrieve saved config
        const savedKey = localStorage.getItem('radar_api_key') || '';
        const savedModel = localStorage.getItem('radar_model') || 'MiniMax-M2.7';

        // Reset UI States
        emptyState.classList.add('hidden');
        reportContainer.classList.add('hidden');
        loadingState.classList.remove('hidden');
        reportContainer.innerHTML = '';

        // Disable button
        btn.disabled = true;
        btn.innerHTML = '<span class="btn-text">⏳ 处理中...</span>';

        // Loading Steps Animation
        let stepIndex = 0;
        const stepInterval = setInterval(() => {
            if (stepIndex < steps.length - 1) {
                steps[stepIndex].classList.remove('active');
                stepIndex++;
                steps[stepIndex].classList.add('active');
                steps[stepIndex].innerHTML = steps[stepIndex].innerHTML.replace('○', '●');
            }
        }, 12000);

        try {
            const payload = {
                symbol: symbol,
                days_back: parseInt(daysBack),
                model_name: savedModel
            };
            // Only inject api_key if user has explicitly set one
            if (savedKey) {
                payload.api_key = savedKey;
            }

            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            clearInterval(stepInterval);

            if (response.ok && data.report) {
                reportContainer.innerHTML = marked.parse(data.report);
                loadingState.classList.add('hidden');
                reportContainer.classList.remove('hidden');
            } else {
                loadingState.classList.add('hidden');
                reportContainer.classList.remove('hidden');
                reportContainer.innerHTML = `<h2 style="color: #ef4444;">❌ 错误</h2><p>${data.error || '运行失败'}</p>`;
            }
        } catch (error) {
            clearInterval(stepInterval);
            loadingState.classList.add('hidden');
            reportContainer.classList.remove('hidden');
            reportContainer.innerHTML = `<h2 style="color: #ef4444;">❌ 网络错误</h2><p>${error.message}</p>`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-text">🚀 发起雷达深描</span>';
            // Reset steps for next run
            steps.forEach((st, i) => {
                if (i === 0) {
                    st.classList.add('active');
                    st.innerHTML = '● Map单源截取中...';
                } else if (i === 1) {
                    st.classList.remove('active');
                    st.innerHTML = '○ Shuffle噪音剥离中...';
                } else {
                    st.classList.remove('active');
                    st.innerHTML = '○ M2.7 模型终评研判中...';
                }
            });
        }
    });
});
