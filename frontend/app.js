/**
 * Accordo Agent - Frontend Application
 * Connects to the Python API to generate Concerto models
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const descriptionInput = document.getElementById('description-input');
const namespaceInput = document.getElementById('namespace-input');
const generateBtn = document.getElementById('generate-btn');
const copyBtn = document.getElementById('copy-btn');
const downloadBtn = document.getElementById('download-btn');
const outputContainer = document.getElementById('output-container');
const statusIndicator = document.getElementById('status-indicator');
const processingModal = document.getElementById('processing-modal');
const toast = document.getElementById('toast');

// State
let generatedCTO = '';
let isProcessing = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    generateBtn.addEventListener('click', handleGenerate);
    copyBtn.addEventListener('click', handleCopy);
    downloadBtn.addEventListener('click', handleDownload);

    // Enable enter key to generate
    descriptionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            handleGenerate();
        }
    });
});

/**
 * Handle Generate Button Click
 */
async function handleGenerate() {
    const description = descriptionInput.value.trim();

    if (!description) {
        showToast('Please enter a description', true);
        descriptionInput.focus();
        return;
    }

    if (isProcessing) return;

    isProcessing = true;
    setStatus('processing', 'Generating...');
    showProcessingModal();
    disableButtons(true);

    try {
        // Simulate step progression for better UX
        await updateStep(1, 'active');
        await delay(300);

        const namespace = namespaceInput.value.trim() || null;

        // Call the API
        const response = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description: description,
                namespace: namespace
            })
        });

        await updateStep(1, 'done');
        await updateStep(2, 'active');
        await delay(200);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate model');
        }

        const data = await response.json();

        await updateStep(2, 'done');
        await updateStep(3, 'active');
        await delay(200);
        await updateStep(3, 'done');
        await updateStep(4, 'active');
        await delay(200);
        await updateStep(4, 'done');

        // Success - display the CTO
        generatedCTO = data.cto;
        displayOutput(generatedCTO);

        setStatus('ready', 'Ready');
        showToast('Model generated successfully!');

    } catch (error) {
        console.error('Generation error:', error);
        setStatus('error', 'Error');
        showToast(error.message || 'Failed to generate model', true);

        // Show error in output
        outputContainer.innerHTML = `
            <div class="placeholder-message">
                <div class="placeholder-icon">❌</div>
                <p style="color: var(--error);">${error.message || 'Failed to generate model'}</p>
                <p class="placeholder-hint">Make sure the API server is running: python3 api.py</p>
            </div>
        `;
    } finally {
        isProcessing = false;
        hideProcessingModal();
        disableButtons(false);
    }
}

/**
 * Display CTO output with syntax highlighting
 */
function displayOutput(cto) {
    const highlighted = highlightCTO(cto);
    outputContainer.innerHTML = `<div class="code-output">${highlighted}</div>`;

    // Enable action buttons
    copyBtn.disabled = false;
    downloadBtn.disabled = false;
}

/**
 * Simple CTO syntax highlighting
 */
function highlightCTO(code) {
    return code
        // Comments
        .replace(/(\/\/.*$)/gm, '<span class="comment">$1</span>')
        .replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="comment">$1</span>')
        // Keywords
        .replace(/\b(namespace|concept|asset|participant|transaction|event|enum|abstract|extends|import|from)\b/g,
            '<span class="keyword">$1</span>')
        // Types
        .replace(/\b(String|Integer|Double|Long|Boolean|DateTime)\b/g,
            '<span class="type">$1</span>')
        // Property marker
        .replace(/(\s+o\s+)/g, '<span class="property">$1</span>')
        // Optional keyword
        .replace(/\b(optional)\b/g, '<span class="keyword">$1</span>');
}

/**
 * Copy to Clipboard
 */
async function handleCopy() {
    if (!generatedCTO) return;

    try {
        await navigator.clipboard.writeText(generatedCTO);
        showToast('Copied to clipboard!');
    } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = generatedCTO;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Copied to clipboard!');
    }
}

/**
 * Download as .cto file
 */
function handleDownload() {
    if (!generatedCTO) return;

    // Extract namespace for filename
    const namespaceMatch = generatedCTO.match(/namespace\s+([^\s@]+)/);
    const namespace = namespaceMatch ? namespaceMatch[1].replace(/\./g, '_') : 'model';
    const filename = `${namespace}.cto`;

    const blob = new Blob([generatedCTO], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast(`Downloaded ${filename}`);
}

/**
 * Update status indicator
 */
function setStatus(type, text) {
    const dot = statusIndicator.querySelector('.status-dot');
    const textEl = statusIndicator.querySelector('.status-text');

    dot.className = `status-dot ${type}`;
    textEl.textContent = text;
}

/**
 * Show/hide processing modal
 */
function showProcessingModal() {
    // Reset all steps
    for (let i = 1; i <= 4; i++) {
        const step = document.getElementById(`step-${i}`);
        step.className = 'step';
        step.querySelector('.step-icon').textContent = '⏳';
    }
    processingModal.classList.remove('hidden');
}

function hideProcessingModal() {
    processingModal.classList.add('hidden');
}

/**
 * Update processing step
 */
async function updateStep(stepNum, state) {
    const step = document.getElementById(`step-${stepNum}`);
    const icon = step.querySelector('.step-icon');

    step.className = `step ${state}`;

    if (state === 'active') {
        icon.textContent = '🔄';
    } else if (state === 'done') {
        icon.textContent = '✅';
    }
}

/**
 * Show toast notification
 */
function showToast(message, isError = false) {
    const icon = toast.querySelector('.toast-icon');
    const text = toast.querySelector('.toast-message');

    toast.className = `toast ${isError ? 'error' : ''}`;
    icon.textContent = isError ? '❌' : '✓';
    text.textContent = message;

    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

/**
 * Disable/enable buttons during processing
 */
function disableButtons(disabled) {
    generateBtn.disabled = disabled;
}

/**
 * Utility: delay
 */
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
