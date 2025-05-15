/**
 * Achievement notification system for FinShare
 * Handles notifications for earned achievements
 */

// Store for recently earned achievements
let recentlyEarnedAchievements = [];

/**
 * Shows a toast notification for a newly earned achievement
 * @param {Object} achievement - Achievement object with title, description, icon
 */
function showAchievementToast(achievement) {
  const toastContainer = document.getElementById('toast-container');
  
  // Create toast container if it doesn't exist
  if (!toastContainer) {
    const newContainer = document.createElement('div');
    newContainer.id = 'toast-container';
    document.body.appendChild(newContainer);
    
    // Add toast styles if not already added
    if (!document.getElementById('toast-styles')) {
      const style = document.createElement('style');
      style.id = 'toast-styles';
      style.textContent = `
        #toast-container {
          position: fixed;
          bottom: 20px;
          right: 20px;
          z-index: 9999;
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 10px;
        }
        .achievement-toast {
          background-color: var(--white);
          border-radius: 15px;
          padding: 15px 20px;
          box-shadow: var(--shadow-lg);
          display: flex;
          align-items: center;
          gap: 15px;
          max-width: 380px;
          transform: translateX(400px);
          opacity: 0;
          transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275),
                      opacity 0.5s ease;
          border-left: 4px solid var(--success);
        }
        .achievement-toast.show {
          transform: translateX(0);
          opacity: 1;
        }
        .achievement-toast-icon {
          width: 50px;
          height: 50px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background-color: rgba(46, 204, 113, 0.1);
          color: var(--success);
          font-size: 20px;
        }
        .achievement-toast-content {
          flex-grow: 1;
          padding-right: 10px;
        }
        .achievement-toast-title {
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 5px;
          display: flex;
          align-items: center;
          gap: 5px;
        }
        .achievement-toast-title span {
          display: inline-block;
          padding: 2px 5px;
          border-radius: 4px;
          background: linear-gradient(90deg, var(--primary) 0%, var(--success) 100%);
          color: white;
          font-size: 11px;
        }
        .achievement-toast-description {
          color: var(--text-secondary);
          font-size: 14px;
        }
        .achievement-toast-close {
          color: var(--text-secondary);
          background: none;
          border: none;
          cursor: pointer;
          font-size: 16px;
          padding: 0;
          margin-left: 10px;
          opacity: 0.6;
        }
        .achievement-toast-close:hover {
          opacity: 1;
        }
        @keyframes confetti {
          0% { transform: translateY(0) rotate(0); opacity: 1; }
          100% { transform: translateY(-100px) rotate(720deg); opacity: 0; }
        }
      `;
      document.head.appendChild(style);
    }
  }
  
  // Create the toast element
  const toast = document.createElement('div');
  toast.className = 'achievement-toast';
  toast.innerHTML = `
    <div class="achievement-toast-icon">
      <i class="${achievement.icon || 'fa-solid fa-trophy'}"></i>
    </div>
    <div class="achievement-toast-content">
      <div class="achievement-toast-title">
        Achievement Unlocked! <span>+${achievement.points || 10} pts</span>
      </div>
      <div class="achievement-toast-description">
        ${achievement.title}: ${achievement.description}
      </div>
    </div>
    <button class="achievement-toast-close">&times;</button>
  `;
  
  // Add to container
  document.getElementById('toast-container').appendChild(toast);
  
  // Show with animation
  setTimeout(() => toast.classList.add('show'), 50);
  
  // Set up remove handlers
  const closeBtn = toast.querySelector('.achievement-toast-close');
  closeBtn.addEventListener('click', () => removeToast(toast));
  
  // Auto-remove after 7 seconds
  setTimeout(() => removeToast(toast), 7000);
}

/**
 * Remove toast with animation
 * @param {Element} toast - Toast element to remove
 */
function removeToast(toast) {
  toast.style.opacity = '0';
  toast.style.transform = 'translateX(400px)';
  
  // Remove from DOM after animation
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 500);
}

/**
 * Show achievement modal with full details
 * @param {Object} achievement - Achievement data
 */
