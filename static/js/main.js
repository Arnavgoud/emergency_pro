document.addEventListener("DOMContentLoaded", () => {

const sosBtn = document.getElementById("sos-btn");

sosBtn.addEventListener("click", () => {

if (!navigator.geolocation) {
alert("Location not supported");
return;
}

navigator.geolocation.getCurrentPosition((position) => {

const lat = position.coords.latitude;
const lon = position.coords.longitude;

const type = document.getElementById("emergency-type").value;

fetch("/sos", {
method: "POST",
headers: {
"Content-Type": "application/json"
},
body: JSON.stringify({
type: type,
latitude: lat,
longitude: lon
})
})
.then(res => res.json())
.then(data => {

alert("🚨 SOS Sent Successfully");

})
.catch(err => {

alert("⚠ Failed to send SOS");

});

});

});

});
