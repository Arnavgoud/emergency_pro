document.addEventListener("DOMContentLoaded", function () {

const sosButton = document.getElementById("sos-btn");

if (!sosButton) {
console.log("SOS button not found");
return;
}

sosButton.addEventListener("click", function (e) {

e.preventDefault();

if (!navigator.geolocation) {
alert("Geolocation is not supported by your browser");
return;
}

navigator.geolocation.getCurrentPosition(function (position) {

let latitude = position.coords.latitude;
let longitude = position.coords.longitude;

let type = document.getElementById("emergency-type").value;

fetch("/sos", {
method: "POST",
headers: {
"Content-Type": "application/json"
},
body: JSON.stringify({
type: type,
latitude: latitude,
longitude: longitude
})
})
.then(response => response.json())
.then(data => {

alert("🚨 SOS Sent Successfully! Help is on the way.");

})
.catch(error => {

console.log(error);
alert("⚠ Failed to send SOS");

});

});

});

});
