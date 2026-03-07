function sendSOS() {
    const type = document.querySelector("select").value;

    if (!navigator.geolocation) {
        alert("Location not supported");
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
            })
            .catch((err) => {
                console.error(err);
                alert("Server error");
            });
    }, function () {
        alert("Unable to get your location. Please enable GPS and try again.");
    }, {
        enableHighAccuracy: true,
        timeout: 10000
    });
}
