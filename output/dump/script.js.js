var answers = document.querySelectorAll(".clsnqaaa-select");
var lastQnum = document.querySelectorAll("#nnlstm .clsnqaaa-select").length;

function toNext(ele) {
    if(ele.value=="1"){
        document.getElementsByClassName("bdyaln1")[0].classList.add("animate__animated");
        document.getElementsByClassName("bdyaln1")[0].classList.add("animate__fadeOut"); 
        setTimeout(function () { 
            document.getElementsByClassName("bdyaln1")[0].style.display = "none";
        }, 500);
    }
    var ancestor = ele.parentElement.parentElement;
    var next = ancestor.nextElementSibling;
    ancestor.classList.add("animate__animated");
    ancestor.classList.add("animate__fadeOut");
    setTimeout(function () {
        ancestor.style.display = "none";
    }, 490)
    setTimeout(function () {
        next.classList.add("animate__animated");
        next.classList.add("animate__fadeIn");
        next.style.display = "block"
    }, 490)
}


var states = [document.getElementById("clsnqaaa-prgsst1"), 
          document.getElementById("clsnqaaa-prgsst2"), 
          document.getElementById("clsnqaaa-prgsst3"), 
          document.getElementById("clsnqaaa-prgsst4")];

var dones = [document.getElementById("clsnqaaa-prgdnn2"), 
          document.getElementById("clsnqaaa-prgdnn3"), 
          document.getElementById("clsnqaaa-prgdnn4")];

var loadImg = document.getElementById("clsnqaaa-progress-loading");
var loadBgCol = document.getElementById("content-changeCol");

