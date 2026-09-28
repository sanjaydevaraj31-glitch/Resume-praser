/**
 * Upload management module for Resume Parser Agent.
 * Handles drag-and-drop, file selection, validation (.pdf, .docx),
 * and preview states.
 */

export class UploadManager {
  constructor(options = {}) {
    this.dropzone = document.getElementById(options.dropzoneId || 'dropzone');
    this.fileInput = document.getElementById(options.fileInputId || 'resume-file-input');
    this.previewCard = document.getElementById(options.previewCardId || 'file-preview-card');
    this.fileNameEl = document.getElementById(options.fileNameId || 'file-name-display');
    this.fileMetaEl = document.getElementById(options.fileMetaId || 'file-meta-display');
    this.fileTypeIconEl = document.getElementById(options.fileTypeIconId || 'file-type-badge');
    this.removeBtn = document.getElementById(options.removeBtnId || 'btn-remove-file');

    this.onFileChange = options.onFileChange || (() => {});
    this.onError = options.onError || ((msg) => alert(msg));

    this.currentFile = null;
    this.allowedExtensions = ['.pdf', '.docx'];
    this.maxSizeBytes = 10 * 1024 * 1024; // 10MB limit

    this.init();
  }

  init() {
    if (!this.dropzone || !this.fileInput) return;

    // File input change
    this.fileInput.addEventListener('change', (e) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        this.handleFile(files[0]);
      }
    });

    // Drag & Drop events
    ['dragenter', 'dragover'].forEach((eventName) => {
      this.dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.dropzone.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach((eventName) => {
      this.dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.dropzone.classList.remove('drag-over');
      });
    });

    this.dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        this.handleFile(files[0]);
      }
    });

    // Remove file button
    if (this.removeBtn) {
      this.removeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.clearFile();
      });
    }
  }

  handleFile(file) {
    if (!file) return;

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!this.allowedExtensions.includes(ext)) {
      this.onError(`Unsupported file format "${file.name}". Please upload a PDF (.pdf) or Word document (.docx).`);
      this.clearFile();
      return;
    }

    if (file.size > this.maxSizeBytes) {
      this.onError(`File "${file.name}" exceeds the maximum allowed size of 10MB.`);
      this.clearFile();
      return;
    }

    this.currentFile = file;
    this.renderPreview(file, ext);
    this.onFileChange(this.currentFile);
  }

  renderPreview(file, ext) {
    if (!this.previewCard) return;

    const formattedSize = this.formatFileSize(file.size);
    const typeLabel = ext === '.pdf' ? 'PDF' : 'DOCX';

    if (this.fileNameEl) this.fileNameEl.textContent = file.name;
    if (this.fileMetaEl) this.fileMetaEl.textContent = `${typeLabel} Document • ${formattedSize}`;
    if (this.fileTypeIconEl) {
      this.fileTypeIconEl.textContent = typeLabel;
      this.fileTypeIconEl.style.background = ext === '.pdf' ? 'linear-gradient(135deg, #ef4444, #b91c1c)' : 'linear-gradient(135deg, #3b82f6, #1d4ed8)';
    }

    this.previewCard.classList.add('active');
  }

  clearFile() {
    this.currentFile = null;
    if (this.fileInput) this.fileInput.value = '';
    if (this.previewCard) this.previewCard.classList.remove('active');
    this.onFileChange(null);
  }

  formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }

  getFile() {
    return this.currentFile;
  }
}
