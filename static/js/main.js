// Theme Toggle
const themeToggle = document.getElementById("theme-toggle");
const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");

// Check for saved theme preference or use system preference
const currentTheme =
  localStorage.getItem("theme") ||
  (prefersDarkScheme.matches ? "dark" : "light");

// Apply theme on load
document.documentElement.setAttribute("data-theme", currentTheme);
updateThemeIcon(currentTheme);

// Theme toggle click handler
themeToggle.addEventListener("click", () => {
  const newTheme =
    document.documentElement.getAttribute("data-theme") === "dark"
      ? "light"
      : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("theme", newTheme);
  updateThemeIcon(newTheme);
});

function updateThemeIcon(theme) {
  const icon = themeToggle.querySelector("i");
  icon.className = theme === "dark" ? "fas fa-sun" : "fas fa-moon";
}

// Alert Dismissal
document.querySelectorAll(".close-alert").forEach((button) => {
  button.addEventListener("click", () => {
    const alert = button.closest(".alert");
    alert.style.opacity = "0";
    setTimeout(() => alert.remove(), 300);
  });
});

// Profile Dropdown
const profileBtn = document.querySelector(".profile-btn");
const dropdownContent = document.querySelector(".dropdown-content");

if (profileBtn && dropdownContent) {
  profileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdownContent.classList.toggle("show");
  });

  // Close dropdown when clicking outside
  document.addEventListener("click", () => {
    dropdownContent.classList.remove("show");
  });
}

// Search Functionality
const searchInput = document.querySelector(".search-bar input");
const searchButton = document.querySelector(".search-bar button");

if (searchInput && searchButton) {
  let searchTimeout;

  searchInput.addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      performSearch(e.target.value);
    }, 300);
  });

  searchButton.addEventListener("click", () => {
    performSearch(searchInput.value);
  });
}

async function performSearch(query) {
  if (!query.trim()) return;

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    updateSearchResults(data);
  } catch (error) {
    console.error("Search error:", error);
  }
}

function updateSearchResults(results) {
  // Implementation depends on your search results UI
  console.log("Search results:", results);
}

// Infinite Scroll for Dashboard
const loadMoreBtn = document.getElementById("load-more");
let isLoading = false;
let currentPage = 1;

if (loadMoreBtn) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && !isLoading) {
        loadMoreContent();
      }
    });
  });

  observer.observe(loadMoreBtn);
}

async function loadMoreContent() {
  if (isLoading) return;
  isLoading = true;
  currentPage++;

  try {
    const response = await fetch(`/api/users?page=${currentPage}`);
    const data = await response.json();

    if (data.users && data.users.length > 0) {
      appendUsers(data.users);
    } else {
      loadMoreBtn.style.display = "none";
    }
  } catch (error) {
    console.error("Error loading more content:", error);
  } finally {
    isLoading = false;
  }
}

function appendUsers(users) {
  const grid = document.querySelector(".students-grid");
  users.forEach((user) => {
    const card = createUserCard(user);
    grid.appendChild(card);
  });
}

function createUserCard(user) {
  const card = document.createElement("div");
  card.className = "student-card fade-in";
  card.innerHTML = `
        <div class="student-header">
            <img src="https://ui-avatars.com/api/?name=${user.username}" alt="${
    user.username
  }" class="student-avatar">
            <div class="student-info">
                <h3>${user.username}</h3>
                <p class="student-major">${
                  user.major || "Major not specified"
                }</p>
            </div>
        </div>
        <div class="student-bio">
            <p>${user.bio || "No bio available"}</p>
        </div>
        <div class="student-actions">
            <button class="btn btn-primary connect-btn" data-user-id="${
              user.id
            }">
                <i class="fas fa-user-plus"></i> Connect
            </button>
            <a href="/chat/${user.username}" class="btn btn-secondary">
                <i class="fas fa-comment"></i> Message
            </a>
        </div>
    `;
  return card;
}

// Form Validation
document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", (e) => {
    const requiredFields = form.querySelectorAll("[required]");
    let isValid = true;

    requiredFields.forEach((field) => {
      if (!field.value.trim()) {
        isValid = false;
        field.classList.add("error");

        // Add error message if it doesn't exist
        let errorMsg = field.nextElementSibling;
        if (!errorMsg || !errorMsg.classList.contains("error-message")) {
          errorMsg = document.createElement("div");
          errorMsg.className = "error-message";
          field.parentNode.insertBefore(errorMsg, field.nextSibling);
        }
        errorMsg.textContent = "This field is required";
      } else {
        field.classList.remove("error");
        const errorMsg = field.nextElementSibling;
        if (errorMsg && errorMsg.classList.contains("error-message")) {
          errorMsg.remove();
        }
      }
    });

    if (!isValid) {
      e.preventDefault();
    }
  });
});

