window.addEventListener('load', function () {
    const tbody = document.querySelector('.total-table tbody');
    const thead = document.querySelector('.total-table thead');

    function adjustHeaderWidth() {
        const hasScrollBar = tbody.scrollHeight > tbody.clientHeight;
        thead.style.width = hasScrollBar ? 'calc(100% - 20px)' : '100%';
    }

    adjustHeaderWidth();
    window.addEventListener('resize', adjustHeaderWidth);
});