function showAchievementModal(achievement) {
  // Create modal container if it doesn't exist
  let modalContainer = document.getElementById('achievement-modal-container');
  if (!modalContainer) {
    modalContainer = document.createElement('div');
    modalContainer.id = 'achievement-modal-container';
    document.body.appendChild(modalContainer);
  }
  
  // Create modal HTML
  const modal = document.createElement('div');
  modal.className = 'achievement-modal';
  
  // Add appropriate emoji based on achievement title
  let achievementEmoji = '🏆'; // Default trophy
  
  if (achievement.title.includes('First Step')) {
    achievementEmoji = '👣';
  } else if (achievement.title.includes('Saving Star')) {
    achievementEmoji = '⭐';
  } else if (achievement.title.includes('Streak Keeper')) {
    achievementEmoji = '🔥';
  } else if (achievement.title.includes('Social Circle')) {
    achievementEmoji = '👥';
  } else if (achievement.title.includes('Income Champion')) {
    achievementEmoji = '💰';
  }
  
  modal.innerHTML = `
    <div class="achievement-modal-content">
      <div class="achievement-modal-header">
        <div class="confetti-container">
          ${Array(20).fill().map(() => '<div class="confetti"></div>').join('')}
        </div>
        <h2>Achievement Unlocked!</h2>
      </div>
      <div class="achievement-modal-body">
        <div class="achievement-modal-emoji-title">
          ${achievementEmoji} ${achievement.title}
        </div>
        <div class="achievement-modal-description">${achievement.description}</div>
        <div class="achievement-modal-points">+${achievement.points || 10} points</div>
      </div>
      <div class="achievement-modal-footer">
        <button class="achievement-modal-close">Close</button>
        <button class="achievement-modal-share">Share</button>
      </div>
    </div>
  `;
  
  // Add styles
  if (!document.getElementById('achievement-modal-styles')) {
    const style = document.createElement('style');
    style.id = 'achievement-modal-styles';
    style.textContent = `
      #achievement-modal-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease, visibility 0.3s ease;
      }
      
      #achievement-modal-container.show {
        opacity: 1;
        visibility: visible;
      }
      
      .achievement-modal {
        background-color: white;
        border-radius: 15px;
        width: 100%;
        max-width: 450px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        transform: scale(0.8);
        opacity: 0;
        transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275), 
                    opacity 0.5s ease;
        overflow: hidden;
      }
      
      #achievement-modal-container.show .achievement-modal {
        transform: scale(1);
        opacity: 1;
      }

      .achievement-modal-content {
        position: relative;
        border-radius: 15px;
        overflow: hidden;
      }
      
      .achievement-modal-header {
        background: linear-gradient(135deg, #2563eb 0%, #2ecc71 100%);
        padding: 30px 20px;
        color: white;
        text-align: center;
        position: relative;
        overflow: hidden;
      }
      
      .achievement-modal-header h2 {
        margin: 0;
        font-size: 22px;
        font-weight: 600;
        position: relative;
        z-index: 2;
      }
      
      .achievement-modal-body {
        padding: 20px;
        text-align: center;
        background-color: white;
      }
      
      .achievement-modal-emoji-title {
        font-size: 20px;
        font-weight: 600;
        margin: 15px 0;
        color: #1e293b;
      }
      
      .achievement-modal-description {
        font-size: 16px;
        color: var(--text-secondary);
        margin-bottom: 20px;
      }
      
      .achievement-modal-points {
        font-size: 18px;
        font-weight: 600;
        color: var(--success);
      }
      
      .achievement-modal-footer {
        padding: 20px 30px;
        display: flex;
        justify-content: center;
        gap: 15px;
        border-top: 1px solid #eee;
      }
      
      .achievement-modal-close, .achievement-modal-share {
        padding: 10px 25px;
        border-radius: 30px;
        border: none;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
      }
      
      .achievement-modal-close {
        background-color: #f1f5f9;
        color: var(--text-primary);
      }
      
      .achievement-modal-share {
        background-color: var(--success);
        color: white;
      }
      
      .achievement-modal-close:hover, .achievement-modal-share:hover {
        transform: translateY(-2px);
      }
      
      /* Confetti animation */
      .confetti-container {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        z-index: 0;
        pointer-events: none;
      }
      
      .confetti {
        position: absolute;
        width: 10px;
        height: 10px;
        background-color: #fff;
        opacity: 0.8;
        animation: confetti 2s ease-out forwards;
      }
    `;
    document.head.appendChild(style);
  }
  
  // Add to container
  modalContainer.innerHTML = '';
  modalContainer.appendChild(modal);
  
  // Set random positions and colors for confetti
  const confetti = modal.querySelectorAll('.confetti');
  const colors = ['#ff0', '#f0f', '#0ff', '#0f0', '#00f', '#f00'];
  
  confetti.forEach(c => {
    // Random position
    c.style.left = `${Math.random() * 100}%`;
    c.style.top = `${Math.random() * 100}%`;
    
    // Random color
    c.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    
    // Random size
    const size = 5 + Math.random() * 10;
    c.style.width = `${size}px`;
    c.style.height = `${size}px`;
    
    // Random rotation
    c.style.transform = `rotate(${Math.random() * 360}deg)`;
    
    // Random animation duration
    c.style.animationDuration = `${1 + Math.random() * 2}s`;
    
    // Random animation delay
    c.style.animationDelay = `${Math.random() * 0.5}s`;
  });
  
  // Show modal with animation
  setTimeout(() => modalContainer.classList.add('show'), 50);
  
  // Set up close button
  const closeBtn = modal.querySelector('.achievement-modal-close');
  closeBtn.addEventListener('click', () => closeAchievementModal());
  
  // Close when clicking outside
  modalContainer.addEventListener('click', event => {
    if (event.target === modalContainer) {
      closeAchievementModal();
    }
  });
  
  // Set up share button
  const shareBtn = modal.querySelector('.achievement-modal-share');
  shareBtn.addEventListener('click', () => {
    // In Phase 3, we'll implement actual sharing
    alert('Achievement sharing will be available in the next update!');
  });
}

