/**
 * LibraVerse - 3D Interactive Physics, Tilt Engine & Hero Parallax
 * Implements smooth perspective transforms, dynamic shadows, and cursor-follow lighting.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Check user preference for reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
        console.log('[LibraVerse 3D] Reduced motion enabled. Disabling 3D tilt & parallax.');
        return;
    }

    initHeroParallax();
    init3DCardTilt();
});

/* --------------------------------------------------------------------------
   1. Hero Mouse Parallax (Multi-Depth Space Simulation)
   -------------------------------------------------------------------------- */
function initHeroParallax() {
    const hero = document.getElementById('heroUniverse');
    if (!hero) return;

    const parallaxLayers = hero.querySelectorAll('[data-parallax-depth]');
    if (!parallaxLayers.length) return;

    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let isMouseOver = false;

    hero.addEventListener('mousemove', (e) => {
        const rect = hero.getBoundingClientRect();
        // Normalized coordinates from -1 to 1 relative to center
        targetX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        targetY = ((e.clientY - rect.top) / rect.height) * 2 - 1;
        isMouseOver = true;
    });

    hero.addEventListener('mouseleave', () => {
        targetX = 0;
        targetY = 0;
        isMouseOver = false;
    });

    // Smooth physics loop with spring lerp
    function animateParallax() {
        // Lerp factor
        const ease = 0.08;
        currentX += (targetX - currentX) * ease;
        currentY += (targetY - currentY) * ease;

        parallaxLayers.forEach(layer => {
            const depth = parseFloat(layer.getAttribute('data-parallax-depth')) || 0.1;
            const moveX = currentX * depth * 50;
            const moveY = currentY * depth * 50;
            const rotX = currentY * depth * 15;
            const rotY = -currentX * depth * 15;

            // Preserve existing keyframe animation or apply offset transform
            layer.style.transform = `translate3d(${moveX}px, ${moveY}px, 0) rotateX(${rotX}deg) rotateY(${rotY}deg)`;
        });

        requestAnimationFrame(animateParallax);
    }

    animateParallax();
}

/* --------------------------------------------------------------------------
   2. Interactive 3D Card Tilt with Dynamic Lighting Glare
   -------------------------------------------------------------------------- */
function init3DCardTilt() {
    const cards = document.querySelectorAll('.card-3d-interactive');

    cards.forEach(card => {
        const glare = card.querySelector('.card-3d-glare');
        const maxTilt = parseFloat(card.getAttribute('data-max-tilt')) || 12; // Maximum tilt angle in degrees

        let bounds;

        function updateBounds() {
            bounds = card.getBoundingClientRect();
        }

        card.addEventListener('mouseenter', () => {
            updateBounds();
            card.style.transition = 'transform 0.1s ease-out, box-shadow 0.2s ease';
            if (glare) glare.style.opacity = '1';
        });

        card.addEventListener('mousemove', (e) => {
            if (!bounds) updateBounds();

            const mouseX = e.clientX - bounds.left;
            const mouseY = e.clientY - bounds.top;

            const xPct = mouseX / bounds.width;
            const yPct = mouseY / bounds.height;

            // Compute 3D rotation angles
            const rotateX = ((0.5 - yPct) * maxTilt * 2).toFixed(2);
            const rotateY = ((xPct - 0.5) * maxTilt * 2).toFixed(2);

            // Dynamic card elevation & tilt
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(18px) scale3d(1.02, 1.02, 1.02)`;

            // Update dynamic glare position
            if (glare) {
                const glareX = (xPct * 100).toFixed(1);
                const glareY = (yPct * 100).toFixed(1);
                glare.style.background = `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255, 255, 255, 0.16) 0%, rgba(34, 211, 238, 0.08) 35%, transparent 70%)`;
            }

            // Soft directional dynamic shadow
            const shadowX = -rotateY * 1.5;
            const shadowY = rotateX * 1.5;
            card.style.boxShadow = `${shadowX}px ${shadowY + 18}px 35px -5px rgba(0, 0, 0, 0.65), 0 0 25px rgba(139, 92, 246, 0.35)`;
        });

        card.addEventListener('mouseleave', () => {
            // Smoothly ease back to default position
            card.style.transition = 'transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.5s ease';
            card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px) scale3d(1, 1, 1)';
            card.style.boxShadow = '';
            if (glare) {
                glare.style.opacity = '0';
            }
        });
    });
}
