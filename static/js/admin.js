document.addEventListener('DOMContentLoaded', function() {
    // --- Slider displays (run first so they work even if PDF block fails) ---
    const durationSlider = document.getElementById('dashboard_duration');
    const durationDisplay = document.getElementById('durationDisplay');
    if (durationSlider && durationDisplay) {
      durationSlider.addEventListener('input', function() {
        durationDisplay.textContent = this.value;
      });
    }
    const brightnessSlider = document.getElementById('brightness');
    const brightnessDisplay = document.getElementById('brightnessDisplay');
    if (brightnessSlider && brightnessDisplay) {
      brightnessSlider.addEventListener('input', function() {
        brightnessDisplay.textContent = this.value + '%';
      });
    }

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

    // --- Jump to tab buttons ---
    const goToTabButtons = document.querySelectorAll('[data-go-to-tab]');
    goToTabButtons.forEach(button => {
      button.addEventListener('click', function() {
        const target = this.getAttribute('data-go-to-tab');
        const tabTrigger = document.querySelector(`[data-bs-target="#${target}"]`);
        if (tabTrigger) {
          const tab = new bootstrap.Tab(tabTrigger);
          tab.show();
          if (target === 'settings') {
            setTimeout(() => {
              const anchor = document.getElementById('mqtt-config');
              if (anchor) {
                anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }
            }, 150);
          }
        }
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
                  // Overwrite entire textContent to prevent appending units
                  document.getElementById('uptime').textContent = data.system_stats.uptime;
                  document.getElementById('start_time').textContent = data.system_stats.start_time;
                  document.getElementById('memory_usage').textContent = data.system_stats.memory_usage;
                  document.getElementById('memory_limit').textContent = data.system_stats.memory_limit;
                  document.getElementById('container_id').textContent = data.system_stats.container_id;
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