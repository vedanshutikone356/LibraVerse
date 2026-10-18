/**
 * LibraVerse - Main JavaScript
 * Handles Navigation, Scroll Reveals, Animated Counters, Modals, and UI Helpers
 */

document.addEventListener('DOMContentLoaded', () => {
    initNavbarScroll();
    initScrollReveal();
    initNumberCounters();
    initBookDetailModal();
    initAlertDismiss();
});

/* --------------------------------------------------------------------------
   1. Navbar Scroll Effect
   -------------------------------------------------------------------------- */
function initNavbarScroll() {
    const navbar = document.querySelector('.cyber-navbar');
    if (!navbar) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 30) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }, { passive: true });
}

/* --------------------------------------------------------------------------
   2. Scroll Reveal via IntersectionObserver
   -------------------------------------------------------------------------- */
function initScrollReveal() {
    const revealElements = document.querySelectorAll('.reveal');
    if (!revealElements.length) return;

    const observerOptions = {
        root: null,
        rootMargin: '0px 0px -40px 0px',
        threshold: 0.15
    };

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    revealElements.forEach(el => revealObserver.observe(el));
}

/* --------------------------------------------------------------------------
   3. Animated Number Counters
   -------------------------------------------------------------------------- */
function initNumberCounters() {
    const counterElements = document.querySelectorAll('[data-counter]');
    if (!counterElements.length) return;

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const endVal = parseFloat(target.getAttribute('data-counter')) || 0;
                const duration = parseInt(target.getAttribute('data-duration')) || 1500;
                const isPercentage = target.hasAttribute('data-percentage');
                const isCurrency = target.hasAttribute('data-currency');

                animateValue(target, 0, endVal, duration, isPercentage, isCurrency);
                obs.unobserve(target);
            }
        });
    }, { threshold: 0.3 });

    counterElements.forEach(el => observer.observe(el));
}

function animateValue(obj, start, end, duration, isPercentage = false, isCurrency = false) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        // Ease-out cubic formula
        const ease = 1 - Math.pow(1 - progress, 3);
        const current = start + (end - start) * ease;

        if (Number.isInteger(end)) {
            obj.textContent = (isCurrency ? '$' : '') + Math.floor(current).toLocaleString() + (isPercentage ? '%' : '');
        } else {
            obj.textContent = (isCurrency ? '$' : '') + current.toFixed(1) + (isPercentage ? '%' : '');
        }

        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            if (Number.isInteger(end)) {
                obj.textContent = (isCurrency ? '$' : '') + end.toLocaleString() + (isPercentage ? '%' : '');
            } else {
                obj.textContent = (isCurrency ? '$' : '') + end.toFixed(1) + (isPercentage ? '%' : '');
            }
        }
    };
    window.requestAnimationFrame(step);
}

/* --------------------------------------------------------------------------
   4. Dynamic Book Detail Modal
   -------------------------------------------------------------------------- */
function initBookDetailModal() {
    const modalBackdrop = document.getElementById('bookDetailModal');
    if (!modalBackdrop) return;

    const closeBtns = modalBackdrop.querySelectorAll('[data-close-modal]');
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modalBackdrop.classList.remove('active');
        });
    });

    // Close when clicking outside content box
    modalBackdrop.addEventListener('click', (e) => {
        if (e.target === modalBackdrop) {
            modalBackdrop.classList.remove('active');
        }
    });

    // Delegate detail buttons
    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('[data-book-id]');
        if (!trigger || trigger.tagName.toLowerCase() === 'a' && trigger.getAttribute('href') !== '#') return;

        // If clicking a dedicated link, don't open modal
        if (trigger.hasAttribute('data-open-modal')) {
            e.preventDefault();
            const bookId = trigger.getAttribute('data-book-id');
            openBookModal(bookId);
        }
    });
}

function openBookModal(bookId) {
    const modalBackdrop = document.getElementById('bookDetailModal');
    if (!modalBackdrop) return;

    fetch(`/api/books/${bookId}`)
        .then(res => {
            if (!res.ok) throw new Error('Network error');
            return res.json();
        })
        .then(book => {
            document.getElementById('modalBookTitle').textContent = book.title;
            document.getElementById('modalBookAuthor').textContent = `by ${book.author}`;
            document.getElementById('modalBookCategory').textContent = book.category;
            document.getElementById('modalBookPublisher').textContent = book.publisher;
            document.getElementById('modalBookYear').textContent = book.publication_year;
            document.getElementById('modalBookISBN').textContent = book.isbn;
            document.getElementById('modalBookTotal').textContent = book.total_copies;
            document.getElementById('modalBookAvailable').textContent = book.available_copies;
            document.getElementById('modalBookIssued').textContent = book.total_copies - book.available_copies;
            document.getElementById('modalBookDescription').textContent = book.description || 'No description available for this title.';

            // Status badge
            const statusBadge = document.getElementById('modalBookStatus');
            if (book.available_copies > 0) {
                statusBadge.className = 'badge-cyber badge-available';
                statusBadge.textContent = `${book.available_copies} Available`;
            } else {
                statusBadge.className = 'badge-cyber badge-unavailable';
                statusBadge.textContent = 'Currently Checked Out';
            }

            // Cover Image
            const coverImg = document.getElementById('modalBookCover');
            const coverFallback = document.getElementById('modalBookFallback');
            if (book.cover_url) {
                coverImg.src = book.cover_url;
                coverImg.style.display = 'block';
                if (coverFallback) coverFallback.style.display = 'none';
            } else {
                coverImg.style.display = 'none';
                if (coverFallback) {
                    coverFallback.style.display = 'flex';
                    coverFallback.querySelector('.fallback-cover-title').textContent = book.title;
                    coverFallback.querySelector('.fallback-cover-author').textContent = book.author;
                }
            }

            // Dedicated Link
            const linkBtn = document.getElementById('modalViewDedicatedLink');
            if (linkBtn) {
                linkBtn.href = `/books/${book.id}`;
            }

            modalBackdrop.classList.add('active');
        })
        .catch(err => {
            console.error('Error loading book details:', err);
        });
}

/* --------------------------------------------------------------------------
   5. Image Error Fallback Handler
   -------------------------------------------------------------------------- */
window.handleImageError = function(imgElement, fallbackTitle, fallbackAuthor) {
    imgElement.style.display = 'none';
    const fallbackBox = imgElement.nextElementSibling;
    if (fallbackBox && fallbackBox.classList.contains('fallback-cover')) {
        fallbackBox.style.display = 'flex';
        const titleEl = fallbackBox.querySelector('.fallback-cover-title');
        const authorEl = fallbackBox.querySelector('.fallback-cover-author');
        if (titleEl) titleEl.textContent = fallbackTitle || 'LibraVerse Title';
        if (authorEl) authorEl.textContent = fallbackAuthor || 'Author';
    }
};

/* --------------------------------------------------------------------------
   6. Alert Dismissal
   -------------------------------------------------------------------------- */
function initAlertDismiss() {
    const alerts = document.querySelectorAll('.cyber-alert');
    alerts.forEach(alert => {
        // Auto-dismiss after 6 seconds
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 500);
        }, 6000);

        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.remove();
            });
        }
    });
}
