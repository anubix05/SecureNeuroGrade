/**
 * SecureNeuroGrade — Client-Side JavaScript
 * ==========================================
 * Client-side validation and UI enhancements.
 *
 * NOTE: All validation here is for user convenience only.
 * The backend independently enforces all restrictions.
 */

document.addEventListener('DOMContentLoaded', function () {
    initThemeToggle();
    initSidebarToggle();
    initFileUpload();
    initFlashAutoDismiss();
    initUniversalBackBtn();
});


/**
 * Mobile Sidebar Toggle
 * Opens/closes the slide-in sidebar on small screens via the hamburger button.
 */
function initSidebarToggle() {
    const sidebar    = document.getElementById('sidebar');
    const toggleBtn  = document.getElementById('sidebar-toggle');
    const overlay    = document.getElementById('sidebar-overlay');

    if (!sidebar || !toggleBtn) return;

    function openSidebar() {
        sidebar.classList.add('open');
        if (overlay) {
            overlay.style.display = 'block';
            // Force reflow so transition fires
            overlay.getBoundingClientRect();
            overlay.classList.add('active');
        }
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(function () {
                overlay.style.display = 'none';
            }, 250); // match CSS transition duration
        }
        document.body.style.overflow = '';
    }

    toggleBtn.addEventListener('click', function () {
        if (sidebar.classList.contains('open')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }
}


/**
 * Light / Dark Theme Toggle Switcher with LocalStorage persistence
 */
function initThemeToggle() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeToggleIcon = themeToggleBtn?.querySelector('.theme-toggle-icon');

    // Get current theme from html attribute or default to dark
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    updateToggleIcon(currentTheme);

    if (!themeToggleBtn) return;

    themeToggleBtn.addEventListener('click', function () {
        const activeTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = activeTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('sng_theme', newTheme);
        updateToggleIcon(newTheme);
    });

    function updateToggleIcon(theme) {
        if (themeToggleIcon) {
            const sunSvg = '<svg class="ui-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';
            const moonSvg = '<svg class="ui-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>';
            themeToggleIcon.innerHTML = theme === 'dark' ? sunSvg : moonSvg;
            themeToggleBtn.setAttribute('title', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
        }
    }
}


/**
 * File Upload Area — drag & drop + file info display
 */
function initFileUpload() {
    const fileInput = document.getElementById('scan_file');
    const uploadArea = document.getElementById('file-upload-area');
    const uploadContent = uploadArea?.querySelector('.file-upload-content');
    const fileSelected = document.getElementById('file-selected');
    const fileSelectedName = document.getElementById('file-selected-name');
    const fileSelectedSize = document.getElementById('file-selected-size');

    if (!fileInput || !uploadArea) return;

    // Allowed extensions (client-side hint only; backend enforces)
    const allowedExtensions = ['png', 'jpg', 'jpeg', 'tif', 'tiff', 'dcm', 'nii'];
    const maxSizeMB = 50;

    fileInput.addEventListener('change', function () {
        const file = this.files[0];
        if (!file) return;

        // Client-side extension check
        const ext = file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(ext)) {
            alert(
                'Unsupported file type (.' + ext + '). ' +
                'Supported formats: ' + allowedExtensions.join(', ')
            );
            this.value = '';
            return;
        }

        // Client-side size check
        const sizeMB = file.size / (1024 * 1024);
        if (sizeMB > maxSizeMB) {
            alert(
                'File is too large (' + sizeMB.toFixed(1) + ' MB). ' +
                'Maximum size is ' + maxSizeMB + ' MB.'
            );
            this.value = '';
            return;
        }

        // Show selected file info
        if (uploadContent) uploadContent.style.display = 'none';
        if (fileSelected) fileSelected.style.display = 'flex';
        if (fileSelectedName) fileSelectedName.textContent = file.name;
        if (fileSelectedSize) {
            fileSelectedSize.textContent = '(' + formatFileSize(file.size) + ')';
        }
    });

    // Drag and drop visual feedback
    uploadArea.addEventListener('dragover', function (e) {
        e.preventDefault();
        this.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function () {
        this.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function (e) {
        this.classList.remove('dragover');
    });
}


/**
 * Auto-dismiss flash messages after 8 seconds
 */
function initFlashAutoDismiss() {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (flash) {
        setTimeout(function () {
            flash.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            setTimeout(function () { flash.remove(); }, 500);
        }, 8000);
    });
}


/**
 * Format file size to human-readable string
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}


/**
 * Universal Back Button Handler
 * Enables top back buttons (.back-btn) to navigate back to whichever page the user
 * arrived from (via document.referrer/history.back()). If opened directly, falls back
 * to data-fallback URL or dashboard.
 */
function initUniversalBackBtn() {
    document.addEventListener('click', function (e) {
        const backBtn = e.target.closest('.back-btn');
        if (!backBtn) return;

        e.preventDefault();

        const fallbackUrl = backBtn.getAttribute('data-fallback') || backBtn.getAttribute('href') || '/';
        const referrer = document.referrer;
        const currentOrigin = window.location.origin;

        // Check if referrer exists, is from the same domain, and is not the current page or login
        if (
            referrer &&
            referrer.startsWith(currentOrigin) &&
            referrer !== window.location.href &&
            !referrer.includes('/auth/login')
        ) {
            window.history.back();
        } else if (fallbackUrl && fallbackUrl !== 'javascript:void(0);' && fallbackUrl !== 'javascript:history.back()') {
            window.location.href = fallbackUrl;
        } else {
            window.history.back();
        }
    });
}
