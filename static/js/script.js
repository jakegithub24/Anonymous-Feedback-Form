/**
 * Feedback Form JavaScript
 * Handles form interactions, validation, and submission
 */

// Global variables
let currentSection = 1;
const totalSections = 3;
let formData = {};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    setupEventListeners();
    setupCharacterCounters();
});

/**
 * Initialize form functionality
 */
function initializeForm() {
    // Initialize star ratings
    initializeStarRatings();
    
    // Initialize form progress
    updateFormProgress();
    
    // Smooth scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Next section buttons
    document.querySelectorAll('.next-section').forEach(button => {
        button.addEventListener('click', goToNextSection);
    });
    
    // Previous section buttons
    document.querySelectorAll('.prev-section').forEach(button => {
        button.addEventListener('click', goToPreviousSection);
    });
    
    // Form submission
    const form = document.getElementById('feedbackForm');
    form.addEventListener('submit', handleFormSubmit);
    
    // Real-time validation
    document.querySelectorAll('input, textarea, select').forEach(element => {
        element.addEventListener('blur', validateField);
        element.addEventListener('input', validateField);
    });
    
    // Window resize handling
    window.addEventListener('resize', debounce(handleResize, 250));
}

/**
 * Initialize star rating functionality
 */
function initializeStarRatings() {
    const ratingContainers = document.querySelectorAll('.rating-stars');
    
    ratingContainers.forEach(container => {
        const inputs = container.querySelectorAll('input[type="radio"]');
        const labels = container.querySelectorAll('label');
        
        // Add hover effects
        labels.forEach(label => {
            label.addEventListener('mouseenter', function() {
                const rating = this.getAttribute('for').split('_')[1];
                highlightStars(container, rating);
            });
            
            label.addEventListener('mouseleave', function() {
                const checked = container.querySelector('input:checked');
                if (checked) {
                    highlightStars(container, checked.value);
                } else {
                    resetStars(container);
                }
            });
        });
        
        // Handle click
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                const rating = this.value;
                saveRatingData(container.dataset.field, rating);
                highlightStars(container, rating);
                validateField({ target: this });
            });
        });
    });
}

/**
 * Highlight stars up to given rating
 */
function highlightStars(container, rating) {
    const labels = container.querySelectorAll('label');
    const stars = container.querySelectorAll('.fa-star');
    
    labels.forEach(label => {
        const labelRating = label.getAttribute('for').split('_')[1];
        const star = label.querySelector('.fa-star');
        
        if (labelRating <= rating) {
            star.classList.remove('far');
            star.classList.add('fas', 'text-warning');
        } else {
            star.classList.remove('fas', 'text-warning');
            star.classList.add('far');
        }
    });
}

/**
 * Reset stars to default state
 */
function resetStars(container) {
    const stars = container.querySelectorAll('.fa-star');
    stars.forEach(star => {
        star.classList.remove('fas', 'text-warning');
        star.classList.add('far');
    });
}

/**
 * Save rating data to formData object
 */
function saveRatingData(field, value) {
    formData[field] = value;
    updateReviewSection();
}

/**
 * Set up character counters for textareas
 */
function setupCharacterCounters() {
    const textareas = document.querySelectorAll('textarea[maxlength]');
    
    textareas.forEach(textarea => {
        const maxLength = parseInt(textarea.getAttribute('maxlength'));
        const counterId = textarea.id + '_counter';
        const counter = document.getElementById(counterId);
        
        if (counter) {
            // Initial count
            updateCounter(textarea, counter, maxLength);
            
            // Update on input
            textarea.addEventListener('input', function() {
                updateCounter(this, counter, maxLength);
                validateField({ target: this });
            });
        }
    });
}

/**
 * Update character counter display
 */
function updateCounter(textarea, counter, maxLength) {
    const currentLength = textarea.value.length;
    counter.textContent = currentLength;
    
    // Visual feedback based on length
    const percentage = (currentLength / maxLength) * 100;
    
    if (percentage > 90) {
        counter.style.color = '#e74a3b';
        counter.style.fontWeight = 'bold';
    } else if (percentage > 75) {
        counter.style.color = '#f6c23e';
        counter.style.fontWeight = 'bold';
    } else {
        counter.style.color = '#6c757d';
        counter.style.fontWeight = 'normal';
    }
}

