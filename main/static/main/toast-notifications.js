document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toasts = container.querySelectorAll('.custom-toast');
    
    toasts.forEach((toast, index) => {
        setTimeout(() => {
            toast.classList.add('show');
            
            setTimeout(() => {
                toast.classList.remove('show');
                toast.classList.add('hide');
                
                setTimeout(() => {
                    toast.remove();
                    if (container.children.length === 0) {
                        container.remove();
                    }
                }, 300);
            }, 7000);
        }, index * 150);
    });
});
