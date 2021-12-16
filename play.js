function openPresent() {
    document.getElementById("Present").remove();
    // img
    var img = document.createElement("img");
    img.src = "./Essaouira.JPG";
    img.id = "imgPresent";
    container = document.getElementById("presentContainer");
    container.className = "containerOpened";
    container.appendChild(img);
    // audio
    document.getElementById("audio").play();
}

function audioEnd() {
    // Has escoltat el canvi de to?????
    var textContainer = document.getElementById("textContainer");
    textContainer.className = "textOpen";
}
