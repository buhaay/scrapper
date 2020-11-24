var varieties = document.getElementsByClassName("varieties");
var i;

for (i = 0; i < varieties.length; i++) {
    varieties[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var exams = this.firstElementChild
        exams.classList.toggle("exams");
        exams.removeEventListener("click");
        exams.style.display("block");
        console.log(exams)
        // exams.style.padding = "10px";
        // exams.style.paddingLeft = "20px";
    });
}



//function filterItems() {
//    var user_input = document.getElementById('exam_choice');
//    var filter = input.value.toUpperCase();
//    var
//}

