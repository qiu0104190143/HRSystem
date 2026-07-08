/* ==========================================
   HR招聘管理系统 v2.0 — 全局交互脚本
   ========================================== */

// 全局变量存储图表实例
window.appCharts = {};

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function () {

    // === 侧边栏折叠 ===
    var toggle = document.getElementById('sidebarToggle');
    if (toggle) {
        toggle.addEventListener('click', function () {
            document.querySelector('.sidebar').classList.toggle('collapsed');
            document.querySelector('.main-area').classList.toggle('expanded');
            // 折叠后重绘图表
            setTimeout(function () {
                Object.values(window.appCharts).forEach(function (c) {
                    if (c && c.resize) c.resize();
                });
            }, 350);
        });
    }

    // === Toast自动消失 ===
    document.querySelectorAll('.custom-toast').forEach(function (toast) {
        setTimeout(function () {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(80px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(function () { if (toast.parentElement) toast.remove(); }, 300);
        }, 4000);
    });

    // === 上传区域 ===
    var uploadZone = document.querySelector('.upload-zone-new');
    var fileInput = document.getElementById('fileInput');
    var fileInfo = document.getElementById('fileInfo');
    var fileName = document.getElementById('fileName');

    if (uploadZone && fileInput) {
        uploadZone.addEventListener('click', function () { fileInput.click(); });
        uploadZone.addEventListener('dragover', function (e) {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });
        uploadZone.addEventListener('dragleave', function () {
            uploadZone.classList.remove('drag-over');
        });
        uploadZone.addEventListener('drop', function (e) {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                showFileInfo(e.dataTransfer.files);
            }
        });
        fileInput.addEventListener('change', function () {
            if (this.files.length > 0) showFileInfo(this.files);
        });
    }

    function showFileInfo(files) {
        if (!files) return;
        var fileList = files.length !== undefined ? files : [files];
        if (fileList.length === 0) return;
        if (fileList.length === 1) {
            if (fileName) fileName.textContent = fileList[0].name + ' (' + formatFileSize(fileList[0].size) + ')';
        } else {
            var totalSize = 0;
            for (var i = 0; i < fileList.length; i++) totalSize += fileList[i].size;
            if (fileName) fileName.textContent = fileList[0].name + ' 等 ' + fileList.length + ' 个文件 (' + formatFileSize(totalSize) + ')';
        }
        if (fileInfo) fileInfo.classList.remove('d-none');
    }

    // === 表单提交防重复 ===
    document.querySelectorAll('form:not([data-no-disable])').forEach(function (form) {
        form.addEventListener('submit', function () {
            var btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                var orig = btn.innerHTML;
                btn.setAttribute('data-orig', orig);
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>处理中';
                setTimeout(function () {
                    if (btn.disabled) {
                        btn.disabled = false;
                        btn.innerHTML = btn.getAttribute('data-orig') || orig;
                    }
                }, 10000);
            }
        });
    });

    // === 初始化仪表盘图表 ===
    initDashboardCharts();

    // === 初始化匹配结果动画 ===
    initMatchAnimations();
});


// ===== 仪表盘图表 =====
function initDashboardCharts() {
    // 简历趋势
    var trendCtx = document.getElementById('resumeTrendChart');
    if (trendCtx) {
        fetch('/api/stats/resume-trend')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                window.appCharts.trend = new Chart(trendCtx, {
                    type: 'bar',
                    data: {
                        labels: data.map(function (d) { return d.date; }),
                        datasets: [{
                            label: '上传简历数',
                            data: data.map(function (d) { return d.count; }),
                            backgroundColor: 'rgba(79,110,247,0.7)',
                            borderColor: '#4f6ef7',
                            borderWidth: 1,
                            borderRadius: 8,
                            borderSkipped: false,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { stepSize: 1, font: { size: 11 } },
                                grid: { color: '#f0f0f0' }
                            },
                            x: {
                                ticks: { font: { size: 10 }, maxTicksLimit: 10 },
                                grid: { display: false }
                            }
                        }
                    }
                });
            });
    }

    // 学历分布
    var eduCtx = document.getElementById('educationPieChart');
    if (eduCtx) {
        fetch('/api/stats/education-dist')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var colors = ['#4f6ef7', '#10b981', '#f6b100', '#8b5cf6', '#f43f5e', '#14b8a6', '#f97316'];
                window.appCharts.edu = new Chart(eduCtx, {
                    type: 'doughnut',
                    data: {
                        labels: data.map(function (d) { return d.name; }),
                        datasets: [{
                            data: data.map(function (d) { return d.value; }),
                            backgroundColor: colors.slice(0, data.length),
                            borderWidth: 3,
                            borderColor: '#fff',
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, font: { size: 12 } } }
                        }
                    }
                });
            });
    }

    // 职位状态
    var statusCtx = document.getElementById('jobStatusChart');
    if (statusCtx) {
        fetch('/api/stats/job-status')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                window.appCharts.status = new Chart(statusCtx, {
                    type: 'doughnut',
                    data: {
                        labels: data.map(function (d) { return d.name; }),
                        datasets: [{
                            data: data.map(function (d) { return d.value; }),
                            backgroundColor: ['#10b981', '#9ca3af'],
                            borderWidth: 3,
                            borderColor: '#fff',
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, font: { size: 12 } } }
                        }
                    }
                });
            });
    }
}