function drawloader(){
    setTimeout(function () {
        dones[0].style.display="block";
        dones[0].classList.add("animate__animated");
        dones[0].classList.add("animate__fadeInUp");
    },1500);

    setTimeout(function () {
        states[0].style.display="block";
        states[0].classList.add("animate__animated");
        states[0].classList.add("animate__fadeOut");
        dones[0].style.color = "#34ae21";
        loadImg.classList.add("animate__animated");
        loadImg.classList.add("animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #e3ffdf,#fff,#fff,#fff,#e3ffdf)";
    },2300);

    setTimeout(function () {
        states[0].style.display="none";
        states[1].style.display="block";
        states[1].classList.add("animate__animated");
        states[1].classList.add("animate__fadeIn");
        dones[0].classList.add("animate__animated");
        dones[0].classList.add("animate__fadeOut");
        loadImg.classList.remove("animate__animated");
        loadImg.classList.remove("animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #fff,#fff,#fff,#fff,#fff)";
    },3500);






    setTimeout(function () {
        dones[0].style.display="none";
        dones[1].style.display="block";
        dones[1].classList.add("animate__animated");
        dones[1].classList.add("animate__fadeInUp");
    },5500);

    setTimeout(function () {
        states[1].style.display="block";
        states[1].classList.add("animate__animated");
        states[1].classList.add("animate__fadeOut");
        dones[1].style.color = "#34ae21";
        loadImg.classList.add("animate__animated");
        loadImg.classList.add("animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #e3ffdf,#fff,#fff,#fff,#e3ffdf)";
    },6300);

    setTimeout(function () {
        states[1].style.display="none";
        states[2].style.display="block";
        states[2].classList.add("animate__animated");
        states[2].classList.add("animate__fadeIn");
        dones[1].classList.add("animate__animated");
        dones[1].classList.add("animate__fadeOut");
        loadImg.classList.remove("animate__animated");
        loadImg.classList.remove("animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #fff,#fff,#fff,#fff,#fff)";
    },7500);







    setTimeout(function () {
        dones[1].style.display="none";
        dones[2].style.display="block";
        dones[2].classList.add("animate__animated");
        dones[2].classList.add("animate__fadeInUp");
    },9500);

    setTimeout(function () {
        states[2].style.display="block";
        states[2].classList.add("animate__animated");
        states[2].classList.add("animate__fadeOut");
        dones[2].style.color = "#34ae21";
        loadImg.classList.add("animate__animated");
        loadImg.classList.add("animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #e3ffdf,#fff,#fff,#fff,#e3ffdf)";
    },10300);

    setTimeout(function () {
        states[2].style.display="none";
        states[3].style.display="block";
        states[3].classList.add("animate__animated");
        states[3].classList.add("animate__fadeIn");
        dones[2].classList.add("animate__animated");
        dones[2].classList.add("animate__fadeOut");
        loadImg.classList.remove("animate__animated");
        loadImg.classList.remove("animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #fff,#fff,#fff,#fff,#fff)";
    },11500);

    setTimeout(function () {
        document.getElementById("verif-content").classList.add("animate__animated");
        document.getElementById("verif-content").classList.add("animate__fadeOut");
    },13500);

    setTimeout(function () {
        document.getElementById("verif-content").style.display = "none";
        document.getElementById("pza1").style.display = "block";
        document.getElementById("pza1").classList.add("animate__animated");
        document.getElementById("pza1").classList.add("animate__fadeIn");
        /* document.getElementById("content-changeCol").style.backgroundImage = "url('../images/banner.jpg')"; */
    },14000);

    setTimeout(function () {
        document.getElementById("pza2").style.display = "block";
        document.getElementById("pza2").classList.add("animate__animated");
        document.getElementById("pza2").classList.add("animate__fadeIn");
        document.getElementById("nothing-id").style.display = "none";
        document.getElementById("comments").style.display = "block";
        document.getElementById("comments").classList.remove("animate__fadeOut");
        document.getElementById("comments").classList.add("animate__fadeIn");
        document.getElementById("fftrfooter").style.display = "block";
        document.getElementById("fftrfooter").classList.remove("animate__fadeOut");
        document.getElementById("fftrfooter").classList.add("animate__fadeIn");
    },15000);
}


for (var i = 0; i < answers.length; i++) {
    if (i < (answers.length-lastQnum)){
        answers[i].onclick = function () {
            toNext(this)
        }
    } else {
        answers[i].onclick = function () {
            toNext(this);
            document.getElementById("comments").classList.add("animate__animated");
            document.getElementById("comments").classList.add("animate__fadeOut");
            document.getElementById("fftrfooter").classList.add("animate__animated");
            document.getElementById("fftrfooter").classList.add("animate__fadeOut");
            setTimeout(function () {
                document.getElementById("comments").style.display = "none";
                document.getElementById("fftrfooter").style.display = "none";
                document.getElementById("content-changeCol").style.backgroundImage = "none";
                drawloader()
            }, 600)
        }
    }
}


document.getElementById("btn-claim").onclick = function () {
    var modsclaim = document.getElementById("modal-prize");
    modsclaim.classList.add("mdlabg");
    modsclaim.children[0].classList.add("mdlainn");
    modsclaim.classList.remove("hidden");
    var modsprize = document.getElementById("prrzbodesc").innerText;
    document.getElementById("modal-head-prod").innerText = modsprize;
    document.getElementById("modal-head-prod2").innerText = modsprize;
}



const qhed = document.querySelectorAll(".qhda") || [];
const ques = document.querySelectorAll(".cltxt") || [];
const qnum = document.querySelectorAll(".clsqnu") || [];

for(var qn = 0; qn < qnum.length; qn++){
    qhed[qn].innerText = "Enquête sur l'expérience client Vinci Autoroutes";
    qnum[qn].innerText = "Question "+(qn+1)+" sur "+qnum.length+":";
}

let qtexxtt = [
    "À quelle fréquence les publicités de Vinci Autoroutes retiennent-elles votre attention lors de vos activités quotidiennes ?",
    "Souvent, ils sont assez visibles.",
    "Parfois, quand ils correspondent à mes besoins.",
    "Rarement, je ne les remarque presque jamais.",
    "Jamais, ils se fondent dans le décor.",
    "Quand vous pensez à Vinci Autoroutes, lequel des mots suivants vous vient à l’esprit en premier ?",
    "Fiabilité",
    "Innovation",
    "Sécurité",
    "Commodité",
    "Avez-vous participé à des événements promotionnels Vinci Autoroutes avant cette enquête ?",
    "Oui, plus d'une fois.",
    "Oui, c'est ma première fois.",
    "Non, mais j'y ai réfléchi.",
    "Non, et cela ne m'intéresse pas.",
    "Si Vinci Autoroutes élargissait ses services, lequel des services suivants vous intéresserait le plus ?",
    "Des haltes plus fréquentes",
    "Fonctionnalités de sécurité routière améliorées",
    "Des initiatives éco-responsables",
    "Systèmes avancés de gestion du trafic",
    "Quelle est la probabilité que vous utilisiez le Car Emergency Kit de Vinci Autoroutes dans les 6 prochains mois ?",
    "Très probablement, cela semble indispensable.",
    "Assez probable, en fonction de mes voyages.",
    "C'est peu probable, j'en ai déjà un.",
    "Peu probable, je n’en vois pas la nécessité.",
    "Quelle fonctionnalité du Kit d’Urgence Voiture Vinci Autoroutes vous séduit le plus ?",
    "La sélection complète d'outils",
    "L’inclusion de guides de sécurité",
    "Son design compact et facile à ranger",
    "La qualité des produits inclus",
    "Comment votre expérience globale avec Vinci Autoroutes a-t-elle influencé votre vision de leurs cadeaux promotionnels ?",
    "Positivement, je fais davantage confiance à leurs produits.",
    "Un peu positivement, c'est intéressant.",
    "Aucun changement, je ressens la même chose.",
    "Négativement, je suis sceptique quant aux avantages.",
    "Une expérience positive avec le Car Emergency Kit vous inciterait-elle à faire vos achats plus fréquemment chez Vinci Autoroutes ?",
    "Certainement, cela renforce la confiance.",
    "Peut-être, si la qualité est bonne.",
    "Pas vraiment, mes habitudes d’achat ne changeraient pas.",
    "Non, cela n'influencerait pas du tout mes achats."
];

var dsq = 0;
var incq = 0;

while(dsq < qtexxtt.length){
    ques[dsq].innerText = qtexxtt[dsq];
    dsq++;
}







