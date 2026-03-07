document.addEventListener("DOMContentLoaded", function () {

const sosButton = document.getElementById("sos-btn");

sosButton.addEventListener("click", function () {

if (!navigator.geolocation) {
alert("Location not supported");
return;
}

navigator.geolocation.getCurrentPosition(function(position){

const latitude = position.coords.latitude;
const longitude = position.coords.longitude;

const type = document.getElementById("emergency-type").value;

fetch("/sos",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({
type:type,
latitude:latitude,
longitude:longitude
})

})
.then(res=>res.json())
.then(data=>{

if(data.success){

alert("🚨 SOS Sent Successfully. Help is on the way.");

}else{

alert("⚠ Failed to send SOS");

}

})

.catch(err=>{
alert("⚠ Server error");
})

});

});

});