/**
 * Stock Notes Feature - localStorage-based notes per ticker
 * Allows users to save personal notes for any stock
 */

const NOTES_STORAGE_KEY = 'stock_notes';

// ============================================
// NOTES MANAGEMENT
// ============================================

/**
 * Get all notes from localStorage
 */
function getAllNotes() {
    try {
        const notes = localStorage.getItem(NOTES_STORAGE_KEY);
        return notes ? JSON.parse(notes) : {};
    } catch (e) {
        console.error('[Stock Notes] Error reading notes:', e);
        return {};
    }
}

/**
 * Save all notes to localStorage
 */
function saveAllNotes(notes) {
    try {
        localStorage.setItem(NOTES_STORAGE_KEY, JSON.stringify(notes));
        console.log('[Stock Notes] Notes saved');
    } catch (e) {
        console.error('[Stock Notes] Error saving notes:', e);
    }
}

/**
 * Get note for a specific ticker
 */
function getNote(ticker) {
    const notes = getAllNotes();
    return notes[ticker] || '';
}

/**
 * Save note for a specific ticker
 */
function saveNote(ticker, noteText) {
    const notes = getAllNotes();
    if (noteText.trim()) {
        notes[ticker] = {
            text: noteText.trim(),
            updated: new Date().toISOString()
        };
    } else {
        delete notes[ticker];
    }
    saveAllNotes(notes);
    updateAllNoteIcons();
}

/**
 * Check if a ticker has a note
 */
function hasNote(ticker) {
    const notes = getAllNotes();
    return notes[ticker] && notes[ticker].text;
}

/**
 * Get list of all tickers with notes
 */
function getTickersWithNotes() {
    const notes = getAllNotes();
    return Object.keys(notes).filter(ticker => notes[ticker] && notes[ticker].text);
}

// ============================================
// UI COMPONENTS
// ============================================

/**
 * Create note icon HTML for stock cards
 */
function createNoteIconHTML(ticker) {
    const hasNoteClass = hasNote(ticker) ? 'has-note' : '';
    return `
        <span class="note-icon ${hasNoteClass}" 
              data-ticker="${ticker}"
              onclick="openNoteModal('${ticker}', event)"
              title="${hasNote(ticker) ? 'Edit note' : 'Add note'}">
            📝
        </span>
    `;
}

/**
 * Update all note icons on the page
 */
function updateAllNoteIcons() {
    const icons = document.querySelectorAll('.note-icon');
    icons.forEach(icon => {
        const ticker = icon.dataset.ticker;
        if (hasNote(ticker)) {
            icon.classList.add('has-note');
            icon.title = 'Edit note';
        } else {
            icon.classList.remove('has-note');
            icon.title = 'Add note';
        }
    });
}

/**
 * Open note modal for a ticker
 */
function openNoteModal(ticker, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log(`[Stock Notes] Opening modal for ${ticker}`);
    
    // Get existing note
    const notes = getAllNotes();
    const existingNote = notes[ticker] || {};
    const noteText = existingNote.text || '';
    const lastUpdated = existingNote.updated ? new Date(existingNote.updated).toLocaleString() : '';
    
    // Create modal if it doesn't exist
    let modal = document.getElementById('note-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'note-modal';
        modal.className = 'note-modal';
        document.body.appendChild(modal);
    }
    
    modal.innerHTML = `
        <div class="note-modal-content">
            <div class="note-modal-header">
                <h3>📝 Notes for ${ticker}</h3>
                <button class="note-modal-close" onclick="closeNoteModal()">&times;</button>
            </div>
            <div class="note-modal-body">
                <textarea id="note-textarea" placeholder="Enter your notes for ${ticker}...">${noteText}</textarea>
                ${lastUpdated ? `<div class="note-last-updated">Last updated: ${lastUpdated}</div>` : ''}
            </div>
            <div class="note-modal-footer">
                <button class="note-btn note-btn-delete" onclick="deleteNote('${ticker}')" ${!noteText ? 'disabled' : ''}>
                    🗑️ Delete
                </button>
                <button class="note-btn note-btn-cancel" onclick="closeNoteModal()">
                    Cancel
                </button>
                <button class="note-btn note-btn-save" onclick="saveNoteFromModal('${ticker}')">
                    💾 Save
                </button>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
    
    // Focus textarea
    setTimeout(() => {
        document.getElementById('note-textarea').focus();
    }, 100);
    
    // Close on escape key
    document.addEventListener('keydown', handleNoteModalKeydown);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeNoteModal();
        }
    });
}

/**
 * Close note modal
 */
function closeNoteModal() {
    const modal = document.getElementById('note-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    document.removeEventListener('keydown', handleNoteModalKeydown);
}

/**
 * Handle keydown in note modal
 */
function handleNoteModalKeydown(e) {
    if (e.key === 'Escape') {
        closeNoteModal();
    } else if (e.key === 'Enter' && e.ctrlKey) {
        // Ctrl+Enter to save
        const ticker = document.querySelector('#note-modal h3').textContent.replace('📝 Notes for ', '');
        saveNoteFromModal(ticker);
    }
}

/**
 * Save note from modal
 */
function saveNoteFromModal(ticker) {
    const textarea = document.getElementById('note-textarea');
    const noteText = textarea.value;
    saveNote(ticker, noteText);
    closeNoteModal();
    showNotification(`Note ${noteText ? 'saved' : 'removed'} for ${ticker}`, 'success');
}

/**
 * Delete note for ticker
 */
function deleteNote(ticker) {
    if (confirm(`Delete note for ${ticker}?`)) {
        saveNote(ticker, '');
        closeNoteModal();
        showNotification(`Note deleted for ${ticker}`, 'info');
    }
}

// ============================================
// NOTES PAGE/SECTION HELPERS
// ============================================

/**
 * Get all notes with their data for display
 */
function getAllNotesForDisplay() {
    const notes = getAllNotes();
    return Object.entries(notes)
        .filter(([_, data]) => data && data.text)
        .map(([ticker, data]) => ({
            ticker,
            text: data.text,
            updated: new Date(data.updated)
        }))
        .sort((a, b) => b.updated - a.updated);
}

/**
 * Export notes as JSON
 */
function exportNotes() {
    const notes = getAllNotes();
    const blob = new Blob([JSON.stringify(notes, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `stock-notes-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    console.log('[Stock Notes] Notes exported');
}

/**
 * Import notes from JSON
 */
function importNotes(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const imported = JSON.parse(e.target.result);
            const currentNotes = getAllNotes();
            // Merge imported notes (imported takes precedence)
            const merged = { ...currentNotes, ...imported };
            saveAllNotes(merged);
            updateAllNoteIcons();
            showNotification(`Imported ${Object.keys(imported).length} notes`, 'success');
        } catch (err) {
            console.error('[Stock Notes] Import error:', err);
            showNotification('Failed to import notes', 'error');
        }
    };
    reader.readAsText(file);
}

console.log('[Stock Notes] Module loaded');
