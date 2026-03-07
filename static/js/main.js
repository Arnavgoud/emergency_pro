function sendSOS() {

    const type = document.querySelector("select").value;

    if (!navigator.geolocation) {
        alert("Location not supported");
        return;
    }

    navigator.geolocation.getCurrentPosition(function(position){

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
        .then(response => response.json())
        .then(data => {

            if(data.success){
                alert("🚨 SOS Sent Successfully");
            }else{
                alert("❌ Failed to send SOS");
            }

        })
        .catch(err => {
            console.error(err);
            alert("Server error");
        });

    });
}
