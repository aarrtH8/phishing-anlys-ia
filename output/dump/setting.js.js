function datehax() {
    const mydate = new Date();
    mydate.setDate(mydate.getDate());
    let year = mydate.getFullYear(); // Use getFullYear instead of getYear
    let day = mydate.getDay();
    let month = mydate.getMonth();
    let daym = mydate.getDate();

    if (daym < 10) {
        daym = "0" + daym;
    }

    const dayarray = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
    const montharray = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];

    return `${montharray[month]} ${daym}, ${year}`;
}

function datenhax() {
    const mydate = new Date();
    mydate.setDate(mydate.getDate());
    let year = mydate.getFullYear(); // Use getFullYear instead of getYear
    let month = mydate.getMonth() + 1; // Months are zero-indexed
    let daym = mydate.getDate();

    if (month < 10) {
        month = "0" + month; // Add leading zero for months less than 10
    }

    return `${daym}/${month}/${year}`;
}

function datenhay() {
    const mydate = new Date();
    const year = mydate.getFullYear(); // Use getFullYear instead of getYear
    return year.toString();
}

const states = [
    document.getElementById("qassersaa-prgsst1"), 
    document.getElementById("qassersaa-prgsst2"), 
    document.getElementById("qassersaa-prgsst3"), 
    document.getElementById("qassersaa-prgsst4")
];

const dones = [
    document.getElementById("qassersaa-prgdnn2"), 
    document.getElementById("qassersaa-prgdnn3"), 
    document.getElementById("qassersaa-prgdnn4")
];

const loadImg = document.getElementById("qassersaa-progress-loading");
const loadBgCol = document.getElementById("content-changeCol");

