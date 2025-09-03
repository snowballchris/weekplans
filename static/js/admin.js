document.addEventListener('DOMContentLoaded', function() {
    // --- Tab Handling ---
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
      button.addEventListener('shown.bs.tab', function(e) {
        const tabId = e.target.getAttribute('data-bs-target').substring(1);
        const url = new URL(window.location);
        url.searchParams.set('tab', tabId);
        // Use replaceState to avoid cluttering browser history
        window.history.replaceState({}, '', url);
      });
    });
    
    // --- Initialize Bootstrap Tooltips ---
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  
    // --- PDF Preview Handling ---
    const pdfFileInput = document.getElementById('pdf_file');
    if (pdfFileInput) {
      pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
      let currentPdf = null;
      let currentPage = 1;
      let totalPages = 1;
  
      pdfFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file && file.type === 'application/pdf') {
          const fileReader = new FileReader();
          fileReader.onload = function() {
            const typedarray = new Uint8Array(this.result);
            loadPdf(typedarray);
          };
          fileReader.readAsArrayBuffer(file);
        }
      });
  
      async function loadPdf(data) {
        try {
          currentPdf = await pdfjsLib.getDocument({ data: data }).promise;
          totalPages = currentPdf.numPages || 1;
          currentPage = 1;
          document.getElementById('pdfPreview').style.display = 'block';
          updateControls();
          renderPage(currentPage);
        } catch (error) {
          console.error('Error loading PDF:', error);
          document.getElementById('pdfPreview').style.display = 'none';
        }
      }
  
      async function renderPage(pageNum) {
        if (!currentPdf) return;
        
        const page = await currentPdf.getPage(pageNum);
        const viewport = page.getViewport({ scale: 1.5 });
        const canvas = document.getElementById('pdfCanvas');
        const context = canvas.getContext('2d');
        
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        await page.render({
          canvasContext: context,
          viewport: viewport
        }).promise;
        document.getElementById('pdfPageNum').textContent = String(pageNum);
        document.getElementById('pdfPageCount').textContent = String(totalPages);
        updateControls();
      }

      function updateControls() {
        const prevBtn = document.getElementById('pdfPrev');
        const nextBtn = document.getElementById('pdfNext');
        if (prevBtn) prevBtn.disabled = currentPage <= 1;
        if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
      }

      const prevBtn = document.getElementById('pdfPrev');
      const nextBtn = document.getElementById('pdfNext');
      if (prevBtn) {
        prevBtn.addEventListener('click', () => {
          if (currentPdf && currentPage > 1) {
            currentPage -= 1;
            renderPage(currentPage);
          }
        });
      }
      if (nextBtn) {
        nextBtn.addEventListener('click', () => {
          if (currentPdf && currentPage < totalPages) {
            currentPage += 1;
            renderPage(currentPage);
          }
        });
      }

      // Keyboard navigation when preview is visible
      document.addEventListener('keydown', (e) => {
        const preview = document.getElementById('pdfPreview');
        if (!preview || preview.style.display === 'none') return;
        if (e.key === 'ArrowLeft') {
          if (currentPdf && currentPage > 1) {
            currentPage -= 1;
            renderPage(currentPage);
          }
        } else if (e.key === 'ArrowRight') {
          if (currentPdf && currentPage < totalPages) {
            currentPage += 1;
            renderPage(currentPage);
          }
        }
      });
    }
  
    // --- Settings Tab: Duration Slider ---
    const durationSlider = document.getElementById('dashboard_duration');
    const durationDisplay = document.getElementById('durationDisplay');
    if (durationSlider && durationDisplay) {
      durationSlider.addEventListener('input', function() {
        durationDisplay.textContent = this.value;
      });
    }
  
    // --- Controls Tab: Brightness Slider ---
    const brightnessSlider = document.getElementById('brightness');
    const brightnessDisplay = document.getElementById('brightnessDisplay');
    if (brightnessSlider && brightnessDisplay) {
        brightnessSlider.addEventListener('input', function() {
            brightnessDisplay.textContent = this.value + '%';
        });
    }
  
    // --- Controls Tab: Refresh Status ---
    const refreshButton = document.getElementById('refreshStatus');
    if (refreshButton) {
      refreshButton.addEventListener('click', function() {
        const icon = this.querySelector('i');
        const originalIconClass = icon.className;
        icon.className = 'fas fa-sync-alt fa-spin'; // Show loading spinner
        this.disabled = true;
        
        // Construct URL safely
        const url = new URL(window.location);
        url.searchParams.set('refresh_status', 'true');
        
        fetch(url)
          .then(response => {
              if (!response.ok) { throw new Error('Network response was not ok'); }
              return response.json();
          })
          .then(data => {
              if(data.system_stats) {
                  // BUG FIX: Overwrite entire textContent to prevent appending units
                  document.getElementById('boot_time').textContent = data.system_stats.boot_time;
                  document.getElementById('cpu_load').textContent = parseFloat(data.system_stats.cpu_load).toFixed(1) + '%';
                  document.getElementById('cpu_temp').textContent = parseFloat(data.system_stats.cpu_temp).toFixed(1) + '°C';
                  document.getElementById('memory_usage').textContent = parseFloat(data.system_stats.memory_usage).toFixed(1) + '%';
                  document.getElementById('disk_free_pct').textContent = data.system_stats.disk_free_pct + '%';
              }
          })
          .catch(error => console.error('Error refreshing status:', error))
          .finally(() => {
            icon.className = originalIconClass; // Restore original icon
            this.disabled = false;
          });
      });
    }
  });
  
  function confirmRestart() {
    if (confirm("Are you sure you want to restart the entire system? This cannot be undone.")) {
      document.getElementById('restartForm').submit();
    }
  }