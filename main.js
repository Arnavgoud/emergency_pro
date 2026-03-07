document.addEventListener("DOMContentLoaded", function () {

const sosButton = document.getElementById("sos-btn");

if (sosButton) {

sosButton.addEventListener("click", function () {

if (!navigator.geolocation) {
alert("Geolocation is not supported by your browser");
return;
}

navigator.geolocation.getCurrentPosition(function (position) {

let latitude = position.coords.latitude;
let longitude = position.coords.longitude;

let typeSelect = document.getElementById("emergency-type");
let emergencyType = typeSelect ? typeSelect.value : "crime";

fetch("/sos", {
method: "POST",
headers: {
"Content-Type": "application/json"
},
body: JSON.stringify({
type: emergencyType,
latitude: latitude,
longitude: longitude
})
})

.then(response => response.json())
.then(data => {

alert("🚨 SOS Sent Successfully!");

})

.catch(error => {

alert("Something went wrong. Please try again.");

});

});

});

}

});