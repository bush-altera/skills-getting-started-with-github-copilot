document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Helper function to show messages with auto-hide
  function showMessage(messageDiv, text, className) {
    messageDiv.textContent = text;
    messageDiv.className = className;
    messageDiv.classList.remove("hidden");
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <p><strong>Participants:</strong></p>
            ${details.participants.length > 0 
              ? `<div class="participants-list">${details.participants.map(participant => `<div class="participant-item"><span class="participant-email">${participant}</span><button class="delete-btn" data-activity="${name}" data-participant="${participant}">✖</button></div>`).join('')}</div>`
              : `<p class="no-participants">No participants yet</p>`
            }
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add delete button event listeners
        const deleteButtons = activityCard.querySelectorAll('.delete-btn');
        deleteButtons.forEach(btn => {
          btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const activity = btn.dataset.activity;
            const participant = btn.dataset.participant;
            
            if (confirm(`Are you sure you want to unregister ${participant} from ${activity}?`)) {
              try {
                const response = await fetch(
                  `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(participant)}`,
                  {
                    method: "DELETE",
                  }
                );
                
                const result = await response.json();
                
                if (response.ok) {
                  // Refresh the activities to show updated participant list
                  fetchActivities();
                  
                  // Show success message
                  showMessage(messageDiv, result.message, "success");
                } else {
                  showMessage(messageDiv, result.detail || "Failed to unregister participant", "error");
                }
              } catch (error) {
                showMessage(messageDiv, "Failed to unregister participant. Please try again.", "error");
                console.error("Error unregistering participant:", error);
              }
            }
          });
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
        signupForm.reset();
        
        // Refresh the activities to show updated participant list
        fetchActivities();
        
        showMessage(messageDiv, result.message, "success");
      } else {
        showMessage(messageDiv, result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage(messageDiv, "Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