/**
 * Close achievement modal with animation
 */
function closeAchievementModal() {
  const container = document.getElementById('achievement-modal-container');
  if (container) {
    container.classList.remove('show');
    setTimeout(() => {
      container.style.visibility = 'hidden';
    }, 300);
  }
}

/**
 * Check for newly earned achievements
 * @param {Array} achievements - Array of achievement objects
 */
function checkForNewAchievements(achievements) {
  // Get cached achievements from localStorage
  const cachedAchievements = JSON.parse(localStorage.getItem('cachedAchievements') || '[]');
  
  // Find newly earned achievements
  const newAchievements = achievements.filter(achievement => {
    return !cachedAchievements.some(cached => cached.id === achievement.id);
  });
  
  // Update cache with all current achievements
  localStorage.setItem('cachedAchievements', JSON.stringify(achievements));
  
  // Show notifications for new achievements
  if (newAchievements.length > 0) {
    newAchievements.forEach((achievement, index) => {
      // Stagger notifications
      setTimeout(() => {
        showAchievementToast(achievement);
      }, index * 1000);
      
      // Show modal for the first achievement only
      if (index === 0) {
        setTimeout(() => {
          showAchievementModal(achievement);
        }, 500);
      }
    });
  }
}

/**
 * Initialize achievement notification system
 */
function initAchievementSystem() {
  console.log('Achievement notification system initialized');
  
  // Check for new achievements when the page loads
  fetchUserAchievements();
  
  // Set up periodic checks
  setInterval(fetchUserAchievements, 60000); // Check every minute
}

/**
 * Fetch user achievements from the API
 */
function fetchUserAchievements() {
  fetch('/api/achievements')
    .then(response => response.json())
    .then(data => {
      if (data.earned && Array.isArray(data.earned)) {
        checkForNewAchievements(data.earned);
      }
    })
    .catch(error => console.error('Error fetching achievements:', error));
}

// Initialize the achievement system when the DOM is loaded
document.addEventListener('DOMContentLoaded', initAchievementSystem);

// Export functions for use in other scripts
window.achievementSystem = {
  showAchievementToast,
  showAchievementModal,
  fetchUserAchievements
};
