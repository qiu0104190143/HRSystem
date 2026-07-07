/* ==========================================
   HR招聘管理系统 — 全局交互脚本
   ========================================== */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function () {
    // 自动隐藏消息提示（5秒后）
    var alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            var closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });

    // 为所有表格添加hover效果
    var tables = document.querySelectorAll('.table-hover tbody tr');
    tables.forEach(function (row) {
        row.addEventListener('mouseenter', function () {
            this.style.backgroundColor = '#f8faff';
        });
        row.addEventListener('mouseleave', function () {
            this.style.backgroundColor = '';
        });
    });

    // 数字输入框的上下限限制
    var numberInputs = document.querySelectorAll('input[type="number"][min]');
    numberInputs.forEach(function (input) {
        input.addEventListener('blur', function () {
            var min = parseInt(this.min) || 0;
            var max = parseInt(this.max) || 999;
            var val = parseInt(this.value) || 0;
            if (val < min) this.value = min;
            if (val > max) this.value = max;
        });
    });

    // 表单提交时禁用提交按钮（防止重复提交）
    var forms = document.querySelectorAll('form');
    forms.forEach(function (form) {
        form.addEventListener('submit', function () {
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.classList.contains('no-disable')) {
                submitBtn.disabled = true;
                var originalText = submitBtn.innerHTML;
                submitBtn.setAttribute('data-original-text', originalText);
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>处理中...';
                // 5秒后恢复（防止卡住）
                setTimeout(function () {
                    if (submitBtn.disabled) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || originalText;
                    }
                }, 30000);
            }
        });
    });

    // 技能标签输入增强（如果有技能输入框）
    var skillInput = document.querySelector('input[name="skills"], input[name="skills_required"]');
    if (skillInput) {
        skillInput.addEventListener('keydown', function (e) {
            // 输入逗号后自动加空格
            if (e.key === ',') {
                var start = this.selectionStart;
                var end = this.selectionEnd;
                var val = this.value;
                if (val.charAt(start - 1) !== ' ') {
                    this.value = val.slice(0, start) + ', ' + val.slice(end);
                    this.selectionStart = this.selectionEnd = start + 2;
                    e.preventDefault();
                }
            }
        });
    }
});

// 通用确认弹窗
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '';
    var d = new Date(dateStr);
    return d.getFullYear() + '-' +
           String(d.getMonth() + 1).padStart(2, '0') + '-' +
           String(d.getDate()).padStart(2, '0');
}

// Toast消息（非阻塞提示）
function showToast(message, type) {
    type = type || 'info';
    var colors = {
        'success': '#10b981',
        'danger': '#ef4444',
        'warning': '#f59e0b',
        'info': '#3b82f6'
    };

    var toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;' +
                          'background:' + colors[type] + ';color:white;' +
                          'padding:12px 24px;border-radius:8px;' +
                          'box-shadow:0 4px 15px rgba(0,0,0,0.2);' +
                          'transition:opacity 0.3s ease;font-size:14px;';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(function () {
        toast.style.opacity = '0';
        setTimeout(function () {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}