// ===== 匹配结果动画 =====
function initMatchAnimations() {
    // 环形进度条动画
    document.querySelectorAll('.match-score-ring .fg-circle').forEach(function (circle) {
        var targetDash = parseFloat(circle.getAttribute('data-dash') || '0');
        var initial = parseFloat(circle.style.strokeDashoffset) || 283;
        circle.style.strokeDashoffset = initial;
        setTimeout(function () {
            circle.style.strokeDashoffset = targetDash;
        }, 300);
    });

    // 维度条动画
    document.querySelectorAll('.match-dim-fill').forEach(function (bar) {
        var targetW = bar.style.width;
        bar.style.width = '0%';
        setTimeout(function () {
            bar.style.width = targetW;
        }, 400);
    });
}


// ===== 全局工具函数 =====

// 确认删除（使用浏览器confirm，可替换为自定义模态框）
function confirmDelete(url, name) {
    if (confirm('确定要删除 "' + name + '" 吗？\n此操作不可恢复，请谨慎操作。')) {
        var form = document.getElementById('deleteForm');
        if (form) {
            form.action = url;
            form.submit();
        }
    }
}

// Modal确认（用于更友好的交互）
function confirmDeleteModal(url, name) {
    var dialog = document.createElement('div');
    dialog.className = 'modal-backdrop-custom';
    dialog.innerHTML =
        '<div class="modal-custom fade-in">' +
        '<h5 class="fw-bold mb-3"><i class="bi bi-exclamation-triangle text-danger me-2"></i>确认删除</h5>' +
        '<p class="mb-4">确定要删除 <strong>"' + name + '"</strong> 吗？此操作不可恢复。</p>' +
        '<div class="d-flex justify-content-end gap-2">' +
        '<button class="btn-custom btn-outline-custom" id="modalCancel">取消</button>' +
        '<button class="btn-custom btn-danger-custom" id="modalConfirm">确认删除</button>' +
        '</div></div>';
    document.body.appendChild(dialog);

    document.getElementById('modalCancel').addEventListener('click', function () { dialog.remove(); });
    document.getElementById('modalConfirm').addEventListener('click', function () {
        dialog.remove();
        var form = document.getElementById('deleteForm');
        if (form) { form.action = url; form.submit(); }
    });
    dialog.addEventListener('click', function (e) { if (e.target === dialog) dialog.remove(); });
}

// Toast通知
function showToast(message, type) {
    type = type || 'info';
    var icons = { success: 'bi-check-circle-fill', danger: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
    var container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    var toast = document.createElement('div');
    toast.className = 'custom-toast toast-' + type;
    toast.innerHTML =
        '<div class="toast-icon"><i class="bi ' + (icons[type] || icons.info) + '"></i></div>' +
        '<div class="toast-body">' + message + '</div>' +
        '<button class="toast-close" onclick="this.parentElement.remove()">&times;</button>';
    container.appendChild(toast);
    setTimeout(function () {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(80px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(function () { if (toast.parentElement) toast.remove(); }, 300);
    }, 3500);
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (!bytes) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '';
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr.slice(0, 10);
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

// 重置文件选择
function resetFile() {
    var fi = document.getElementById('fileInput');
    var div = document.getElementById('fileInfo');
    if (fi) fi.value = '';
    if (div) div.classList.add('d-none');
}