/**
 * Navigate to next section
 */
function goToNextSection(event) {
    event.preventDefault();
    
    // Validate current section before proceeding
    if (!validateCurrentSection()) {
        showValidationErrors();
        return;
    }
    
    // Save current section data
    saveCurrentSectionData();
    
    // Hide current section with animation
    const currentSectionElement = document.querySelector(`#section${currentSection}`);
    if (currentSectionElement) {
        currentSectionElement.style.opacity = '0';
        currentSectionElement.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            currentSectionElement.style.display = 'none';
            
            // Show next section
            currentSection++;
            const nextSectionElement = document.querySelector(`#section${currentSection}`);
            if (nextSectionElement) {
                nextSectionElement.style.display = 'block';
                setTimeout(() => {
                    nextSectionElement.style.opacity = '1';
                    nextSectionElement.style.transform = 'translateY(0)';
                }, 50);
            }
            
            updateFormProgress();
            updateNavigationButtons();
            
            // Scroll to top of section
            scrollToSection(nextSectionElement);
            
        }, 300);
    }
}

/**
 * Navigate to previous section
 */
function goToPreviousSection(event) {
    event.preventDefault();
    
    // Hide current section
    const currentSectionElement = document.querySelector(`#section${currentSection}`);
    if (currentSectionElement) {
        currentSectionElement.style.opacity = '0';
        currentSectionElement.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            currentSectionElement.style.display = 'none';
            
            // Show previous section
            currentSection--;
            const prevSectionElement = document.querySelector(`#section${currentSection}`);
            if (prevSectionElement) {
                prevSectionElement.style.display = 'block';
                setTimeout(() => {
                    prevSectionElement.style.opacity = '1';
                    prevSectionElement.style.transform = 'translateY(0)';
                }, 50);
            }
            
            updateFormProgress();
            updateNavigationButtons();
            
            // Scroll to top of section
            scrollToSection(prevSectionElement);
            
        }, 300);
    }
}

/**
 * Scroll to section smoothly
 */
function scrollToSection(element) {
    if (element) {
        const offset = 80; // Account for fixed navbar
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
}

/**
 * Validate current section
 */
function validateCurrentSection() {
    let isValid = true;
    
    // Get all required fields in current section
    const currentSectionElement = document.querySelector(`#section${currentSection}`);
    if (currentSectionElement) {
        const requiredFields = currentSectionElement.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!validateField({ target: field })) {
                isValid = false;
            }
        });
    }
    
    return isValid;
}

/**
 * Validate individual field
 */
function validateField(event) {
    const field = event.target;
    const isValid = checkFieldValidity(field);
    
    // Update UI based on validity
    if (field.value.trim() !== '') {
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
        }
    } else {
        field.classList.remove('is-valid', 'is-invalid');
    }
    
    return isValid;
}

/**
 * Check field validity
 */
function checkFieldValidity(field) {
    if (!field.hasAttribute('required') && !field.value.trim()) {
        return true; // Optional field
    }
    
    const value = field.value.trim();
    const type = field.type;
    const name = field.name;
    
    switch (type) {
        case 'radio':
            const radioGroup = document.querySelectorAll(`input[name="${name}"]:checked`);
            return radioGroup.length > 0;
            
        case 'textarea':
            if (field.hasAttribute('maxlength')) {
                const maxLength = parseInt(field.getAttribute('maxlength'));
                return value.length > 0 && value.length <= maxLength;
            }
            return value.length > 0;
            
        case 'number':
            const min = field.hasAttribute('min') ? parseInt(field.getAttribute('min')) : 1;
            const max = field.hasAttribute('max') ? parseInt(field.getAttribute('max')) : 5;
            const numValue = parseInt(value);
            return !isNaN(numValue) && numValue >= min && numValue <= max;
            
        default:
            return value.length > 0;
    }
}

/**
 * Show validation errors for current section
 */
