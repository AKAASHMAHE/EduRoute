/**
 * Main JavaScript File for Train Booking Date Reminder System
 */

document.addEventListener("DOMContentLoaded", function () {
    // 1. Initialize Quick Booking Date Calculator on Landing Page
    const quickDateInput = document.getElementById("quick_journey_date");
    const quickResultDiv = document.getElementById("quick_calc_result");
    const quickCalcDate = document.getElementById("quick_calc_date");
    const quickCalcStatus = document.getElementById("quick_calc_status");

    if (quickDateInput) {
        quickDateInput.addEventListener("change", function () {
            const selectedDate = this.value;
            if (!selectedDate) return;

            fetchBookingDateCalculation(selectedDate, function (data) {
                if (data.success) {
                    quickCalcDate.textContent = data.expected_booking_date_formatted;
                    quickCalcStatus.textContent = data.status_text;
                    quickCalcStatus.className = `badge rounded-pill ${data.status_class} mt-2`;
                    quickResultDiv.classList.remove("d-none");
                }
            });
        });
    }

    // 2. Initialize Live Calculation Preview on Add/Edit Journey Forms
    const journeyDateInput = document.getElementById("journey_date");
    const liveCard = document.getElementById("live_calculation_card");
    const previewBookingDate = document.getElementById("preview_booking_date");
    const previewStatusText = document.getElementById("preview_status_text");

    if (journeyDateInput) {
        // Trigger calculation if date is already filled (e.g., edit mode or form redisplay)
        if (journeyDateInput.value) {
            updateLiveFormPreview(journeyDateInput.value);
        }

        journeyDateInput.addEventListener("change", function () {
            updateLiveFormPreview(this.value);
        });
    }

    function updateLiveFormPreview(dateStr) {
        if (!dateStr) {
            if (liveCard) liveCard.classList.add("d-none");
            return;
        }

        fetchBookingDateCalculation(dateStr, function (data) {
            if (data.success && liveCard) {
                previewBookingDate.textContent = data.expected_booking_date_formatted;
                previewStatusText.textContent = `${data.status_text} • Journey in ${data.days_until_journey} days`;
                liveCard.classList.remove("d-none");
            }
        });
    }

    // Helper function for AJAX fetch
    function fetchBookingDateCalculation(journeyDate, callback) {
        fetch("/api/v1/calculate-booking-date", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ journey_date: journeyDate }),
        })
            .then((response) => response.json())
            .then((data) => callback(data))
            .catch((err) => console.error("Error calculating booking date:", err));
    }

    // 3. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});
