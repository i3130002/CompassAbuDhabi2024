
let recordButton;

let isRecording = false;

let mediaRecorder;
let chunks = [];

let audioDuration = 2

const isHttps = window.location.protocol === "https:";

// Construct the socket connection URL based on the protocol
const socketProtocol = isHttps ? "https://" : "http://";
const socket = io.connect(socketProtocol + document.domain + ':' + location.port);


document.addEventListener('DOMContentLoaded', function () {

recordButton = document.getElementById("voiceBtn")
recordButton.addEventListener('click', handleRecording);



});

function startCountdown(seconds) {
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log("Countdown ended");
        resolve();
      }, seconds * 1000);
    });
  }




function handleRecording(){

console.log("Handling")
if (isRecording){
stopRecording()
}else{
startRecording()
}

}



function startRecording() {
isRecording = true;
recordButton.classList.add("blinking-element")

navigator.mediaDevices.getUserMedia({ audio: true })
.then(function (stream) {
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = function (event) {
        chunks.push(event.data);
    };
    mediaRecorder.onstop = function() {
        // Handle the stop event
        sendRecording();
    };
    mediaRecorder.start();
})
.catch(function (err) {
    console.error('Error: ', err);
});
}


function stopRecording() {

    recordButton.classList.remove("blinking-element")

console.log("Recording stopped");
isRecording = false;
mediaRecorder.stop();
recordButton.disabled = false;
}



function sendRecording(){

blob = new Blob(chunks, { type: 'audio/mp3' });

chunks = [];


const formData = new FormData();

console.log(blob)

formData.append('file', blob)


fetch('/send_audio_full', {
    method: 'POST',
    body: formData
})
.then(response => {
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  return response.blob();
})
.then(blob => {
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play();

  document.getElementById("pro").classList.add("shaking")

  startCountdown(audioDuration).then(() => {
    document.getElementById("pro").classList.remove("shaking")
  })


})
.catch(error => {
    console.error('Error:', error);
});
}


socket.on('duration', function(duration) {
    console.log(duration)
    audioDuration = duration
  });