function showValidationErrors() {
    const currentSectionElement = document.querySelector(`#section${currentSection}`);
    if (currentSectionElement) {
        const invalidFields = currentSectionElement.querySelectorAll('.is-invalid');
        
        if (invalidFields.length > 0) {
            // Scroll to first invalid field
            invalidFields[0].scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
            
            // Add shake animation to invalid fields
            invalidFields.forEach(field => {
                field.classList.add('shake');
                setTimeout(() => {
                    field.classList.remove('shake');
                }, 500);
            });
            
            // Show error message
            showToast('Please fill in all required fields correctly.', 'error');
        }
    }
}

/**
 * Shake animation CSS (added dynamically)
 */
const shakeAnimation = `
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
}
.shake {
    animation: shake 0.5s ease-in-out;
}
`;

// Add shake animation to document
const styleSheet = document.createElement('style');
styleSheet.textContent = shakeAnimation;
document.head.appendChild(styleSheet);

/**
 * Save current section data
 */
function saveCurrentSectionData() {
    const currentSectionElement = document.querySelector(`#section${currentSection}`);
    if (currentSectionElement) {
        const inputs = currentSectionElement.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            if (input.name) {
                if (input.type === 'radio') {
                    if (input.checked) {
                        formData[input.name] = input.value;
                    }
                } else if (input.type === 'checkbox') {
                    formData[input.name] = input.checked;
                } else {
                    formData[input.name] = input.value.trim();
                }
            }
        });
    }
    
    // Update review section if we're on the last section
    if (currentSection === totalSections - 1) {
        updateReviewSection();
    }
}

/**
 * Update review section with collected data
 */
function updateReviewSection() {
    const reviewContent = document.querySelector('.review-content');
    if (!reviewContent) return;
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <h6 class="fw-semibold mb-3">Ratings Summary</h6>
                <div class="review-item">
                    <strong>Content Quality:</strong>
                    <div class="float-end">
                        ${getStarRating(formData.content_quality || 0)}
                        <span class="ms-2">${formData.content_quality || 'Not rated'}/5</span>
                    </div>
                </div>
                <div class="review-item">
                    <strong>Clarity of Explanations:</strong>
                    <div class="float-end">
                        ${getStarRating(formData.clarity || 0)}
                        <span class="ms-2">${formData.clarity || 'Not rated'}/5</span>
                    </div>
                </div>
                <div class="review-item">
                    <strong>Engagement Level:</strong>
                    <div class="float-end">
                        ${getStarRating(formData.engagement || 0)}
                        <span class="ms-2">${formData.engagement || 'Not rated'}/5</span>
                    </div>
                </div>
                <div class="review-item">
                    <strong>Overall Satisfaction:</strong>
                    <div class="float-end">
                        ${getStarRating(formData.satisfaction || 0)}
                        <span class="ms-2">${formData.satisfaction || 'Not rated'}/5</span>
                    </div>
                </div>
                <div class="review-item">
                    <strong>Apply Likelihood:</strong>
                    <div class="float-end">
                        ${getStarRating(formData.apply_likelihood || 0)}
                        <span class="ms-2">${formData.apply_likelihood || 'Not rated'}/5</span>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <h6 class="fw-semibold mb-3">Feedback Summary</h6>
                <div class="review-item">
                    <strong>Recommend to Others:</strong>
                    <span class="float-end badge ${formData.recommend === 'Yes' ? 'bg-success' : 'bg-danger'}">
                        ${formData.recommend || 'Not answered'}
                    </span>
                </div>
                <div class="review-item">
                    <strong>Most Valuable:</strong>
                    <div class="mt-2 text-muted small">
                        ${truncateText(formData.most_valuable || 'Not provided', 100)}
                    </div>
                </div>
                <div class="review-item">
                    <strong>Improvements Suggested:</strong>
                    <div class="mt-2 text-muted small">
                        ${truncateText(formData.improvements || 'Not provided', 100)}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    reviewContent.innerHTML = html;
}

/**
 * Get star rating HTML
 */
function getStarRating(rating) {
    if (!rating || rating < 1) return 'Not rated';
    
    let stars = '';
    for (let i = 0; i < 5; i++) {
        if (i < rating) {
            stars += '<i class="fas fa-star text-warning"></i>';
        } else {
            stars += '<i class="far fa-star text-muted"></i>';
        }
    }
    return stars;
}

