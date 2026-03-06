document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const sortSelect = document.getElementById("sort-by");

  // Utility: escape HTML to prevent XSS
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // Render star display (read-only) for a given rating
  function renderStars(rating, maxStars = 5) {
    let html = '<span class="stars-display">';
    for (let i = 1; i <= maxStars; i++) {
      if (rating >= i) {
        html += '<span class="star filled">&#9733;</span>';
      } else if (rating >= i - 0.5) {
        html += '<span class="star half">&#9733;</span>';
      } else {
        html += '<span class="star empty">&#9734;</span>';
      }
    }
    html += "</span>";
    return html;
  }

  // Render interactive star selector for review form
  function renderStarsInput(activityName) {
    let html = '<div class="stars-input" data-activity="' + escapeHtml(activityName) + '">';
    for (let i = 1; i <= 5; i++) {
      html += '<span class="star" data-value="' + i + '">&#9734;</span>';
    }
    html += "</div>";
    return html;
  }

  // Render a single review item
  function renderReviewItem(activityName, review) {
    const date = new Date(review.timestamp).toLocaleDateString();
    return `
      <div class="review-item">
        <div class="review-header">
          <span>${renderStars(review.rating)} <span class="review-meta">${escapeHtml(review.email)} &middot; ${date}</span></span>
          <button class="review-delete-btn" data-activity="${escapeHtml(activityName)}" data-email="${escapeHtml(review.email)}" title="Delete review">&#10005;</button>
        </div>
        <div class="review-comment">${escapeHtml(review.comment)}</div>
      </div>
    `;
  }

  // Render the review form for an activity
  function renderReviewForm(activityName) {
    return `
      <div class="review-form" data-activity="${escapeHtml(activityName)}">
        <h5>Write a Review</h5>
        <div class="form-group">
          <input type="email" class="review-email" placeholder="your-email@mergington.edu" required />
        </div>
        <div class="form-group">
          <label>Rating:</label>
          ${renderStarsInput(activityName)}
          <input type="hidden" class="review-rating" value="0" />
        </div>
        <div class="form-group">
          <textarea class="review-comment-input" placeholder="Write your review..." maxlength="500"></textarea>
          <div class="char-counter"><span class="char-count">0</span>/500</div>
        </div>
        <button type="submit" class="submit-review-btn">Submit Review</button>
      </div>
    `;
  }

  // Fetch reviews for a specific activity and render them
  async function loadReviewsSection(activityName, container) {
    try {
      const response = await fetch(`/activities/${encodeURIComponent(activityName)}/reviews`);
      const data = await response.json();

      let reviewsHtml = "";
      if (data.reviews.length > 0) {
        data.reviews.forEach((review) => {
          reviewsHtml += renderReviewItem(activityName, review);
        });
      } else {
        reviewsHtml = '<p class="no-reviews">No reviews yet. Be the first!</p>';
      }

      container.innerHTML = reviewsHtml + renderReviewForm(activityName);
      setupReviewFormEvents(container, activityName);
    } catch (error) {
      container.innerHTML = '<p class="no-reviews">Failed to load reviews.</p>';
      console.error("Error loading reviews:", error);
    }
  }

  // Setup events for the review form inside a container
  function setupReviewFormEvents(container, activityName) {
    // Star input click
    const starsInput = container.querySelector(".stars-input");
    const ratingInput = container.querySelector(".review-rating");
    if (starsInput) {
      starsInput.addEventListener("click", (e) => {
        const star = e.target.closest(".star");
        if (!star) return;
        const value = parseInt(star.dataset.value);
        ratingInput.value = value;
        starsInput.querySelectorAll(".star").forEach((s, idx) => {
          if (idx < value) {
            s.innerHTML = "&#9733;";
            s.classList.add("selected");
          } else {
            s.innerHTML = "&#9734;";
            s.classList.remove("selected");
          }
        });
      });

      // Hover effect
      starsInput.addEventListener("mouseover", (e) => {
        const star = e.target.closest(".star");
        if (!star) return;
        const value = parseInt(star.dataset.value);
        starsInput.querySelectorAll(".star").forEach((s, idx) => {
          s.innerHTML = idx < value ? "&#9733;" : "&#9734;";
        });
      });
      starsInput.addEventListener("mouseleave", () => {
        const selected = parseInt(ratingInput.value);
        starsInput.querySelectorAll(".star").forEach((s, idx) => {
          if (idx < selected) {
            s.innerHTML = "&#9733;";
          } else {
            s.innerHTML = "&#9734;";
          }
        });
      });
    }

    // Character counter
    const textarea = container.querySelector(".review-comment-input");
    const charCount = container.querySelector(".char-count");
    const charCounter = container.querySelector(".char-counter");
    if (textarea && charCount) {
      textarea.addEventListener("input", () => {
        const len = textarea.value.length;
        charCount.textContent = len;
        if (len > 450) {
          charCounter.classList.add("warning");
        } else {
          charCounter.classList.remove("warning");
        }
      });
    }

    // Submit button
    const submitBtn = container.querySelector(".submit-review-btn");
    if (submitBtn) {
      submitBtn.addEventListener("click", async () => {
        const email = container.querySelector(".review-email").value.trim();
        const rating = parseInt(ratingInput.value);
        const comment = textarea.value.trim();

        if (!email) {
          showMessage("Please enter your email.", "error");
          return;
        }
        if (rating < 1 || rating > 5) {
          showMessage("Please select a rating (1-5 stars).", "error");
          return;
        }
        if (!comment) {
          showMessage("Please write a comment.", "error");
          return;
        }

        try {
          const response = await fetch(
            `/activities/${encodeURIComponent(activityName)}/reviews`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ email, rating, comment }),
            }
          );
          const result = await response.json();
          if (response.ok) {
            showMessage(result.message, "success");
            // Reload reviews section
            const content = container;
            await loadReviewsSection(activityName, content);
            // Refresh activity cards to update ratings
            activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
            fetchActivities();
          } else {
            showMessage(result.detail || "An error occurred", "error");
          }
        } catch (error) {
          showMessage("Failed to submit review. Please try again.", "error");
          console.error("Error submitting review:", error);
        }
      });
    }
  }

  // Show a message to the user
  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const sortBy = sortSelect ? sortSelect.value : "";
      let url = "/activities";
      if (sortBy) {
        url += `?sort_by=${encodeURIComponent(sortBy)}`;
      }
      const response = await fetch(url);
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Rating badge
        let ratingBadge = "";
        if (details.average_rating !== null) {
          ratingBadge = `
            <div class="rating-badge">
              ${renderStars(details.average_rating)}
              <span>${details.average_rating} (${details.review_count} review${details.review_count !== 1 ? "s" : ""})</span>
            </div>
          `;
        } else {
          ratingBadge = `<div class="rating-badge"><span class="review-meta">No reviews yet</span></div>`;
        }

        const participantsList = details.participants.length > 0
          ? `<ul class="participants-list">${details.participants.map(p => `<li><span class="participant-email">${escapeHtml(p)}</span><button class="delete-btn" data-activity="${escapeHtml(name)}" data-email="${escapeHtml(p)}" title="Remove participant">&#10005;</button></li>`).join('')}</ul>`
          : '<p class="no-participants">No participants yet</p>';

        activityCard.innerHTML = `
          <h4>${escapeHtml(name)}</h4>
          ${ratingBadge}
          <p>${escapeHtml(details.description)}</p>
          <p><strong>Schedule:</strong> ${escapeHtml(details.schedule)}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <strong>Participants:</strong>
            ${participantsList}
          </div>
          <div class="review-section">
            <button class="review-section-toggle">&#9662; Reviews (${details.review_count})</button>
            <div class="review-section-content"></div>
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Setup toggle for reviews section
        const toggle = activityCard.querySelector(".review-section-toggle");
        const content = activityCard.querySelector(".review-section-content");
        let loaded = false;
        toggle.addEventListener("click", async () => {
          const isOpen = content.classList.contains("open");
          if (isOpen) {
            content.classList.remove("open");
            toggle.innerHTML = `&#9662; Reviews (${details.review_count})`;
          } else {
            content.classList.add("open");
            toggle.innerHTML = `&#9652; Reviews (${details.review_count})`;
            if (!loaded) {
              content.innerHTML = '<p class="no-reviews">Loading reviews...</p>';
              await loadReviewsSection(name, content);
              loaded = true;
            }
          }
        });

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        signupForm.reset();
        activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Handle unregister and review delete button clicks (event delegation)
  activitiesList.addEventListener("click", async (event) => {
    // Unregister participant
    if (event.target.classList.contains("delete-btn")) {
      const button = event.target;
      const activity = button.dataset.activity;
      const email = button.dataset.email;

      if (!confirm(`Remove ${email} from ${activity}?`)) {
        return;
      }

      try {
        const response = await fetch(
          `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
          { method: "DELETE" }
        );

        const result = await response.json();

        if (response.ok) {
          showMessage(result.message, "success");
          activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
          fetchActivities();
        } else {
          showMessage(result.detail || "An error occurred", "error");
        }
      } catch (error) {
        showMessage("Failed to unregister. Please try again.", "error");
        console.error("Error unregistering:", error);
      }
    }

    // Delete review
    if (event.target.classList.contains("review-delete-btn")) {
      const button = event.target;
      const activity = button.dataset.activity;
      const email = button.dataset.email;

      if (!confirm(`Delete review by ${email} from ${activity}?`)) {
        return;
      }

      try {
        const response = await fetch(
          `/activities/${encodeURIComponent(activity)}/reviews?email=${encodeURIComponent(email)}`,
          { method: "DELETE" }
        );

        const result = await response.json();

        if (response.ok) {
          showMessage(result.message, "success");
          activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
          fetchActivities();
        } else {
          showMessage(result.detail || "An error occurred", "error");
        }
      } catch (error) {
        showMessage("Failed to delete review. Please try again.", "error");
        console.error("Error deleting review:", error);
      }
    }
  });

  // Sort control
  if (sortSelect) {
    sortSelect.addEventListener("change", () => {
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
      fetchActivities();
    });
  }

  // Initialize app
  fetchActivities();
});
