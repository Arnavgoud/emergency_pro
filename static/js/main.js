document.addEventListener("DOMContentLoaded", () => {

const sosBtn = document.getElementById("sos-btn");

sosBtn.addEventListener("click", () => {

if (!navigator.geolocation) {
alert("Location not supported");
return;
}

navigator.geolocation.getCurrentPosition(async (position) => {

const lat = position.coords.latitude;
const lon = position.coords.longitude;
const type = document.getElementById("emergency-type").value;

try {

const res = await fetch("/sos", {
method: "POST",
headers: {
"Content-Type": "application/json"
},
body: JSON.stringify({
type: type,
latitude: lat,
longitude: lon
})
});

if (!res.ok) {
throw new Error("Server error");
}

const data = await res.json();

alert("🚨 SOS Sent Successfully");

} catch (err) {

console.error(err);
alert("❌ Failed to send SOS");

}

});

});

});