// Real-time Online Status
function updateOnlineStatus() {
  const statusElements = document.querySelectorAll(".user-status");
  statusElements.forEach((status) => {
    const userId = status.dataset.userId;
    if (userId) {
      fetch(`/api/user/${userId}/status`)
        .then((response) => response.json())
        .then((data) => {
          status.className = `user-status ${
            data.online ? "online" : "offline"
          }`;
          status.textContent = data.online ? "Online" : "Offline";
        })
        .catch((error) => console.error("Error fetching user status:", error));
    }
  });
}

// Update online status every 30 seconds
setInterval(updateOnlineStatus, 30000);

// Initialize tooltips
document.querySelectorAll("[title]").forEach((element) => {
  element.addEventListener("mouseenter", (e) => {
    const tooltip = document.createElement("div");
    tooltip.className = "tooltip";
    tooltip.textContent = e.target.title;
    document.body.appendChild(tooltip);

    const rect = e.target.getBoundingClientRect();
    tooltip.style.top = `${rect.bottom + window.scrollY + 5}px`;
    tooltip.style.left = `${
      rect.left + window.scrollX + (rect.width - tooltip.offsetWidth) / 2
    }px`;

    e.target.addEventListener("mouseleave", () => tooltip.remove(), {
      once: true,
    });
  });
});

