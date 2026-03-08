function sendSOS() {
    const type = document.getElementById("emergency-type").value;
    const button = document.querySelector(".sos-btn");
    if (button) {
        button.disabled = true;
        button.textContent = "Sending...";
    }

    if (!navigator.geolocation) {
        alert("Location not supported");
        if (button) {
            button.disabled = false;
            button.textContent = "SOS";
        }
        return;
    }

    navigator.geolocation.getCurrentPosition(function (position) {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        fetch("/send_sos", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                type: type,
                lat: lat,
                lon: lon
            })
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    const team = data.assigned_to ? ` and routed to ${data.assigned_to}` : "";
                    alert(`SOS sent successfully${team}.`);
                } else {
                    alert(data.error || "Failed to send SOS");
                }
                if (button) {
                    button.disabled = false;
                    button.textContent = "SOS";
                }
            })
            .catch((err) => {
                console.error(err);
                alert("Server error");
                if (button) {
                    button.disabled = false;
                    button.textContent = "SOS";
                }
            });
    }, function () {
        alert("Unable to get your location. Please enable GPS and try again.");
        if (button) {
            button.disabled = false;
            button.textContent = "SOS";
        }
    }, {
        enableHighAccuracy: false,
        timeout: 6000,
        maximumAge: 30000
    });
}
