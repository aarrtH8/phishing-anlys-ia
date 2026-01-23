function datehax() {
    var mydate = new Date()
    mydate.setDate(mydate.getDate());
    var year = mydate.getYear()
    if (year < 1000)
        year += 1900
    var day = mydate.getDay()
    var month = mydate.getMonth()
    var daym = mydate.getDate()
    if (daym < 10)
        daym = "0" + daym
    var dayarray = Array("Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi");
     var montharray = new Array("Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre") ;
    
    //var dayarray = Array("dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi");
    //var montharray = new Array("janvier","février","mars","avril","mai","juin","juillet","aout","septembre","octobre","novembre","décembre");
    
    // var dayarray = new Array("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
    // var montharray = new Array("Januari","Februari","Maart","April","Mei","Juni","Juli","Augustus","September","Oktober","November","December")
    return "" + montharray[month] + " " + daym + ", " + year + "";
}


function datenhax() {
    var mydate = new Date()
    mydate.setDate(mydate.getDate());
    var year = mydate.getYear()
    if (year < 1000)
        year += 1900
    var month = mydate.getMonth()+1;
    var daym = mydate.getDate();
    if(month < 10){month = "0"+month+"";}
    console.log();
    return "" + daym + "/" + month + "/" + year + "";
    
}


function datenhay() {
    var mydate = new Date()
    mydate.setDate(mydate.getDate());
    var year = mydate.getYear()
    if (year < 1000)
        year += 1900
    return year + "";
    
}


function startTimer(duration, display) {
    var timer = duration,
        minutes, seconds;
    setInterval(function() {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display.innerHTML = "<span class='con-time-block'>" + minutes + "</span>:<span class='con-time-block'>" + seconds + "</span>";

        if (--timer < 0) {
            timer = duration;
        }
    }, 1000);
}

window.onload = function() {
    var fiveMinutes = 30 * 13, display = document.querySelector('#time');
    startTimer(fiveMinutes, display);
};