/**
 * Truncate text with ellipsis
 */
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Update form progress bar
 */
function updateFormProgress() {
    const progress = (currentSection / totalSections) * 100;
    const progressBar = document.getElementById('formProgress');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
    }
}

/**
 * Update navigation buttons state
 */
function updateNavigationButtons() {
    // Update previous buttons
    document.querySelectorAll('.prev-section').forEach(button => {
        button.disabled = currentSection === 1;
    });
    
    // Update next buttons text
    const nextButtons = document.querySelectorAll('.next-section');
    nextButtons.forEach(button => {
        if (currentSection === totalSections - 1) {
            button.textContent = 'Review & Submit';
            button.classList.remove('btn-primary', 'btn-info');
            button.classList.add('btn-warning');
        } else if (currentSection === totalSections) {
            button.style.display = 'none';
        }
    });
}

/**
 * Handle form submission
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    
    // Final validation
    if (!validateCurrentSection()) {
        showValidationErrors();
        return;
    }
    
    // Save all data
    saveCurrentSectionData();
    
    // Show loading indicator
    showLoading(true);
    
    try {
        // Prepare form data
        const form = new FormData();
        Object.keys(formData).forEach(key => {
            form.append(key, formData[key]);
        });
        
        // Submit to server
        const response = await fetch('/submit-feedback', {
            method: 'POST',
            body: form
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show success message
            showSuccess();
            
            // Redirect if URL provided
            if (result.redirect) {
                setTimeout(() => {
                    window.location.href = result.redirect;
                }, 3000);
            }
        } else {
            // Show error message
            showError(result.message || 'Submission failed. Please try again.');
        }
        
    } catch (error) {
        console.error('Submission error:', error);
        showError('Network error. Please check your connection and try again.');
    } finally {
        showLoading(false);
    }
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const form = document.getElementById('feedbackForm');
    
    if (loading && form) {
        if (show) {
            loading.style.display = 'block';
            form.style.opacity = '0.5';
            form.style.pointerEvents = 'none';
            
            // Add loading animation
            loading.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Submitting...</span>
                </div>
                <p class="mt-2 text-muted">Submitting your feedback...</p>
                <div class="progress mt-3" style="height: 4px; width: 200px; margin: 0 auto;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
                </div>
            `;
        } else {
            loading.style.display = 'none';
            form.style.opacity = '1';
            form.style.pointerEvents = 'auto';
        }
    }
}

/**
 * Show success message
 */
function showSuccess() {
    const success = document.getElementById('successMessage');
    const form = document.getElementById('feedbackForm');
    
    if (success && form) {
        form.style.display = 'none';
        success.style.display = 'block';
        
        // Add success animation
        success.style.animation = 'slideIn 0.5s ease-out';
        
        // Scroll to success message
        success.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Show error message
 */
function showError(message) {
    const error = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    
    if (error && errorText) {
        errorText.textContent = message;
        error.style.display = 'block';
        
        // Add error animation
        error.style.animation = 'shake 0.5s ease-in-out';
        
        // Scroll to error message
        error.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Retry submission
 */
function retrySubmission() {
    const error = document.getElementById('errorMessage');
    if (error) {
        error.style.display = 'none';
    }
    handleFormSubmit(new Event('submit'));
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.custom-toast');
    existingToasts.forEach(toast => toast.remove());
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = `custom-toast alert alert-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideInRight 0.3s ease-out;
    `;
    
    toast.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <i class="fas ${type === 'error' ? 'fa-exclamation-triangle' : 'fa-info-circle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

/**
 * Add slide animations
 */
const toastAnimations = `
@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}
`;

// Add toast animations to document
const toastStyleSheet = document.createElement('style');
toastStyleSheet.textContent = toastAnimations;
document.head.appendChild(toastStyleSheet);

/**
 * Handle window resize
 */
function handleResize() {
    // Update any responsive elements if needed
    updateFormProgress();
}

/**
 * Debounce function for resize events
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Export form data (for debugging)
 */
function exportFormData() {
    console.log('Form Data:', formData);
    return formData;
}

// Make functions available globally for debugging
window.exportFormData = exportFormData;
window.validateCurrentSection = validateCurrentSection;