// Function to render loader with animations and progress updates
function renderLoader() {
    setTimeout(function () {
        dones[0].style.display = "block";
        dones[0].classList.add("animate__animated", "animate__fadeInUp");
    }, 1500);

    setTimeout(function () {
        states[0].style.display = "block";
        states[0].classList.add("animate__animated", "animate__fadeOut");
        dones[0].style.color = "#34ae21";
        loadImg.classList.add("animate__animated", "animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #e3ffdf, #fff, #fff, #fff, #e3ffdf)";
    }, 2300);

    setTimeout(function () {
        states[0].style.display = "none";
        states[1].style.display = "block";
        states[1].classList.add("animate__animated", "animate__fadeIn");
        dones[0].classList.add("animate__animated", "animate__fadeOut");
        loadImg.classList.remove("animate__animated", "animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #fff, #fff, #fff, #fff, #fff)";
    }, 3500);

    setTimeout(function () {
        dones[0].style.display = "none";
        dones[1].style.display = "block";
        dones[1].classList.add("animate__animated", "animate__fadeInUp");
    }, 5500);

    setTimeout(function () {
        states[1].style.display = "block";
        states[1].classList.add("animate__animated", "animate__fadeOut");
        dones[1].style.color = "#34ae21";
        loadImg.classList.add("animate__animated", "animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #e3ffdf, #fff, #fff, #fff, #e3ffdf)";
    }, 6300);

    setTimeout(function () {
        states[1].style.display = "none";
        states[2].style.display = "block";
        states[2].classList.add("animate__animated", "animate__fadeIn");
        dones[1].classList.add("animate__animated", "animate__fadeOut");
        loadImg.classList.remove("animate__animated", "animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #fff, #fff, #fff, #fff, #fff)";
    }, 7500);

    setTimeout(function () {
        dones[1].style.display = "none";
        dones[2].style.display = "block";
        dones[2].classList.add("animate__animated", "animate__fadeInUp");
    }, 9500);

    setTimeout(function () {
        states[2].style.display = "block";
        states[2].classList.add("animate__animated", "animate__fadeOut");
        dones[2].style.color = "#34ae21";
        loadImg.classList.add("animate__animated", "animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #e3ffdf, #fff, #fff, #fff, #e3ffdf)";
    }, 10300);

    setTimeout(function () {
        states[2].style.display = "none";
        states[3].style.display = "block";
        states[3].classList.add("animate__animated", "animate__fadeIn");
        dones[2].classList.add("animate__animated", "animate__fadeOut");
        loadImg.classList.remove("animate__animated", "animate__bounceIn");
        loadBgCol.style.backgroundImage = "linear-gradient(to right, #fff, #fff, #fff, #fff, #fff)";
    }, 11500);

    setTimeout(function () {
        document.getElementById("verif-content").classList.add("animate__animated", "animate__fadeOut");
    }, 13500);

    setTimeout(function () {
        document.getElementById("verif-content").style.display = "none";
        document.getElementById("zprrs1").style.display = "block";
        document.getElementById("zprrs1").classList.add("animate__animated", "animate__fadeIn");
    }, 14000);

    setTimeout(function () {
        document.getElementById("zprrs2").style.display = "block";
        document.getElementById("zprrs2").classList.add("animate__animated", "animate__fadeIn");
        document.getElementById("nothing-id").style.display = "none";
        document.getElementById("comments").style.display = "block";
        document.getElementById("comments").classList.remove("animate__fadeOut");
        document.getElementById("comments").classList.add("animate__fadeIn");
        document.getElementById("ttrrfasfooter").style.display = "block";
        document.getElementById("ttrrfasfooter").classList.remove("animate__fadeOut");
        document.getElementById("ttrrfasfooter").classList.add("animate__fadeIn");
    }, 15000);
}




document.getElementById("animate_btn_0").onclick = function () {
    document.getElementsByClassName("surveyContent")[0].classList.remove("hdsnvnn_dvhddn");
    document.querySelector(".bawesdaln2").classList.add("hdsnvnn_dvhddn");
    document.querySelector(".bawesdaln1").classList.add("hdsnvnn_dvhddn");
}


document.getElementById("btn-clm-sub").onclick = function () {
    let modsclaim = document.getElementById("modal-prize");
    modsclaim.classList.add("mdlabg");
    modsclaim.children[0].classList.add("mdlainn");
    modsclaim.classList.remove("hdsnvnn_dvhddn");
    var modsprize = document.getElementById("zpdssbdddesc").innerText;
    document.getElementById("modal-head-prod").innerText = modsprize;
    document.getElementById("modal-head-prod2").innerText = modsprize;
}





// Ensure elements exist before manipulating them to avoid errors
const ttll = document.getElementsByClassName("wbttlle")[0];
const hd1 = document.getElementsByClassName("hwsdaa-ln1")[0];
const hd3 = document.getElementsByClassName("hwsdaa-ln3")[0];
const hd1ln = document.getElementsByClassName("hwsdaa-line")[0];
const bdyln = document.getElementsByClassName("bawesdaln1-inn2")[0];
const btnstrt = document.getElementById("animate_btn_0");
const ldng = document.getElementsByClassName("qassersaa-verif-content-title")[0];
const tyds = document.getElementsByClassName("bawesdaln3")[0];
const prd1 = document.getElementsByClassName("zpdssbddtitle")[0];
const prd2 = document.getElementsByClassName("zpdssbdddesc")[0];
const prd3 = document.getElementsByClassName("zpdssbddamount")[0];
const prd4 = document.getElementsByClassName("zpdssbddstock")[0];
const prd5 = document.getElementsByClassName("zpdssbddpfs")[0];
const clmbtn = document.getElementById("btn-clm-sub");

const cmfnt1 = document.getElementsByClassName("tmmnasname")[0];
const cmfnt2 = document.getElementsByClassName("tmmnastitle")[0];
const ftrd1 = document.getElementsByClassName("copyrightzz")[0];
const ftrd2 = document.getElementsByClassName("claimcop")[0];
const offrex = document.getElementsByClassName("cswccmcbottom-bar")[0];

const mdprz1 = document.getElementsByClassName("md-cgrts")[0];
const mdprz2 = document.getElementsByClassName("md-pstps")[0];
const mdprzbtn = document.getElementsByClassName("btngto")[0];

// Check if elements exist before trying to manipulate them
if (ttll) ttll.textContent = "Sephora - Récompenses du sondage";
if (hd1) hd1.innerHTML = "<h4>Plus de 4 000 000 € d'offres déjà distribuées !</h4>";
if (hd3) hd3.innerHTML = datehax();
if (hd1ln) hd1ln.innerHTML = "<hr/><span>Sondage sur</span><hr/>";/* marque */
if (bdyln) bdyln.innerHTML = "<p><b>Cher client de Sephora,</b><br/><br/>Nous souhaitons vous offrir une opportunité unique de recevoir un <b>Lancôme Beauty Box!</b> Pour le réclamer, il vous suffit de répondre à ce court sondage sur votre expérience avec Sephora.</p><br/><p><b><span>Attention !</span></b> Cette offre de sondage expire aujourd'hui, "+datehax()+".</b></p>";
if (btnstrt) btnstrt.textContent = "COMMENCER LE SONDAGE";
if (ldng) ldng.innerHTML = "<b>Veuillez patienter pendant que nous traitons vos réponses...</b>";
if (tyds) tyds.innerHTML = "<h2><b>Merci d'avoir complété le sondage !</b></h2><p>Grâce à vos précieuses réponses, vous pouvez maintenant choisir parmi les récompenses exclusives ci-dessous.</p><p>Veuillez noter que si vous quittez cette page sans réclamer votre récompense, nous devrons donner la chance à un autre visiteur de participer à notre programme de récompenses.</p> <div class='asdfdb animate__animated animate__slower animate__infinite animate__shakeY'><b><i class='fas fa-angle-double-down fa-2x'></i></b></i></div>";
if (prd1) prd1.textContent = "Lancôme Beauty Box"; 
if (prd2) prd2.innerHTML = "La Lancôme Holiday Beauty Box est un coffret de beauté luxueux et en édition limitée qui comprend une sélection des produits de soin de la peau et de maquillage les plus populaires de Lancôme, tous magnifiquement emballés dans une trousse de toilette premium. Conçu comme l'indulgence ultime pour les fêtes ou un cadeau, cette collection exclusive offre un mélange d'articles en taille réelle et d'éléments pratiques pour voyager, permettant aux passionnés de beauté de découvrir les bestsellers de Lancôme à une valeur incroyable."; 
if (prd3) prd3.innerHTML = "<div class='zpdssbddzero1'>&nbsp;Prix : <del>150,50 €</del></div><div class='zpdssbddzero2 animate__animated animate__heartBeat animate__slower animate__infinite'>0,00 €</div>";




if (typeof states !== 'undefined') {
    if (states[0]) states[0].textContent = "Envoi des réponses...";
    if (states[1]) states[1].textContent = "Vérification des adresses IP en double...";
    if (states[2]) states[2].textContent = "Vérification de notre stock de produits...";
    if (states[3]) states[3].textContent = "Félicitations...";
}
  
if (typeof dones !== 'undefined') {
    if (dones[0]) dones[0].textContent = "Réponses envoyées";
    if (dones[1]) dones[1].textContent = "Adresse IP vérifiée";
    if (dones[2]) dones[2].textContent = "Produits disponibles en stock";
}

let stockLeft = 5;
if (!stockLeft) {
    stockLeft = Math.floor(Math.random() * (5 - 2 + 1)) + 2; // Stock aléatoire entre 2 et 5
    sessionStorage.setItem("stockLeft", stockLeft);
}

// Informations sur le stock et la récompense
prd4.innerHTML = `&nbsp;Stock restant : <b>(<span class='stockLeft animate__animated animate__flash animate__slower animate__infinite'> ${stockLeft} </span>)</b>`;
prd5.innerHTML = "&nbsp;Ne payez que les frais d'expédition !";
clmbtn.innerHTML = "<i class='fas fa-shopping-cart'></i> RÉCLAMER LA RÉCOMPENSE";

// Section des commentaires
cmfnt1.innerHTML = "Nouveau commentaire";
cmfnt2.innerHTML = "<span><i class='fas fa-comments'></i> Commentaires (5)</span><span><button><i class='fas fa-camera'></i></button><button>Envoyer</button></span>";

// Pied de page
ftrd1.innerHTML = "Copyright © " + datenhay(); 
ftrd2.innerHTML = "*Ce site n'est ni affilié ni approuvé par Sephora ou toute autre marque similaire, et ne prétend pas représenter ni posséder les droits ou marques associées à ces produits, qui restent la propriété de leurs détenteurs respectifs. La participation à ce sondage est volontaire et ne garantit pas l'obtention d'un prix. Les offres de tiers liées à ce sondage peuvent inclure des conditions supplémentaires, telles que des frais d'inscription ou un abonnement ; veuillez consulter toutes les conditions sur le site du tiers.<br/>Aucun achat ni paiement n'est requis pour participer à ce sondage. Pour plus de détails, veuillez consulter nos Conditions générales.<br><br><span id='btn-pripo'>Politique de confidentialité</span>&bull;<span id='btn-tercon'>Conditions générales</span><br/><br/><br/><br/>";

// Expiration de l'offre
offrex.innerHTML = "<div class='offerExpiry'>L'offre expire dans <span id='time'></span></div>";

// Modal pour les prix
mdprz1.innerHTML = "<p><span>Félicitations !</span> Nous avons réservé <b>(1)</b> <span id='modal-head-prod'></span> exclusivement pour vous !</p>";
mdprz2.innerHTML = "<p><span>Comment réclamer votre <span><span id='modal-head-prod2'></span> :</p><ol><li>Remplissez votre adresse de livraison.</li><li>Paiement uniquement des frais d'expédition pour recevoir votre prix.</li><li>Votre prix sera livré sous 5 à 7 jours ouvrables.</li></ol>";

// Bouton du modal
mdprzbtn.innerText = "Continuer";




var surveyData = [
  {
    "question": "À quelle fréquence faites-vous vos courses chez Sephora pour des produits de beauté ou de soin de la peau ?",
    "answers": [
      "Régulièrement, c'est mon magasin de beauté préféré",
      "Occasionnellement, lorsque j'ai besoin de quelque chose de spécifique",
      "Rarement, uniquement lors des soldes ou des vacances",
      "Jamais, c'est ma première fois"
    ]
  },
  {
    "question": "Avez-vous déjà acheté ou essayé des produits Lancôme ?",
    "answers": [
      "Oui, je suis un utilisateur régulier de Lancôme",
      "J'ai essayé quelques produits",
      "Pas encore, mais j'ai entendu de très bonnes choses",
      "Non, je n'ai jamais essayé Lancôme"
    ]
  },
  {
    "question": "Quel type de produit de beauté préférez-vous acheter ?",
    "answers": [
      "Soins de la peau (sérums, crèmes, nettoyants)",
      "Maquillage (fond de teint, mascara, rouge à lèvres)",
      "Parfums et fragrances",
      "Coffrets cadeaux ou éditions limitées"
    ]
  },
  {
    "question": "Si vous remportiez la Lancôme Beauty Box, quel produit essayeriez-vous en premier ?",
    "answers": [
      "Le Sérum Advanced Génifique",
      "Le Mascara Hypnôse",
      "Le Parfum La Vie Est Belle",
      "La Crème Rénergie Lift Multi-Action"
    ]
  },
  {
    "question": "Qu'est-ce qui vous intéresse le plus dans les concours de boîtes beauté comme celui-ci ?",
    "answers": [
      "La chance d'essayer de nouveaux produits",
      "L'expérience de la marque de luxe",
      "Un excellent rapport qualité-prix et une grande variété",
      "Parfait pour offrir ou partager"
    ]
  },
  {
    "question": "Où entendez-vous généralement parler des promotions ou des concours Sephora ?",
    "answers": [
      "Application Sephora ou newsletter par e-mail",
      "Réseaux sociaux ou influenceurs",
      "Présentoirs et échantillons en magasin",
      "Amis ou avis en ligne"
    ]
  },
  {
    "question": "Qu'est-ce qui vous inciterait à acheter davantage de produits Lancôme chez Sephora ?",
    "answers": [
      "Offres exclusives ou réductions",
      "Échantillons gratuits avec un achat",
      "Points de fidélité et récompenses",
      "Avis positifs d'autres personnes"
    ]
  },
  {
    "question": "Si Sephora organisait plus de concours, quelle marque aimeriez-vous voir ensuite ?",
    "answers": [
      "Estée Lauder",
      "Dior",
      "Clinique",
      "Charlotte Tilbury"
    ]
  }
];
 
var currentQuestionIndex = 0;
var totalQuestions = surveyData.length;

function renderQuestion(index) {
var questionData = surveyData[index];

// Update question text
document.querySelector('.qhwsdaa').textContent = questionData.question;

// Update question number
document.querySelector('.qawrv').textContent = 'Question ' + (index + 1) + ' sur ' + totalQuestions;

// Clear previous answers
var answerContainer = document.querySelector('.qassers');
answerContainer.innerHTML = ''; // Clear previous buttons

// Add new answer buttons
questionData.answers.forEach(function (answer) {
    var button = document.createElement('button');
    button.classList.add('qassersaa-select', 'qecsctct');
    button.textContent = answer;
    answerContainer.appendChild(button);

    // Add event listener to each button
    button.addEventListener('click', function () {
        if (currentQuestionIndex < totalQuestions - 1) {
            currentQuestionIndex++;
            renderQuestion(currentQuestionIndex);
        } else {
        document.getElementsByClassName("surveyContent")[0].classList.add("hdsnvnn_dvhddn");
        document.getElementById("verif-content").classList.remove("hdsnvnn_dvhddn");
            renderLoader();
        }
    });
});
}

// Start the survey when the DOM is ready
document.addEventListener("DOMContentLoaded", function () {
renderQuestion(currentQuestionIndex);  // Start rendering the first question
});




fetch('./js/comments.json')
.then(response => { 
    return response.json();
})
.then(data => {
    document.getElementById("comment-list").innerHTML = data.comments.map(comment => `
        <div class="tmmnasdiv">
        <div class="tmmnasimage">
            ${comment.prof ? `<img src="${comment.prof}" alt="User uploaded image">` : ""}
        
        </div>
        <div class="tmmnasdesc">
            <div class="tmmnasname">${comment.name}</div>
            <div class="tmmnastext">
                ${comment.text}
                <br/>
                ${comment.image ? `<img src="${comment.image}" alt="No review image">` : ""}
            </div>
            <div class="tmmnasfooter">
                <div class='tmmnastredffdatelike'><div><i class='fas fa-calendar-alt'></i><span>`+datenhax()+`</span></div><div><i class='fas fa-thumbs-up'></i><span>${comment.likes}</span></div></div><div><a href='#'>J'aime</a><a href='#'>Répondre</a></div>
            </div>
        </div>
        </div>
    `).join("");
})
.catch(error => {
    console.error('Error fetching comments:', error);
});



let expiryTime = Date.now() + (6 * 60 * 1000); // 6 minutes from now

function updateTimer() {
    let timeLeft = expiryTime - Date.now();
    if (timeLeft > 0) {
        let minutes = Math.floor(timeLeft / 60000);
        let seconds = ((timeLeft % 60000) / 1000).toFixed(0);
        document.getElementById("time").innerHTML = `<span class='cswccmctime-block'>${minutes}</span>:<span class='cswccmctime-block'>${seconds}</span>`;
    } else {
        document.getElementById("time").innerHTML = "Offre expirée.";
    }
}

// Update the timer every second
setInterval(updateTimer, 1000);

updateTimer();




const mdpripro = document.getElementById("modal-pri-pro");

// Function to handle modal content
function generatePrivacyPolicy() {
    return `
        <div class='modal mdlainn'>
            <div class='btn-close'>
                <h2>Politique de confidentialité</h2>
                <button id='btn-close-pri-pro' class='btn-close-cls'>
                    <i class='fas fa-times fa-lg'></i>
                </button>
            </div>
            <hr>
            <div class='modal-body mod-desc-ovr'>
                <p class='modeffdate'><b>Date d'entrée en vigueur : </b>${datehax()}</p>
                <p>Ce site respecte votre vie privée. Cette politique de confidentialité explique les types de données que nous pouvons collecter pendant votre participation à notre enquête, comment nous utilisons ces informations et vos droits à leur sujet.</p>
                <ol>
                    <li><b>Introduction et acceptation</b>
                        <ul>
                            <li><b>Données de suivi des clics :</b> Nous collectons des données non personnelles, telles que les clics et le comportement de navigation, afin de comprendre l'engagement des utilisateurs et d'améliorer notre site.</li>
                            <li><b>Aucune information personnelle :</b> Nous ne collectons ni ne traitons de données personnelles, telles que des noms, des emails ou des informations de paiement, lors de cette enquête. Les sites tiers liés peuvent collecter des données selon leurs propres politiques.</li>
                        </ul>
                    </li>
                    <li><b>Utilisation des informations</b>
                        <ul>
                            <li>Les données de suivi des clics sont utilisées uniquement pour améliorer l'expérience utilisateur et analyser l'engagement.</li>
                            <li>Nous ne partageons, ne vendons ni n'utilisons les données de suivi des clics en dehors d'analyses globales non identifiables.</li>
                        </ul>
                    </li>
                    <li><b>Liens et offres de tiers</b>
                        <ul>
                            <li>Notre site peut contenir des liens vers des offres de tiers. Ces sites fonctionnent de manière indépendante et ont leurs propres politiques de confidentialité. Nous ne sommes pas responsables de leur contenu, de leurs conditions ou de leurs pratiques de gestion des données.</li>
                            <li>Les données personnelles fournies sur des sites tiers sont régies par les politiques de confidentialité de ces sites. Ce site ne reçoit ni ne stocke aucune donnée que vous fournissez à ces sites.</li>
                        </ul>
                    </li>
                    <li><b>Partage et divulgation des données</b>
                        <ul>
                            <li>Nous ne partageons, ne vendons ni ne distribuons les données collectées, sauf si la loi l'exige (par exemple, en réponse à des subpoenas).</li>
                            <li>Si nos actifs sont vendus ou fusionnés, les données utilisateur agrégées ou anonymes peuvent être transférées avec les protections appropriées.</li>
                        </ul>
                    </li>
                    <li><b>Sécurité des données</b>
                        <ul>
                            <li>Nous mettons en œuvre des mesures de sécurité raisonnables pour protéger les données collectées contre un accès ou une divulgation non autorisés, mais nous ne pouvons garantir une sécurité absolue.</li>
                            <li>Les utilisateurs doivent examiner les pratiques de sécurité sur tout site tiers lié à notre promotion.</li>
                        </ul>
                    </li>
                    <li><b>Conservation des données</b>
                        <ul>
                            <li>Les données de suivi des clics sont conservées uniquement aussi longtemps que nécessaire à des fins analytiques ou comme l'exige la loi. En général, les données agrégées sont stockées pendant une période maximale de 2 ans.</li>
                        </ul>
                    </li>
                    <li><b>Vie privée des enfants</b>
                        <ul>
                            <li>Cette promotion est destinée aux personnes âgées de 18 ans ou plus. Nous ne collectons pas sciemment de données provenant d'enfants de moins de 18 ans.</li>
                        </ul>
                    </li>
                    <li><b>Mises à jour de la politique</b>
                        <ul>
                            <li>Cette politique de confidentialité peut être mise à jour périodiquement. Les changements seront publiés sur cette page avec une date d'entrée en vigueur mise à jour. L'utilisation continue de notre site constitue l'acceptation de toute politique révisée.</li>
                        </ul>
                    </li>
                </ol>
            </div>
            <div>&nbsp;</div>
        </div>
    `;
}

// Inject the generated HTML content into the modal
mdpripro.innerHTML = generatePrivacyPolicy();


const mdtercon = document.getElementById("modal-ter-con");

// Function to handle modal content
function generateTermsAndConditions() {
    return `
        <div class='modal mdlainn'>
            <div class='btn-close'>
                <h2>Conditions Générales</h2>
                <button id='btn-close-ter-con' class='btn-close-cls'>
                    <i class='fas fa-times fa-lg'></i>
                </button>
            </div>
            <hr>
            <div class='modal-body mod-desc-ovr'>
                <p class='modeffdate'><b>Date d'entrée en vigueur : </b>${datehax()}</p>
                <h3>Bienvenue dans notre enquête!</h3><br/>
                <p>Veuillez lire attentivement ces Conditions Générales avant de participer à notre enquête et à toute offre ou concours d'un tiers affilié. En participant, vous acceptez ces conditions dans leur intégralité. Si vous n'êtes pas d'accord, veuillez ne pas poursuivre cette enquête.</p>
                <ol>
                    <li><b>Introduction et acceptation</b><br/>Cette promotion d'enquête (“Promotion”) est gérée indépendamment par ce site et n'est affiliée à aucune marque ou produit mentionné dans cette enquête. Cette promotion vise à promouvoir des concours d'entreprises tierces. En participant à cette promotion, vous acceptez d'être lié par ces Conditions Générales, ainsi que par toutes les conditions définies par les entreprises tierces associées aux offres auxquelles vous pouvez accéder via ce site.</li>
                    <li><b>Éligibilité</b><br/>Cette promotion est ouverte aux résidents légaux de la France, âgés de 18 ans ou plus au moment de leur participation. Aucun achat ou paiement n'est requis pour participer ou gagner un prix associé à l'offre affiliée. Cette promotion est nulle là où la loi l'interdit.</li>
                    <li><b>Offres et Concours de Tiers</b><br/>Cette promotion peut inclure des liens vers des entreprises tierces offrant des opportunités de concours ou des prix. Ces entreprises tierces fonctionnent indépendamment de ce site et sont seules responsables de tous les aspects de leurs promotions, y compris la sélection des prix, l'exécution, l'éligibilité et les frais associés.<br/><br/>Bien qu'un frais d'entrée puisse être requis pour participer à certains concours de tiers, le paiement de ce frais n'est pas nécessaire pour participer à cette enquête et n'augmente pas vos chances de gagner. En suivant le lien vers toute offre de tiers, vous acceptez les conditions, politiques et politiques de confidentialité de cette entreprise. Ce site n'a aucun contrôle sur et n'est pas responsable des opérations, pratiques ou politiques des entreprises tierces.</li>
                    <li><b>Aucune Garantie de Gain</b><br/>La participation à cette enquête ou à toute offre de tiers ne garantit pas un prix ou un gain. Les gagnants de tout concours de tiers sont sélectionnés à la seule discrétion de l'opérateur tiers, conformément à leurs politiques et procédures. Ce site ne détermine pas la sélection des gagnants, le montant des prix ou les conditions d'éligibilité pour tout concours de tiers.</li>
                    <li><b>Collecte de Données et Confidentialité</b><br/>Nous respectons votre vie privée et ne collectons que des données de suivi des clics pour surveiller l'engagement avec notre promotion. Aucune information personnelle, telle que des adresses email, n'est collectée, traitée ou stockée par ce site. Ce site ne partage, ne vend ni ne distribue vos données de suivi des clics à des tiers, sauf si la loi l'exige. Pour des informations sur la manière dont vos données peuvent être utilisées lorsque vous interagissez avec des sites tiers, veuillez consulter les politiques de confidentialité respectives de ces sites.</li>
                    <li><b>Propriété Intellectuelle et Marques Déposées</b><br/>Toutes les marques, logos et noms de marques mentionnés dans cette promotion sont la propriété de leurs propriétaires respectifs. La mention de toute marque ou produit ne sous-entend aucune affiliation, parrainage ou approbation de la part du propriétaire de la marque. Cette promotion est gérée de manière indépendante et vise à promouvoir l'interaction des consommateurs sans le soutien direct ou l'autorisation de toutes les marques mentionnées.</li>
                    <li><b>Limitation de Responsabilité</b><br/>Ce site n'est pas responsable des actions ou pratiques de tout site tiers lié à cette promotion. Vous acceptez que votre interaction avec des sites tiers, y compris tout achat ou frais d'entrée, se fasse entièrement à vos risques et périls. Ce site ne pourra être tenu responsable des pertes, dommages ou réclamations découlant de votre interaction avec des sites ou offres tiers, y compris mais sans se limiter à l'éligibilité, l'exécution des prix, les frais et la gestion de toute information personnelle que vous choisissez de partager avec ces sites tiers.</li>
                    <li><b>Option de Désabonnement et Informations de Contact</b><br/>Si vous avez accédé à cette promotion par e-mail, annonce sur les réseaux sociaux, pop-up ou autre source en ligne, et souhaitez arrêter de recevoir des messages similaires, suivez simplement les instructions de désabonnement ou d'opt-out fournies dans le message ou la plateforme d'origine. Les utilisateurs sont encouragés à utiliser les options fournies sur la plateforme d'origine pour gérer leurs préférences concernant le contenu promotionnel.</li>
                    <li><b>Modification des Conditions</b><br/>Ce site se réserve le droit de mettre à jour ou de modifier ces Conditions Générales à tout moment, sans préavis. Toutes les mises à jour seront effectives immédiatement après leur publication sur ce site. La participation continue à cette promotion indique votre acceptation de toute révision des Conditions Générales. Il vous est conseillé de revoir ces conditions périodiquement pour rester informé de tout changement.</li>
                </ol>
            </div>
            <div>&nbsp;</div>
        </div>
    `;
}

// Inject the generated HTML content into the modal
mdtercon.innerHTML = generateTermsAndConditions();






document.getElementById("btn-pripo").onclick = function () {
    var modsclaim = document.getElementById("modal-pri-pro");
    modsclaim.classList.add("mdlabg");
    modsclaim.classList.remove("mdlabg-rv");
    modsclaim.children[0].classList.add("mdlainn");
    modsclaim.children[0].classList.remove("mdlainn-rv");
    modsclaim.classList.remove("hdsnvnn_dvhddn");
}

document.getElementById("btn-close-pri-pro").onclick = function () {
    var modsclaim = document.getElementById("modal-pri-pro");
    modsclaim.classList.remove("mdlabg");
    modsclaim.classList.add("mdlabg-rv");
    modsclaim.children[0].classList.remove("mdlainn");
    modsclaim.children[0].classList.add("mdlainn-rv");
    setTimeout(function(){
        modsclaim.classList.add("hdsnvnn_dvhddn");
    },900);
}


document.getElementById("btn-tercon").onclick = function () {
    var modsclaim = document.getElementById("modal-ter-con");
    modsclaim.classList.add("mdlabg");
    modsclaim.classList.remove("mdlabg-rv");
    modsclaim.children[0].classList.add("mdlainn");
    modsclaim.children[0].classList.remove("mdlainn-rv");
    modsclaim.classList.remove("hdsnvnn_dvhddn");
}

document.getElementById("btn-close-ter-con").onclick = function () {
    var modsclaim = document.getElementById("modal-ter-con");
    modsclaim.classList.remove("mdlabg");
    modsclaim.classList.add("mdlabg-rv");
    modsclaim.children[0].classList.remove("mdlainn");
    modsclaim.children[0].classList.add("mdlainn-rv");
    setTimeout(function(){
        modsclaim.classList.add("hdsnvnn_dvhddn");
    },900);
}