document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on a policy page
  const isPolicyPage = window.location.pathname.match(
    /^\/(privacy|cookies|terms)$/
  );

  // Only remove loading spinners if we're not on a policy page
  if (!isPolicyPage) {
    const existingSpinners = document.querySelectorAll(".loading-container");
    existingSpinners.forEach((spinner) => spinner.remove());
  }

  // Ensure content is visible
  const mainContent = document.querySelector(".main-content");
  if (mainContent) {
    mainContent.style.display = "block";
    mainContent.style.visibility = "visible";
    mainContent.style.opacity = "1";
  }

  // Theme Toggle
  const themeToggle = document.getElementById("theme-toggle");
  const themeIcon = themeToggle.querySelector("i");

  themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    const isDarkMode = document.body.classList.contains("dark-mode");
    themeIcon.className = isDarkMode ? "fas fa-sun" : "fas fa-moon";
    localStorage.setItem("darkMode", isDarkMode);
  });

  // Initialize theme from localStorage
  if (localStorage.getItem("darkMode") === "true") {
    document.body.classList.add("dark-mode");
    themeIcon.className = "fas fa-sun";
  }

  // Notifications Dropdown
  const notificationsBtn = document.getElementById("notifications-btn");
  const notificationsDropdown = document.getElementById(
    "notifications-dropdown"
  );

  if (notificationsBtn && notificationsDropdown) {
    notificationsBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      notificationsDropdown.classList.toggle("active");
    });

    // Mark all as read
    const markAllReadBtn =
      notificationsDropdown.querySelector(".mark-all-read");
    if (markAllReadBtn) {
      markAllReadBtn.addEventListener("click", () => {
        const unreadItems = notificationsDropdown.querySelectorAll(
          ".notification-item.unread"
        );
        unreadItems.forEach((item) => item.classList.remove("unread"));
        const badge = notificationsBtn.querySelector(".notification-badge");
        if (badge) badge.style.display = "none";
      });
    }
  }

  // Profile Dropdown
  const profileBtn = document.getElementById("profile-btn");
  const profileDropdown = document.getElementById("profile-dropdown");

  if (profileBtn && profileDropdown) {
    profileBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      profileDropdown.classList.toggle("active");
    });
  }

  // Close dropdowns when clicking outside
  document.addEventListener("click", (e) => {
    if (
      notificationsDropdown &&
      !notificationsDropdown.contains(e.target) &&
      !notificationsBtn.contains(e.target)
    ) {
      notificationsDropdown.classList.remove("active");
    }
    if (
      profileDropdown &&
      !profileDropdown.contains(e.target) &&
      !profileBtn.contains(e.target)
    ) {
      profileDropdown.classList.remove("active");
    }
  });

  // Newsletter Form
  const newsletterForm = document.querySelector(".newsletter-form");
  if (newsletterForm) {
    newsletterForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const emailInput = newsletterForm.querySelector('input[type="email"]');
      const email = emailInput.value;

      try {
        const response = await fetch("/api/newsletter/subscribe", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email }),
        });

        const data = await response.json();

        if (data.success) {
          showAlert("Successfully subscribed to newsletter!", "success");
          emailInput.value = "";
        } else {
          showAlert(
            data.message || "Failed to subscribe. Please try again.",
            "danger"
          );
        }
      } catch (error) {
        showAlert("An error occurred. Please try again later.", "danger");
      }
    });
  }

  // Alert System
  function showAlert(message, type = "info") {
    const alert = document.createElement("div");
    alert.className = `alert alert-${type} fade-in`;
    alert.innerHTML = `
            ${message}
            <button class="close-alert" aria-label="Close alert">&times;</button>
        `;

    const mainContent = document.querySelector(".main-content");
    mainContent.insertBefore(alert, mainContent.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      alert.classList.add("fade-out");
      setTimeout(() => alert.remove(), 300);
    }, 5000);

    // Close button
    const closeBtn = alert.querySelector(".close-alert");
    closeBtn.addEventListener("click", () => {
      alert.classList.add("fade-out");
      setTimeout(() => alert.remove(), 300);
    });
  }

  // Close existing alerts
  document.querySelectorAll(".alert .close-alert").forEach((btn) => {
    btn.addEventListener("click", () => {
      const alert = btn.closest(".alert");
      alert.classList.add("fade-out");
      setTimeout(() => alert.remove(), 300);
    });
  });

  // Search functionality
  const searchInput = document.querySelector(".search-input");
  if (searchInput) {
    let searchTimeout;

    searchInput.addEventListener("input", (e) => {
      clearTimeout(searchTimeout);
      const query = e.target.value.trim();

      if (query.length >= 2) {
        searchTimeout = setTimeout(async () => {
          try {
            const response = await fetch(
              `/api/search?q=${encodeURIComponent(query)}`
            );
            const data = await response.json();

            // Handle search results
            // This will depend on your search implementation
            console.log("Search results:", data);
          } catch (error) {
            console.error("Search error:", error);
          }
        }, 300);
      }
    });
  }

  // Page Transition Handling
  document.querySelectorAll("a").forEach((link) => {
    // Skip policy pages completely
    if (
      link.pathname === "/privacy" ||
      link.pathname === "/cookies" ||
      link.pathname === "/terms"
    ) {
      return;
    }

    if (
      link.hostname === window.location.hostname &&
      !link.hasAttribute("data-no-transition")
    ) {
      link.addEventListener("click", function (e) {
        // Don't show spinner for links that open in new tabs
        if (e.ctrlKey || e.metaKey || e.shiftKey) return;

        // Don't show spinner for links with specific classes or attributes
        if (
          link.classList.contains("no-transition") ||
          link.hasAttribute("download") ||
          link.hasAttribute("target")
        )
          return;

        e.preventDefault();
        const href = this.href;

        // Show loading spinner
        const spinnerTemplate = document.getElementById(
          "loading-spinner-template"
        );
        if (spinnerTemplate) {
          const spinner = spinnerTemplate.content.cloneNode(true);
          document.body.appendChild(spinner);
        }

        // Navigate to the new page
        window.location.href = href;
      });
    }
  });

  // Handle form submissions
  document.querySelectorAll("form").forEach((form) => {
    // Skip forms on policy pages
    if (
      window.location.pathname === "/privacy" ||
      window.location.pathname === "/cookies" ||
      window.location.pathname === "/terms"
    ) {
      return;
    }

    if (!form.hasAttribute("data-no-transition")) {
      form.addEventListener("submit", function (e) {
        // Don't show spinner for forms that should submit normally
        if (
          form.classList.contains("no-transition") ||
          form.hasAttribute("data-no-transition")
        )
          return;

        // Show loading spinner
        const spinnerTemplate = document.getElementById(
          "loading-spinner-template"
        );
        if (spinnerTemplate) {
          const spinner = spinnerTemplate.content.cloneNode(true);
          document.body.appendChild(spinner);
        }
      });
    }
  });
});
