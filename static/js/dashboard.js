document.addEventListener('DOMContentLoaded', function() {

    const timeEl = document.getElementById('time');
    const dateEl = document.getElementById('date');
    const dashboardEl = document.getElementById('dashboard');
    const screensaverEl = document.getElementById('screensaver');
    const screensaverImg = screensaverEl.querySelector('img');
  
    // Update dashboard time every second
    function updateDashboardTime() {
      const now = new Date();
      if (timeEl) {
        timeEl.textContent = now.toLocaleTimeString('en-GB');
      }
      if (dateEl) {
        const dateOptions = { weekday: 'long', day: 'numeric', month: 'long' };
        let dateStr = now.toLocaleDateString('en-GB', dateOptions);
        dateEl.textContent = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
      }
    }
  
    // Poll server to check if dashboard should be shown or hidden
    let previousModeIsDashboard = false;
    function checkMode() {
      fetch("/mode")
        .then(response => response.json())
        .then(data => {
          const isDashboardMode = data.dashboard;
          const view = data.view || 'all';
          if (isDashboardMode) {
            dashboardEl.style.display = "block";
            screensaverEl.style.display = "none";
            try {
              // If a specific user view is requested, render their two pages
              if (view === 'plan1' || view === 'plan2') {
                const viewsJson = dashboardEl.getAttribute('data-user-views');
                const views = viewsJson ? JSON.parse(viewsJson) : {};
                const selected = views[view];
                if (selected) {
                  const content = document.getElementById('dashboardContent');
                  if (content) {
                    content.innerHTML = `
                      <div class="plan-container" style="width:100%">
                        <div class="plan-header">
                          <span class="plan-icon">${selected.icon || ''}</span>
                          <h2 class="plan-title">${selected.name || ''}</h2>
                        </div>
                        <div class="d-flex" style="height: calc(100vh - 12rem); gap: 0.5rem;">
                          <div class="image-frame" style="flex:1">
                            <img src="${selected.img_page1_url || selected.img_url}" class="plan-image" />
                          </div>
                          <div class="image-frame" style="flex:1">
                            ${selected.img_page2_url || selected.img_url2 ? `<img src="${selected.img_page2_url || selected.img_url2}" class="plan-image" />` : '<div style="color:#6c757d">No page 2</div>'}
                          </div>
                        </div>
                      </div>`;
                  }
                }
              }
            } catch (e) {
              console.error('Error rendering user view', e);
            }
          } else {
            dashboardEl.style.display = "none";
            screensaverEl.style.display = "block";
  
            // If we just switched FROM dashboard TO screensaver, get a new image
            if (previousModeIsDashboard) {
              fetch("/screensaver_image")
                .then(res => res.json())
                .then(result => {
                  if (result.image_url && screensaverImg) {
                    screensaverImg.src = result.image_url;
                  }
                })
                .catch(err => console.error("Error fetching new screensaver image:", err));
            }
          }
          previousModeIsDashboard = isDashboardMode;
        })
        .catch(err => console.error("Error checking mode:", err));
    }
  
    // Initial calls and intervals
    updateDashboardTime();
    setInterval(updateDashboardTime, 1000);
    
    checkMode();
    setInterval(checkMode, 1000);
  });