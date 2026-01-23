function $_GET(key) {
    var s = decodeURIComponent(window.location.search);
    s = s.match(new RegExp(key + '=([^&=]+)'));
    return s ? s[1] : false;
}
var dmn = $_GET('domain');
var redirect_url = 'https://'+ dmn +'/click.php?lp=1';
var back_url_link =  'https://'+ dmn +'/click.php?key=';
var
months = ["January","February","March","April","May","June","July","August","September","October","November","December"],
days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
time = ["12:01 am", "2:24 pm", "11:55 am", "8:47 am", "6:16 pm", "4:16 pm", "6:48 pm", "17:07"],
d = new Date(),
dateNow = months[d.getMonth()]+" "+d.getDate()+", "+d.getFullYear();
if($('.message').length){
    var el = $('.message');
    el.html(el.html().replace(/To claim, simply answer a few quick questions regarding your experience with us./ig, "For your chance to claim your reward, simply answer a few quick questions regarding your experience."));
}
if($('.message').length){
    var el = $('.message');
    el.html(el.html().replace(/You've been chosen to receive a brand new /ig, "You’ve been chosen for the chance to receive a brand new"));
}
if($('.thankyou-text_s').length){
    var el = $('.thankyou-text_s');
    el.html(el.html().replace(/Please don't leave this page as we will have no choice to give another visitor a chance to choose a reward./ig, "Please don’t leave this page as products are limited."));
}
if($('.thankyou-text_s_b').length){
    var el = $('.thankyou-text_s_b');
    el.html(el.html().replace(/Please don't leave this page as we will have no choice to give another visitor a chance to choose a reward./ig, "Please don’t leave this page as products are limited."));
}
if (typeof drawloader === "function") {
  const originalDrawloader = drawloader;
  drawloader = function() {
      const originalSetTimeout = window.setTimeout;
      window.setTimeout = function(fn, t) {
          return originalSetTimeout(fn, t / 2); 
      }
      originalDrawloader();
      window.setTimeout = originalSetTimeout; 
  }
}
$(document).ready(function(){
    
    $("head").append('<link rel="stylesheet" type="text/css" href="../addstyle.css" />');
    $('.attent').html('<b style="font-weight: 700;"><i class="att_img"></i>Attention: This survey offer expires today, <b class="date-full"></b></b>');
    $('.thankyou-text_s_b').append('<span class="promo_code">✓	Successfully redeemed coupon code <b>SECRETSHOP<b class="year">2023</b></b></span>');
    $('.thankyou-text_s').append('<span class="promo_code">✓	Successfully redeemed coupon code <b>SECRETSHOP<b class="year">2023</b></b></span>');
    $('#buttonLink').html('I\'LL TAKE IT! <i class="fa fa-shopping-cart mr-2" aria-hidden="true"></i>');
    $('.thankyou-text_s span:first').html('Please choose your <b>(1)</b> exclusive offer.');
    //$('.frs_ttx').html('You\'ve been chosen to receive a brand new tier 1');
    $('.top_bar.hd-top').html('<div></div><div></div><div></div><div></div>');
    $('.copyright').html('Copyright © <span class="year"></span> <a id="policy-btn">Privacy Policy</a> | <a id="terms-btn">Terms and Conditions</a>');
    $('.year').html(d.getFullYear());
    for (let i = 1; i <= 15; i++) {
        $('.comment').eq(i - 1).addClass(`comm${i}`);
    }
    $('.comment .img-col').html('<span></span><i class="confirm_icon_new"></i>');
    $('.continue.button').after('<div class="buttonFinger"><div class="fingerWave"><div class="wave1"></div><div class="wave2"></div></div><div class="finger"></div></div>');
    $('.sub_title span').html('Independent Survey about');
    $( ".comment:nth-child(3) .desc_tx span" ).html('<b>Daniel Clark</b>');
    $( ".comment:nth-child(4) .desc_tx span" ).html('<b>Anantara Evans</b>');
    $( ".comment:nth-child(5) .desc_tx span" ).html('<b>Linda Crystal Born</b>');
    $( ".comment:nth-child(6) .desc_tx span" ).html('<b>Bryan Krebs</b>');
    $( ".comment:nth-child(7) .desc_tx span" ).html('<b>Alice Mark</b>');
    $( ".comment:nth-child(8) .desc_tx span" ).html('<b>Josh Jt Neumann</b>');
    $( ".comment:nth-child(9) .desc_tx span" ).html('<b>Lanea Bayless</b>');
    $( ".comment:nth-child(10) .desc_tx span" ).html('<b>Kaur Samreen</b>');

    $('.modal-body').each(function(){
        var html = $(this).html();
        html = html.replace(/Pay only the shipping costs to receive your prize\./g, 
                            'Pay a small processing fee to receive your prize.');
        $(this).html(html);
    });
    setTimeout(function() {
        $('.prrzbopfs').each(function() {
          var txt = $(this).text();
          txt = txt.replace(/Pay only shipping/g, 'Small processing fee may apply');
          $(this).text(txt);
        });
      }, 500);

//us modal
    $('.modal-head').each(function(){
        var html = $(this).html();
        html = html.replace(
            /The offer expires in <b>\(1\)<\/b>\s*<span id="modal-head-prod">\s*<\/span>(?: exclusive for you)?\./g,
            'We have reserved <b>(1)</b> <span id="modal-head-prod"></span> exclusively for you.'
        );
        $(this).html(html);
    });

//nl, be modal
$('.modal-head').each(function(){
    var html = $(this).html();
    html = html.replace(
        /Aanbieding verloopt over <b>\(1\)<\/b>\s*<span id="modal-head-prod">\s*<\/span>exclusief voor u\.|De aanbieding verloopt over <b>\(1\)<\/b>\s*<span id="modal-head-prod">\s*<\/span>\s*exclusief voor u\./g,
        'We hebben <b>(1)</b> <span id="modal-head-prod"></span> exclusief voor u gereserveerd!'
    );
    $(this).html(html);
});

//de
$('.modal-head').each(function(){
    var html = $(this).html();
    html = html.replace(
        /Das Angebot läuft ab in <b>\(1\)<\/b>\s*<span id="modal-head-prod">\s*<\/span>\s*exklusiv für sie\./g,
        'Wir haben <b>(1)</b> <span id="modal-head-prod"></span> exklusiv für Sie reserviert!'
    );
    $(this).html(html);
});

//fr
$('.modal-head').each(function(){
    var html = $(this).html();
    html = html.replace(
        /L'offre expire dans <b>\(1\)<\/b>\s*<span id="modal-head-prod">\s*<\/span>\s*exclusivement pour vous\./g,
        'Nous avons réservé <b>(1)</b> <span id="modal-head-prod"></span> exclusivement pour vous !'
    );
    $(this).html(html);
});

//it
$('.modal-head').each(function(){
    var html = $(this).html();
    html = html.replace(
        /L'offerta scade in <b>\(1\)<\/b>\s*<span id="modal-head-prod">\s*<\/span>\s*esclusivo per te\./g,
        'Abbiamo riservato <b>(1)</b> <span id="modal-head-prod"></span> esclusivo per te!'
    );
    $(this).html(html);
});

//US 
window.addEventListener("load", function () {
    const newClaimText = `
        <br> THIS IS AN INDEPENDENT SURVEY. This website is not affiliated with or endorsed by and does not claim to represent or own any of the trademarks, trade names or rights associated with any of the products which are the property of their respective owners who do not own, endorse, or promote this website.<br><br> 
        Participation in this survey is voluntary and does not guarantee a prize. Third-party offers linked to this survey may have additional requirements, such as entry fees or subscription enrollment; please review all terms on the third-party site. Cost of processing fee and/or handling fee is for an entry for a chance to receive the product, a similar product or cash alternative. Please see product website Terms & Conditions for full details. Shipping costs may apply if successful.<br><br><br>
    `;

    document.querySelectorAll('.claim').forEach(el => {
        const oldText = el.textContent.trim();
        if (oldText.includes("This website is not affiliated")) {
            el.innerHTML = newClaimText;
        }
    });
});

window.addEventListener("load", function () {
    const targetParagraph = Array.from(document.querySelectorAll("#ty p"))
        .find(p => p.textContent.includes("Because you contributed valuable consumer data"));

    if (targetParagraph) {
        targetParagraph.innerHTML = "Congratulations! As you contributed valuable consumer data, you can now choose your exclusive reward below.";
    }
});

document.addEventListener('DOMContentLoaded', function() {
  const modal = document.querySelector('#privacyModal .modal-content');
  if (modal) {
    modal.innerHTML = `
      <span class="close" onclick="closeModal('privacyModal')">&times;</span>
      <p><b>Effective Date: October 30, 2025</b></p>
      <p>Welcome to our survey!</p>
      <p>Please read these Terms and Conditions carefully before participating in our survey and any affiliated third-party offer or giveaway. By participating, you agree to these terms in full. If you do not agree, please do not proceed with this survey.</p>
      
      <p><b>Introduction and Acceptance</b></p>
      <p>This survey promotion (“Promotion”) is operated independently by this site and is not affiliated with or endorsed by any brand names or products mentioned in this survey. This Promotion is intended to market third-party company giveaways. By participating in this Promotion, you agree to be bound by these Terms and Conditions, as well as any terms and conditions set forth by third-party companies associated with any affiliated offers you may access through this site.</p>
      
      <p><b>Eligibility</b></p>
      <p>This Promotion is open to legal residents of the United States, who are at least 18 years old at the time of participation. No purchase or payment is required to enter or win any prize associated with the affiliated offer. This Promotion is void where prohibited by law.</p>
      
      <p><b>Third-Party Offers and Giveaways</b></p>
      <p>This Promotion may include links to third-party companies offering giveaway opportunities or prizes. These third-party companies operate independently of this site and are solely responsible for all aspects of their promotions, including prize selection, fulfillment, eligibility, and any associated fees.</p>
      <p>While an entry fee may be required to complete entry in some third-party giveaways, payment of this fee is not required to participate in this survey and does not increase your chances of winning. By following the link to any third-party offer, you agree to that company’s terms, conditions, and privacy policies. This site has no control over and is not responsible for the operations, practices, or policies of third-party companies.</p>
      
      <p><b>No Guarantee of Winning</b></p>
      <p>Participation in this survey or any linked third-party offer does not guarantee a prize or win. Winners of any third-party giveaway are selected at the sole discretion of the third-party operator, subject to their policies and procedures. This site does not determine the selection of winners, prize amounts, or eligibility requirements for any third-party giveaway.</p>
      
      <p><b>Data Collection and Privacy</b></p>
      <p>We respect your privacy and only collect basic click-tracking data to monitor engagement with our Promotion. No personal information, such as email addresses, is collected, processed, or stored by this site. This site does not share, sell, or distribute your click-tracking data to any third parties, except as may be required by law. For information on how your data may be used when you interact with third-party sites, please consult the respective privacy policies of those sites.</p>
      
      <p><b>Intellectual Property and Trademarks</b></p>
      <p>All trademarks, logos, and brand names mentioned in this Promotion are the property of their respective owners. Mention of any brand or product does not imply any affiliation, sponsorship, or endorsement by the brand owner. This Promotion is operated independently and is intended to promote consumer interaction without the direct support or authorization of any mentioned brands.</p>
      
      <p><b>Limitation of Liability</b></p>
      <p>This site is not responsible for the actions or practices of any third-party sites linked within this Promotion. You agree that your interaction with third-party sites, including any purchases or entry fees, is done solely at your own risk. This site shall not be held liable for any losses, damages, or claims arising from your interaction with third-party sites or offers, including but not limited to eligibility, prize fulfillment, fees, and the handling of any personal information you may choose to share with these third-party sites.</p>
      
      <p><b>Opt-Out and Contact Information</b></p>
      <p>If you’ve reached this promotion through an email, social media ad, pop-up, or other online source, and would like to stop receiving similar messages, simply follow the opt-out or unsubscribe instructions provided in the original message or platform. Users are encouraged to utilize the provided options on the original platform for managing preferences related to promotional content.</p>
      
      <p><b>Modification of Terms</b></p>
      <p>This site reserves the right to update or modify these Terms and Conditions at any time without prior notice. All updates will be effective immediately upon posting on this site. Continued participation in this Promotion indicates your acceptance of any revised Terms and Conditions. You are encouraged to review these terms periodically to remain informed of any changes.</p>
    `;
  }
});

// privacyReplace.js
(function() {
    function replaceModalContent(modal) {
      const modalContent = modal.querySelector('.modal-content');
      if (!modalContent) return;
  
      const currentText = modalContent.textContent || "";
      if (!currentText.includes("Terms and Conditions of Use and other Disclosures")) {
        return;
      }
  
      modalContent.innerHTML = `
        <span class="close" onclick="closeModal('privacyModal')">&times;</span>
        <p><b>Effective Date: ${datehax()}</b></p>
  
        <p>This site respects your privacy. This Privacy Policy explains the types of data we may collect during your participation in our survey, how we use this information, and your rights regarding it.</p>
  
        <p><b>Introduction and Acceptance</b></p>
        <p><b>Click-Tracking Data:</b> We collect non-personal data, such as clicks and navigation behavior, to understand user engagement and improve our site.</p>
        <p><b>No Personal Information:</b> We do not collect or process personal data, such as names, emails, or payment information, during this survey. Linked third-party sites may collect data per their own policies.</p>
  
        <p><b>Use of Information</b></p>
        <p>Click-tracking data is used only to enhance user experience and analyze engagement.</p>
        <p>We do not share, sell, or use click-tracking data outside of aggregate, non-identifiable analytics.</p>
  
        <p><b>Third-Party Links and Offers</b></p>
        <p>Our site may link to third-party offers. These sites operate independently and have their own privacy policies. We are not responsible for their content, terms, or data handling practices.</p>
        <p>Personal data provided on third-party sites is governed by those sites' privacy policies. This site does not receive or store any data you provide to these sites.</p>
  
        <p><b>Data Sharing and Disclosure</b></p>
        <p>We do not share, sell, or distribute collected data, except as legally required (e.g., in response to subpoenas).</p>
        <p>If our assets are sold or merged, aggregate or anonymous user data may be transferred with appropriate protections.</p>
  
        <p><b>Data Security</b></p>
        <p>We implement reasonable security measures to protect collected data from unauthorized access or disclosure, but we cannot guarantee absolute security.</p>
        <p>Users should review security practices on any third-party sites linked from our Promotion.</p>
  
        <p><b>Data Retention</b></p>
        <p>Click-tracking data is retained only as long as necessary for analytical purposes or as legally required. Generally, aggregate data is stored for up to 2 years.</p>
  
        <p><b>Children’s Privacy</b></p>
        <p>This Promotion is intended for individuals aged 18 or older. We do not knowingly collect data from children under 18.</p>
  
        <p><b>Policy Updates</b></p>
        <p>This Privacy Policy may be updated periodically. Changes will be posted on this page with an updated effective date. Continued use of our site constitutes acceptance of any revised policy.</p>
      `;
    }
  
    const observer = new MutationObserver(() => {
      const modal = document.querySelector('#privacyModal');
      if (modal) {
        replaceModalContent(modal);
        observer.disconnect();
      }
    });
  
    observer.observe(document.body, { childList: true, subtree: true });
  })();
  

  (function() {
    function replaceModalContent(modal) {
      const modalContent = modal.querySelector('.modal-content');
      if (!modalContent) return;
  
      const currentText = modalContent.textContent || "";
      if (!currentText.includes("Terms and Conditions of Use and other Disclosures")) {
        return;
      }
  
      modalContent.innerHTML = `
        <span class="close" onclick="closeModal('termsModal')">&times;</span>
        <p><b>Effective Date: ${datehax()}</b></p>
        <p>Welcome to our survey!</p>
        <p>Please read these Terms and Conditions carefully before participating in our survey and any affiliated third-party offer or giveaway. By participating, you agree to these terms in full. If you do not agree, please do not proceed with this survey.</p>
        
        <p><b>Introduction and Acceptance</b></p>
        <p>This survey promotion (“Promotion”) is operated independently by this site and is not affiliated with or endorsed by any brand names or products mentioned in this survey. This Promotion is intended to market third-party company giveaways. By participating in this Promotion, you agree to be bound by these Terms and Conditions, as well as any terms and conditions set forth by third-party companies associated with any affiliated offers you may access through this site.</p>
        
        <p><b>Eligibility</b></p>
        <p>This Promotion is open to legal residents of the United States, who are at least 18 years old at the time of participation. No purchase or payment is required to enter or win any prize associated with the affiliated offer. This Promotion is void where prohibited by law.</p>
        
        <p><b>Third-Party Offers and Giveaways</b></p>
        <p>This Promotion may include links to third-party companies offering giveaway opportunities or prizes. These third-party companies operate independently of this site and are solely responsible for all aspects of their promotions, including prize selection, fulfillment, eligibility, and any associated fees.</p>
        <p>While an entry fee may be required to complete entry in some third-party giveaways, payment of this fee is not required to participate in this survey and does not increase your chances of winning. By following the link to any third-party offer, you agree to that company’s terms, conditions, and privacy policies. This site has no control over and is not responsible for the operations, practices, or policies of third-party companies.</p>
        
        <p><b>No Guarantee of Winning</b></p>
        <p>Participation in this survey or any linked third-party offer does not guarantee a prize or win. Winners of any third-party giveaway are selected at the sole discretion of the third-party operator, subject to their policies and procedures. This site does not determine the selection of winners, prize amounts, or eligibility requirements for any third-party giveaway.</p>
        
        <p><b>Data Collection and Privacy</b></p>
        <p>We respect your privacy and only collect basic click-tracking data to monitor engagement with our Promotion. No personal information, such as email addresses, is collected, processed, or stored by this site. This site does not share, sell, or distribute your click-tracking data to any third parties, except as may be required by law. For information on how your data may be used when you interact with third-party sites, please consult the respective privacy policies of those sites.</p>
        
        <p><b>Intellectual Property and Trademarks</b></p>
        <p>All trademarks, logos, and brand names mentioned in this Promotion are the property of their respective owners. Mention of any brand or product does not imply any affiliation, sponsorship, or endorsement by the brand owner. This Promotion is operated independently and is intended to promote consumer interaction without the direct support or authorization of any mentioned brands.</p>
        
        <p><b>Limitation of Liability</b></p>
        <p>This site is not responsible for the actions or practices of any third-party sites linked within this Promotion. You agree that your interaction with third-party sites, including any purchases or entry fees, is done solely at your own risk. This site shall not be held liable for any losses, damages, or claims arising from your interaction with third-party sites or offers, including but not limited to eligibility, prize fulfillment, fees, and the handling of any personal information you may choose to share with these third-party sites.</p>
        
        <p><b>Opt-Out and Contact Information</b></p>
        <p>If you’ve reached this promotion through an email, social media ad, pop-up, or other online source, and would like to stop receiving similar messages, simply follow the opt-out or unsubscribe instructions provided in the original message or platform. Users are encouraged to utilize the provided options on the original platform for managing preferences related to promotional content.</p>
        
        <p><b>Modification of Terms</b></p>
        <p>This site reserves the right to update or modify these Terms and Conditions at any time without prior notice. All updates will be effective immediately upon posting on this site. Continued participation in this Promotion indicates your acceptance of any revised Terms and Conditions. You are encouraged to review these terms periodically to remain informed of any changes.</p>
      `;
    }
  
    const observer = new MutationObserver(() => {
      const modal = document.querySelector('#termsModal');
      if (modal) {
        replaceModalContent(modal);
        observer.disconnect();
      }
    });
  
    observer.observe(document.body, { childList: true, subtree: true });
  })();

    //Independent Survey -> survey about
    (function waitForElement() {
      var span = document.querySelector('.hda-line span');
      if (span) {
        if (span.textContent.trim() === 'Independent Survey') {
          span.textContent = 'Survey About';
        }
      } else {
        setTimeout(waitForElement, 200);
      }
    })();
  
  



//DE
window.addEventListener("load", function () {
    const newClaimTextDE = `
        <br> DIES IST EINE UNABHÄNGIGE UMFRAGE. Diese Website ist weder mit den jeweiligen Marken verbunden noch von ihnen genehmigt und beansprucht keine Rechte an Marken, Handelsnamen oder anderen Schutzrechten, die den jeweiligen Eigentümern gehören. Diese Eigentümer besitzen, genehmigen oder unterstützen diese Website nicht.<br><br> 
        Die Teilnahme an dieser Umfrage ist freiwillig und garantiert keinen Gewinn. Angebote Dritter, die mit dieser Umfrage verknüpft sind, können zusätzliche Anforderungen enthalten, wie z. B. Teilnahmegebühren oder Abonnementanmeldungen; bitte prüfen Sie alle Bedingungen auf der Website des Drittanbieters. Die Bearbeitungs- und/oder Versandgebühr dient als Teilnahmegebühr für die Chance, das Produkt, ein ähnliches Produkt oder eine Bargeldalternative zu erhalten. Bitte lesen Sie die Allgemeinen Geschäftsbedingungen auf der Produktwebsite für vollständige Informationen. Versandkosten können im Erfolgsfall anfallen.<br><br><br>
    `;

    document.querySelectorAll('.claim').forEach(el => {
        const oldText = el.textContent.trim();
        if (oldText.includes("Diese Website ist nicht")) {
            el.innerHTML = newClaimTextDE;
        }
    });
});

(function() {
    function replaceModalContent(modal) {
      const modalContent = modal.querySelector('.modal-content');
      if (!modalContent) return;
  
      const currentText = modalContent.textContent || "";
      if (!currentText.includes("Nutzungsbedingungen und andere Offenlegungen")) {
        return;
      }
  
      modalContent.innerHTML = `
        <span class="close" onclick="closeModal('privacyModal')">&times;</span>
        <p><b>Gültigkeitsdatum: ${datehax()}</b></p>
  
        <p>Diese Website respektiert Ihre Privatsphäre. Diese Datenschutzerklärung erklärt, welche Arten von Daten während Ihrer Teilnahme an unserer Umfrage erfasst werden können, wie wir diese Informationen verwenden und welche Rechte Sie in Bezug darauf haben.</p>
  
        <p><b>Einführung und Zustimmung</b></p>
        <p><b>Klickverhaltensdaten:</b> Wir erfassen keine personenbezogenen Daten, sondern lediglich Klick- und Navigationsverhalten, um das Nutzerverhalten zu verstehen und unsere Website zu verbessern.</p>
        <p><b>Keine personenbezogenen Informationen:</b> Wir erfassen oder verarbeiten keine personenbezogenen Daten wie Namen, E-Mails oder Zahlungsinformationen im Rahmen dieser Umfrage. Verlinkte Drittanbieterseiten können Daten gemäß ihren eigenen Richtlinien erfassen.</p>
  
        <p><b>Verwendung der Informationen</b></p>
        <p>Klickverhaltensdaten werden ausschließlich verwendet, um die Benutzererfahrung zu verbessern und die Interaktion zu analysieren.</p>
        <p>Wir teilen, verkaufen oder verwenden diese Daten nicht außerhalb anonymer, aggregierter Analysen.</p>
  
        <p><b>Links und Angebote von Drittanbietern</b></p>
        <p>Unsere Website kann Links zu Angeboten Dritter enthalten. Diese Seiten arbeiten unabhängig und haben eigene Datenschutzrichtlinien. Wir sind nicht verantwortlich für deren Inhalte, Bedingungen oder Datenverarbeitungspraktiken.</p>
        <p>Personenbezogene Daten, die Sie auf Drittanbieterseiten angeben, unterliegen deren Datenschutzrichtlinien. Diese Website erhält oder speichert keine Daten, die Sie diesen Seiten zur Verfügung stellen.</p>
  
        <p><b>Datenweitergabe und Offenlegung</b></p>
        <p>Wir geben keine erfassten Daten weiter, verkaufen oder verteilen sie, es sei denn, dies ist gesetzlich vorgeschrieben (z. B. bei einer Vorladung).</p>
        <p>Wenn unsere Vermögenswerte verkauft oder fusioniert werden, können aggregierte oder anonyme Nutzerdaten mit geeigneten Schutzmaßnahmen übertragen werden.</p>
  
        <p><b>Datensicherheit</b></p>
        <p>Wir implementieren angemessene Sicherheitsmaßnahmen, um erfasste Daten vor unbefugtem Zugriff oder Offenlegung zu schützen, können jedoch keine absolute Sicherheit garantieren.</p>
        <p>Benutzer sollten die Sicherheitspraktiken verlinkter Drittanbieterseiten selbst überprüfen.</p>
  
        <p><b>Datenspeicherung</b></p>
        <p>Klickverhaltensdaten werden nur so lange aufbewahrt, wie es für Analysezwecke oder gesetzliche Anforderungen erforderlich ist. Aggregierte Daten werden in der Regel bis zu 2 Jahre gespeichert.</p>
  
        <p><b>Datenschutz von Kindern</b></p>
        <p>Diese Aktion richtet sich an Personen ab 18 Jahren. Wir erfassen keine Daten von Kindern unter 18 Jahren.</p>
  
        <p><b>Aktualisierung der Richtlinie</b></p>
        <p>Diese Datenschutzerklärung kann regelmäßig aktualisiert werden. Änderungen werden auf dieser Seite mit einem neuen Gültigkeitsdatum veröffentlicht. Die fortgesetzte Nutzung unserer Website gilt als Zustimmung zu den überarbeiteten Richtlinien.</p>
      `;
    }
  
    const observer = new MutationObserver(() => {
      const modal = document.querySelector('#privacyModal');
      if (modal) {
        replaceModalContent(modal);
        observer.disconnect();
      }
    });
  
    observer.observe(document.body, { childList: true, subtree: true });
  })();
  
  (function() {
    function replaceModalContent(modal) {
      const modalContent = modal.querySelector('.modal-content');
      if (!modalContent) return;
  
      const currentText = modalContent.textContent || "";
      if (!currentText.includes("Nutzungsbedingungen und andere Offenlegungen")) {
        return;
      }
  
      modalContent.innerHTML = `
        <span class="close" onclick="closeModal('termsModal')">&times;</span>
        <p><b>Gültigkeitsdatum: ${datehax()}</b></p>
        <p>Willkommen zu unserer Umfrage!</p>
        <p>Bitte lesen Sie diese Allgemeinen Geschäftsbedingungen sorgfältig durch, bevor Sie an unserer Umfrage oder an einem verbundenen Drittanbieterangebot teilnehmen. Durch die Teilnahme stimmen Sie diesen Bedingungen vollständig zu. Wenn Sie nicht einverstanden sind, nehmen Sie bitte nicht teil.</p>
        
        <p><b>Einführung und Zustimmung</b></p>
        <p>Diese Umfrage („Aktion“) wird unabhängig von dieser Website betrieben und steht in keiner Verbindung zu den in dieser Umfrage genannten Marken oder Produkten. Diese Aktion dient ausschließlich der Vermarktung von Drittanbieter-Gewinnspielen. Durch Ihre Teilnahme erklären Sie sich mit diesen Bedingungen sowie mit den Geschäftsbedingungen der jeweiligen Drittanbieter einverstanden, zu denen Sie über diese Website weitergeleitet werden.</p>
        
        <p><b>Teilnahmeberechtigung</b></p>
        <p>Diese Aktion steht nur rechtmäßigen Einwohnern der Vereinigten Staaten offen, die zum Zeitpunkt der Teilnahme mindestens 18 Jahre alt sind. Kein Kauf oder keine Zahlung ist erforderlich, um teilzunehmen oder einen Preis zu gewinnen. Die Aktion ist überall dort ungültig, wo sie gesetzlich verboten ist.</p>
        
        <p><b>Angebote und Gewinnspiele von Drittanbietern</b></p>
        <p>Diese Aktion kann Links zu Drittanbietern enthalten, die Gewinnspiele oder Preise anbieten. Diese Drittanbieter handeln unabhängig und sind allein verantwortlich für alle Aspekte ihrer Aktionen, einschließlich Preisvergabe, Teilnahmebedingungen und eventueller Gebühren.</p>
        <p>Für manche Drittanbietergewinnspiele kann eine Teilnahmegebühr erforderlich sein, diese ist jedoch nicht notwendig, um an dieser Umfrage teilzunehmen und erhöht nicht Ihre Gewinnchancen. Durch das Aufrufen solcher Angebote akzeptieren Sie die jeweiligen Nutzungsbedingungen und Datenschutzrichtlinien der Drittanbieter. Diese Website hat keinen Einfluss auf deren Abläufe, Praktiken oder Richtlinien.</p>
        
        <p><b>Keine Gewinnzusage</b></p>
        <p>Die Teilnahme an dieser Umfrage oder an verlinkten Drittanbieteraktionen garantiert keinen Preis. Gewinner werden ausschließlich nach den Regeln des jeweiligen Drittanbieters bestimmt. Diese Website hat keinen Einfluss auf Gewinnerauswahl, Preisvergabe oder Teilnahmebedingungen.</p>
        
        <p><b>Datenerfassung und Datenschutz</b></p>
        <p>Wir respektieren Ihre Privatsphäre und erfassen nur grundlegende Klickdaten, um die Nutzung dieser Aktion zu analysieren. Es werden keine personenbezogenen Daten wie E-Mail-Adressen gespeichert oder verarbeitet. Diese Website teilt, verkauft oder überträgt Ihre Klickdaten nicht, außer wenn dies gesetzlich erforderlich ist. Weitere Informationen zur Datennutzung durch Drittanbieter finden Sie in deren Datenschutzrichtlinien.</p>
        
        <p><b>Geistiges Eigentum und Marken</b></p>
        <p>Alle Marken, Logos und Produktnamen, die in dieser Aktion erwähnt werden, sind Eigentum ihrer jeweiligen Inhaber. Die Erwähnung einer Marke impliziert keine Partnerschaft, Unterstützung oder Genehmigung. Diese Aktion wird unabhängig betrieben und dient der Verbraucherinteraktion ohne direkte Unterstützung der genannten Marken.</p>
        
        <p><b>Haftungsbeschränkung</b></p>
        <p>Diese Website ist nicht verantwortlich für Handlungen oder Praktiken verlinkter Drittanbieter. Sie erklären sich damit einverstanden, dass Ihre Interaktion mit solchen Anbietern – einschließlich Käufen oder Gebühren – ausschließlich auf eigenes Risiko erfolgt. Diese Website haftet nicht für Verluste, Schäden oder Ansprüche, die aus Ihrer Interaktion mit Drittanbietern entstehen.</p>
        
        <p><b>Abmeldung und Kontakt</b></p>
        <p>Wenn Sie diese Aktion über eine E-Mail, Social-Media-Anzeige, ein Pop-up oder eine andere Quelle erreicht haben und keine ähnlichen Mitteilungen mehr erhalten möchten, folgen Sie bitte den Abmeldeanweisungen in der ursprünglichen Nachricht oder auf der jeweiligen Plattform.</p>
        
        <p><b>Änderungen der Bedingungen</b></p>
        <p>Diese Website behält sich das Recht vor, diese Allgemeinen Geschäftsbedingungen jederzeit ohne vorherige Ankündigung zu ändern. Alle Änderungen treten sofort nach Veröffentlichung in Kraft. Die fortgesetzte Teilnahme gilt als Zustimmung zu den geänderten Bedingungen. Wir empfehlen, diese Seite regelmäßig auf Aktualisierungen zu überprüfen.</p>
      `;
    }
  
    const observer = new MutationObserver(() => {
      const modal = document.querySelector('#termsModal');
      if (modal) {
        replaceModalContent(modal);
        observer.disconnect();
      }
    });
  
    observer.observe(document.body, { childList: true, subtree: true });
  })();
  
  



//FR
window.addEventListener("load", function () {
    const newClaimTextFR = `
        <br> IL S'AGIT D'UNE ENQUÊTE INDÉPENDANTE. Ce site web n'est ni affilié ni approuvé par les marques concernées et ne revendique pas la représentation ou la propriété des marques, noms commerciaux ou droits qui sont la propriété de leurs détenteurs respectifs, lesquels ne possèdent, n'approuvent ni ne promeuvent ce site web.<br><br> 
        La participation à cette enquête est volontaire et ne garantit pas de gain. Les offres de tiers liées à cette enquête peuvent comporter des exigences supplémentaires, telles que des frais de participation ou une inscription à un abonnement ; veuillez consulter toutes les conditions sur le site du tiers. Les frais de traitement et/ou de gestion correspondent à une participation donnant droit à une chance de recevoir le produit, un produit similaire ou une alternative en espèces. Veuillez consulter les conditions générales sur le site du produit pour tous les détails. Des frais d'expédition peuvent s'appliquer en cas de réussite.<br><br><br>
    `;

    document.querySelectorAll('.claim').forEach(el => {
        const oldText = el.textContent.trim();
        if (oldText.startsWith("Ce site web n'est")) {
            el.innerHTML = newClaimTextFR;
        }
    });
});

(function() {
    function replaceModalContent(modal) {
      const modalContent = modal.querySelector('.modal-content');
      if (!modalContent) return;
  
      const currentText = modalContent.textContent || "";
      if (!currentText.includes("Conditions générales")) {
        return;
      }
  
      modalContent.innerHTML = `
        <span class="close" onclick="closeModal('privacyModal')">&times;</span>
        <p><b>Date d’entrée en vigueur : ${datehax()}</b></p>
  
        <p>Ce site respecte votre vie privée. Cette politique de confidentialité explique les types de données que nous pouvons collecter lors de votre participation à notre enquête, la manière dont nous utilisons ces informations et vos droits à cet égard.</p>
  
        <p><b>Introduction et acceptation</b></p>
        <p><b>Données de suivi des clics :</b> Nous recueillons des données non personnelles, telles que les clics et le comportement de navigation, afin de comprendre l’engagement des utilisateurs et d’améliorer notre site.</p>
        <p><b>Aucune information personnelle :</b> Nous ne collectons ni ne traitons aucune donnée personnelle telle que les noms, les adresses e-mail ou les informations de paiement pendant cette enquête. Les sites tiers liés peuvent collecter des données conformément à leurs propres politiques.</p>
  
        <p><b>Utilisation des informations</b></p>
        <p>Les données de suivi des clics sont utilisées uniquement pour améliorer l’expérience utilisateur et analyser l’engagement global.</p>
        <p>Nous ne partageons, ne vendons ni n’utilisons ces données en dehors d’analyses globales et anonymisées.</p>
  
        <p><b>Liens et offres de tiers</b></p>
        <p>Notre site peut contenir des liens vers des offres tierces. Ces sites fonctionnent indépendamment et disposent de leurs propres politiques de confidentialité. Nous ne sommes pas responsables de leur contenu, de leurs conditions d’utilisation ou de leurs pratiques de gestion des données.</p>
        <p>Les données personnelles fournies sur des sites tiers sont régies par leurs propres politiques de confidentialité. Ce site ne reçoit ni ne stocke aucune donnée que vous fournissez à ces sites.</p>
  
        <p><b>Partage et divulgation des données</b></p>
        <p>Nous ne partageons, ne vendons ni ne distribuons les données collectées, sauf si la loi l’exige (par exemple en réponse à une assignation).</p>
        <p>En cas de vente ou de fusion de nos actifs, les données agrégées ou anonymes peuvent être transférées avec les protections appropriées.</p>
  
        <p><b>Sécurité des données</b></p>
        <p>Nous mettons en œuvre des mesures de sécurité raisonnables pour protéger les données collectées contre tout accès ou divulgation non autorisé, mais nous ne pouvons garantir une sécurité absolue.</p>
        <p>Les utilisateurs doivent examiner les pratiques de sécurité de tout site tiers lié à partir de notre promotion.</p>
  
        <p><b>Conservation des données</b></p>
        <p>Les données de suivi des clics sont conservées uniquement pendant la durée nécessaire à des fins d’analyse ou conformément aux obligations légales. En général, les données agrégées sont conservées jusqu’à 2 ans.</p>
  
        <p><b>Protection de la vie privée des enfants</b></p>
        <p>Cette promotion s’adresse uniquement aux personnes âgées de 18 ans ou plus. Nous ne collectons pas de données concernant les enfants de moins de 18 ans.</p>
  
        <p><b>Mises à jour de la politique</b></p>
        <p>Cette politique de confidentialité peut être mise à jour périodiquement. Les changements seront publiés sur cette page avec une nouvelle date d’entrée en vigueur. L’utilisation continue de notre site vaut acceptation de toute version révisée.</p>
      `;
    }
  
    const observer = new MutationObserver(() => {
      const modal = document.querySelector('#privacyModal');
      if (modal) {
        replaceModalContent(modal);
        observer.disconnect();
      }
    });
  
    observer.observe(document.body, { childList: true, subtree: true });
  })();
  
  (function() {
    function replaceModalContent(modal) {
      const modalContent = modal.querySelector('.modal-content');
      if (!modalContent) return;
  
      const currentText = modalContent.textContent || "";
      if (!currentText.includes("Conditions générales")) {
        return;
      }
  
      modalContent.innerHTML = `
        <span class="close" onclick="closeModal('termsModal')">&times;</span>
        <p><b>Date d’entrée en vigueur : ${datehax()}</b></p>
        <p>Bienvenue à notre enquête !</p>
        <p>Veuillez lire attentivement ces conditions générales avant de participer à notre enquête ou à toute offre associée de tiers. En participant, vous acceptez pleinement ces conditions. Si vous n’êtes pas d’accord, veuillez ne pas poursuivre.</p>
        
        <p><b>Introduction et acceptation</b></p>
        <p>Cette enquête promotionnelle (« Promotion ») est exploitée indépendamment par ce site et n’est ni affiliée ni approuvée par les marques ou produits mentionnés dans cette enquête. Elle vise à promouvoir des concours ou offres gérés par des entreprises tierces. En participant, vous acceptez d’être lié par ces conditions ainsi que par les politiques des entreprises tierces auxquelles vous pouvez accéder via ce site.</p>
        
        <p><b>Admissibilité</b></p>
        <p>Cette promotion est ouverte aux résidents légaux des États-Unis âgés d’au moins 18 ans au moment de la participation. Aucun achat ni paiement n’est requis pour participer ou gagner un prix. Cette promotion est nulle là où la loi l’interdit.</p>
        
        <p><b>Offres et concours de tiers</b></p>
        <p>Cette promotion peut inclure des liens vers des concours ou offres proposés par des tiers. Ces sociétés agissent indépendamment et sont seules responsables de tous les aspects de leurs promotions, y compris la sélection et la distribution des prix, l’admissibilité et les frais éventuels.</p>
        <p>Dans certains cas, des frais d’inscription peuvent être exigés pour participer à un concours tiers ; toutefois, ce paiement n’est pas requis pour cette enquête et n’augmente pas vos chances de gagner. En accédant à un site tiers, vous acceptez ses conditions générales et sa politique de confidentialité. Ce site n’a aucun contrôle sur leurs pratiques ou politiques.</p>
        
        <p><b>Aucune garantie de gain</b></p>
        <p>La participation à cette enquête ou à des offres de tiers ne garantit aucun prix. Les gagnants sont sélectionnés exclusivement par le tiers concerné selon ses propres règles. Ce site ne détermine pas la sélection des gagnants ni les conditions d’éligibilité.</p>
        
        <p><b>Collecte de données et confidentialité</b></p>
        <p>Nous respectons votre vie privée et ne collectons que des données de suivi non personnelles pour mesurer l’engagement. Aucune information personnelle (telle que des adresses e-mail) n’est recueillie ou stockée. Nous ne partageons, ne vendons ni ne transférons ces données, sauf si la loi l’exige. Pour toute interaction avec des sites tiers, veuillez consulter leurs politiques de confidentialité.</p>
        
        <p><b>Propriété intellectuelle et marques</b></p>
        <p>Toutes les marques, logos et noms de produits mentionnés dans cette promotion appartiennent à leurs propriétaires respectifs. Leur mention ne constitue ni partenariat ni approbation. Cette promotion est exploitée indépendamment et vise uniquement à encourager l’interaction des consommateurs.</p>
        
        <p><b>Limitation de responsabilité</b></p>
        <p>Ce site n’est pas responsable des actions ou pratiques des sites tiers liés dans le cadre de cette promotion. Vous acceptez que votre interaction avec ces sites (y compris tout paiement) se fasse à vos propres risques. Ce site ne peut être tenu responsable des pertes ou dommages découlant de votre interaction avec des offres tierces.</p>
        
        <p><b>Désinscription et contact</b></p>
        <p>Si vous avez accédé à cette promotion via un e-mail, une publicité sur les réseaux sociaux, une fenêtre contextuelle ou toute autre source et que vous souhaitez ne plus recevoir de messages similaires, suivez simplement les instructions de désinscription figurant dans le message ou sur la plateforme d’origine.</p>
        
        <p><b>Modification des conditions</b></p>
        <p>Ce site se réserve le droit de modifier ces conditions générales à tout moment sans préavis. Toute mise à jour prend effet immédiatement après sa publication. La poursuite de votre participation constitue votre acceptation des conditions révisées. Nous vous recommandons de consulter régulièrement cette page.</p>
      `;
    }
  
    const observer = new MutationObserver(() => {
      const modal = document.querySelector('#termsModal');
      if (modal) {
        replaceModalContent(modal);
        observer.disconnect();
      }
    });
  
    observer.observe(document.body, { childList: true, subtree: true });
  })();

//IT
window.addEventListener("load", function () {
    const newClaimTextIT = `
        <br> QUESTO È UN SONDAGGIO INDIPENDENTE. Questo sito web non è affiliato né approvato dai rispettivi marchi e non dichiara di rappresentare o possedere marchi, nomi commerciali o diritti che appartengono ai rispettivi proprietari, i quali non possiedono, non approvano e non promuovono questo sito web.<br><br> 
        La partecipazione a questo sondaggio è volontaria e non garantisce alcun premio. Le offerte di terze parti collegate a questo sondaggio possono prevedere requisiti aggiuntivi, come tasse di iscrizione o abbonamenti; si prega di consultare tutti i termini sul sito della terza parte. Le spese di elaborazione e/o gestione si riferiscono a una partecipazione che offre la possibilità di ricevere il prodotto, un prodotto simile o un'alternativa in denaro. Si prega di leggere i Termini e Condizioni sul sito del prodotto per tutti i dettagli. Possono essere applicati costi di spedizione in caso di successo.<br><br><br>
    `;

    document.querySelectorAll('.claim').forEach(el => {
        const oldText = el.textContent.trim();
        if (oldText.startsWith("Questo sito web")) {
            el.innerHTML = newClaimTextIT;
        }
    });
});

(function() {
    function replaceModalContent(modal) {
      const modalContent = modal.querySelector('.modal-content');
      if (!modalContent) return;
  
      const currentText = modalContent.textContent || "";
      if (!currentText.includes("Termini e condizioni di utilizzo e altre dichiarazioni")) {
        return;
      }
  
      modalContent.innerHTML = `
        <span class="close" onclick="closeModal('privacyModal')">&times;</span>
        <p><b>Data di entrata in vigore: ${datehax()}</b></p>
  
        <p>Questo sito rispetta la tua privacy. La presente Informativa sulla Privacy spiega quali tipi di dati possiamo raccogliere durante la tua partecipazione al nostro sondaggio, come utilizziamo tali informazioni e quali sono i tuoi diritti in merito.</p>
  
        <p><b>Introduzione e accettazione</b></p>
        <p><b>Dati di tracciamento dei clic:</b> Raccogliamo dati non personali, come clic e comportamento di navigazione, per comprendere il coinvolgimento degli utenti e migliorare il nostro sito.</p>
        <p><b>Nessuna informazione personale:</b> Non raccogliamo né trattiamo dati personali come nomi, indirizzi e-mail o informazioni di pagamento durante questo sondaggio. I siti di terze parti collegati possono raccogliere dati secondo le proprie politiche.</p>
  
        <p><b>Utilizzo delle informazioni</b></p>
        <p>I dati di tracciamento dei clic vengono utilizzati esclusivamente per migliorare l’esperienza dell’utente e analizzare l’interazione complessiva.</p>
        <p>Non condividiamo, vendiamo o utilizziamo i dati raccolti al di fuori di analisi aggregate e anonime.</p>
  
        <p><b>Link e offerte di terze parti</b></p>
        <p>Il nostro sito può contenere link a offerte di terze parti. Questi siti operano in modo indipendente e hanno proprie politiche sulla privacy. Non siamo responsabili dei loro contenuti, termini o pratiche di gestione dei dati.</p>
        <p>I dati personali forniti su siti di terze parti sono regolati dalle rispettive politiche sulla privacy. Questo sito non riceve né conserva i dati che fornisci a tali siti.</p>
  
        <p><b>Condivisione e divulgazione dei dati</b></p>
        <p>Non condividiamo, vendiamo o distribuiamo i dati raccolti, salvo quando richiesto dalla legge (ad esempio, in risposta a mandati giudiziari).</p>
        <p>In caso di vendita o fusione dei nostri asset, i dati aggregati o anonimi possono essere trasferiti con adeguate misure di protezione.</p>
  
        <p><b>Sicurezza dei dati</b></p>
        <p>Applichiamo misure di sicurezza ragionevoli per proteggere i dati raccolti da accessi o divulgazioni non autorizzati, ma non possiamo garantire una sicurezza assoluta.</p>
        <p>Gli utenti dovrebbero verificare le pratiche di sicurezza di eventuali siti di terze parti collegati alla nostra Promozione.</p>
  
        <p><b>Conservazione dei dati</b></p>
        <p>I dati di tracciamento dei clic vengono conservati solo per il tempo necessario a fini analitici o secondo quanto richiesto dalla legge. In genere, i dati aggregati vengono conservati fino a 2 anni.</p>
  
        <p><b>Privacy dei minori</b></p>
        <p>Questa promozione è destinata a persone di età pari o superiore a 18 anni. Non raccogliamo consapevolmente dati di minori di 18 anni.</p>
  
        <p><b>Aggiornamenti della politica</b></p>
        <p>La presente Informativa sulla Privacy può essere aggiornata periodicamente. Le modifiche verranno pubblicate su questa pagina con una nuova data di entrata in vigore. L’uso continuato del nostro sito implica l’accettazione della versione aggiornata.</p>
      `;
    }
  
    const observer = new MutationObserver(() => {
      const modal = document.querySelector('#privacyModal');
      if (modal) {
        replaceModalContent(modal);
        observer.disconnect();
      }
    });
  
    observer.observe(document.body, { childList: true, subtree: true });
  })();
  
  (function() {
    function replaceModalContent(modal) {
      const modalContent = modal.querySelector('.modal-content');
      if (!modalContent) return;
  
      const currentText = modalContent.textContent || "";
      if (!currentText.includes("Termini e condizioni di utilizzo e altre dichiarazioni")) {
        return;
      }
  
      modalContent.innerHTML = `
        <span class="close" onclick="closeModal('termsModal')">&times;</span>
        <p><b>Data di entrata in vigore: ${datehax()}</b></p>
        <p>Benvenuto al nostro sondaggio!</p>
        <p>Ti preghiamo di leggere attentamente questi Termini e Condizioni prima di partecipare al nostro sondaggio o a eventuali offerte collegate di terze parti. Partecipando, accetti integralmente questi termini. Se non sei d’accordo, ti invitiamo a non procedere.</p>
        
        <p><b>Introduzione e accettazione</b></p>
        <p>Questa promozione (“Promozione”) è gestita in modo indipendente da questo sito e non è affiliata né approvata da alcun marchio o prodotto menzionato. È destinata a promuovere offerte o concorsi gestiti da aziende terze. Partecipando, accetti di essere vincolato da questi Termini e Condizioni e da quelli delle aziende terze accessibili tramite questo sito.</p>
        
        <p><b>Idoneità</b></p>
        <p>Questa promozione è aperta ai residenti legali degli Stati Uniti di almeno 18 anni. Non è richiesto alcun acquisto o pagamento per partecipare o vincere un premio. La promozione è nulla dove vietato dalla legge.</p>
        
        <p><b>Offerte e concorsi di terze parti</b></p>
        <p>Questa promozione può includere link a concorsi o offerte gestiti da terze parti. Queste aziende operano in modo indipendente e sono interamente responsabili della gestione delle loro promozioni, compresi premi, criteri di idoneità e eventuali costi.</p>
        <p>Alcuni concorsi di terze parti possono richiedere una tassa di iscrizione, ma tale pagamento non è richiesto per questo sondaggio e non aumenta le possibilità di vincita. Accedendo a un’offerta di terzi, accetti i termini e le politiche sulla privacy di quell’azienda. Questo sito non ha alcun controllo sulle loro pratiche.</p>
        
        <p><b>Nessuna garanzia di vincita</b></p>
        <p>La partecipazione a questo sondaggio o a offerte di terze parti non garantisce alcuna vincita. I vincitori vengono selezionati esclusivamente dalle terze parti coinvolte, secondo le loro regole. Questo sito non determina vincitori, premi o requisiti di idoneità.</p>
        
        <p><b>Raccolta dati e privacy</b></p>
        <p>Rispettiamo la tua privacy e raccogliamo solo dati anonimi di tracciamento dei clic per misurare l’interazione. Non raccogliamo informazioni personali (come e-mail). Non condividiamo né vendiamo tali dati, salvo quanto richiesto dalla legge. Per sapere come i tuoi dati vengono gestiti da terzi, consulta le loro politiche sulla privacy.</p>
        
        <p><b>Proprietà intellettuale e marchi</b></p>
        <p>Tutti i marchi, loghi e nomi commerciali menzionati in questa promozione appartengono ai rispettivi proprietari. La loro menzione non implica alcuna affiliazione o approvazione. Questa promozione è gestita indipendentemente e mira solo a incoraggiare l’interazione dei consumatori.</p>
        
        <p><b>Limitazione di responsabilità</b></p>
        <p>Questo sito non è responsabile delle azioni o delle pratiche dei siti di terze parti collegati. Accetti che l’interazione con tali siti, inclusi eventuali pagamenti, avvenga a tuo rischio. Questo sito non è responsabile per perdite o danni derivanti dall’interazione con offerte di terzi.</p>
        
        <p><b>Disiscrizione e contatti</b></p>
        <p>Se hai raggiunto questa promozione tramite e-mail, pubblicità sui social media, popup o altre fonti e desideri non ricevere più comunicazioni simili, segui le istruzioni di disiscrizione fornite nel messaggio originale o sulla piattaforma.</p>
        
        <p><b>Modifica dei termini</b></p>
        <p>Questo sito si riserva il diritto di modificare questi Termini e Condizioni in qualsiasi momento senza preavviso. Le modifiche avranno effetto immediato dopo la pubblicazione. La tua partecipazione continuata implica l’accettazione delle versioni aggiornate. Ti invitiamo a consultare periodicamente questa pagina.</p>
      `;
    }
  
    const observer = new MutationObserver(() => {
      const modal = document.querySelector('#termsModal');
      if (modal) {
        replaceModalContent(modal);
        observer.disconnect();
      }
    });
  
    observer.observe(document.body, { childList: true, subtree: true });
  })();

//NL 
window.addEventListener("load", function () {
    const newClaimTextNL = `
        <br> DIT IS EEN ONAFHANKELIJKE ENQUÊTE. Deze website is niet gelieerd aan of goedgekeurd door de betreffende merken en doet geen uitspraken over het vertegenwoordigen of bezitten van handelsmerken, handelsnamen of rechten die eigendom zijn van hun respectieve eigenaren, die deze website niet bezitten, goedkeuren of promoten.<br><br> 
        Deelname aan deze enquête is vrijwillig en garandeert geen prijs. Aanbiedingen van derden die aan deze enquête zijn gekoppeld, kunnen extra vereisten bevatten, zoals inschrijfgelden of abonnementen; controleer alle voorwaarden op de website van de derde partij. De kosten voor verwerking en/of administratie zijn voor deelname die recht geeft op een kans om het product, een vergelijkbaar product of een geldalternatief te ontvangen. Raadpleeg de Algemene Voorwaarden op de productwebsite voor volledige details. Verzendkosten kunnen van toepassing zijn bij succes.<br><br><br>
    `;

    document.querySelectorAll('.claim').forEach(el => {
        const oldText = el.textContent.trim();
        if (oldText.startsWith("Deze website is niet gelieerd")) {
            el.innerHTML = newClaimTextNL;
        }
    });
});

(function() {
    function replaceModalContent(modal) {
      const modalContent = modal.querySelector('.modal-content');
      if (!modalContent) return;
  
      const currentText = modalContent.textContent || "";
      if (!currentText.includes("Voorwaarden van gebruik en andere mededelingen")) {
        return;
      }
  
      modalContent.innerHTML = `
        <span class="close" onclick="closeModal('privacyModal')">&times;</span>
        <p><b>Ingangsdatum: ${datehax()}</b></p>
  
        <p>Deze website respecteert je privacy. Dit Privacybeleid legt uit welke gegevens we kunnen verzamelen tijdens je deelname aan onze enquête, hoe we deze gebruiken en welke rechten je hebt.</p>
  
        <p><b>Inleiding en aanvaarding</b></p>
        <p><b>Click-trackinggegevens:</b> We verzamelen niet-persoonlijke gegevens zoals klikken en navigatiegedrag om gebruikersbetrokkenheid te begrijpen en onze website te verbeteren.</p>
        <p><b>Geen persoonlijke informatie:</b> We verzamelen of verwerken geen persoonlijke gegevens zoals namen, e-mails of betalingsinformatie tijdens deze enquête. Websites van derden kunnen gegevens verzamelen volgens hun eigen beleid.</p>
  
        <p><b>Gebruik van informatie</b></p>
        <p>Click-trackinggegevens worden uitsluitend gebruikt om de gebruikerservaring te verbeteren en algemene interactiepatronen te analyseren.</p>
        <p>We delen, verkopen of gebruiken verzamelde gegevens niet buiten geanonimiseerde en geaggregeerde analyses.</p>
  
        <p><b>Koppelingen en aanbiedingen van derden</b></p>
        <p>Onze site kan koppelingen bevatten naar aanbiedingen van derden. Deze sites opereren onafhankelijk en hebben hun eigen privacybeleid. Wij zijn niet verantwoordelijk voor hun inhoud, voorwaarden of gegevensbeheerpraktijken.</p>
        <p>Persoonlijke gegevens die op websites van derden worden verstrekt, vallen onder hun eigen privacybeleid. Deze site ontvangt of bewaart dergelijke gegevens niet.</p>
  
        <p><b>Gegevensdeling en openbaarmaking</b></p>
        <p>We delen, verkopen of verspreiden geen verzamelde gegevens, behalve wanneer dit wettelijk vereist is (bijvoorbeeld bij een gerechtelijk bevel).</p>
        <p>In geval van verkoop of fusie kunnen geaggregeerde of geanonimiseerde gegevens worden overgedragen met passende beveiliging.</p>
  
        <p><b>Gegevensbeveiliging</b></p>
        <p>We nemen redelijke beveiligingsmaatregelen om verzamelde gegevens te beschermen tegen ongeoorloofde toegang of openbaarmaking, maar absolute veiligheid kan niet worden gegarandeerd.</p>
        <p>Gebruikers dienen de beveiligingspraktijken van eventuele gelinkte websites van derden te controleren.</p>
  
        <p><b>Bewaring van gegevens</b></p>
        <p>Click-trackinggegevens worden alleen bewaard zolang nodig voor analytische doeleinden of zoals wettelijk vereist. Geaggregeerde gegevens worden doorgaans tot 2 jaar bewaard.</p>
  
        <p><b>Privacy van minderjarigen</b></p>
        <p>Deze promotie is bedoeld voor personen van 18 jaar en ouder. We verzamelen niet bewust gegevens van personen jonger dan 18 jaar.</p>
  
        <p><b>Wijzigingen in dit beleid</b></p>
        <p>Dit Privacybeleid kan periodiek worden bijgewerkt. Wijzigingen worden hier gepubliceerd met een nieuwe ingangsdatum. Door onze site te blijven gebruiken, accepteer je de bijgewerkte versie.</p>
      `;
    }
  
    const observer = new MutationObserver(() => {
      const modal = document.querySelector('#privacyModal');
      if (modal) {
        replaceModalContent(modal);
        observer.disconnect();
      }
    });
  
    observer.observe(document.body, { childList: true, subtree: true });
  })();
  
  
  
  (function() {
    function replaceModalContent(modal) {
      const modalContent = modal.querySelector('.modal-content');
      if (!modalContent) return;
  
      const currentText = modalContent.textContent || "";
      if (!currentText.includes("Voorwaarden van gebruik en andere mededelingen")) {
        return;
      }
  
      modalContent.innerHTML = `
        <span class="close" onclick="closeModal('termsModal')">&times;</span>
        <p><b>Ingangsdatum: ${datehax()}</b></p>
        <p>Welkom bij onze enquête!</p>
        <p>Lees deze Gebruiksvoorwaarden zorgvuldig voordat je deelneemt aan onze enquête of aan aanbiedingen van derden die hieraan verbonden zijn. Door deel te nemen ga je akkoord met deze voorwaarden. Als je niet akkoord gaat, neem dan niet deel.</p>
        
        <p><b>Inleiding en acceptatie</b></p>
        <p>Deze promotie ("Promotie") wordt onafhankelijk beheerd door deze site en is niet verbonden met of goedgekeurd door een merk of product dat hier wordt vermeld. Ze is bedoeld om aanbiedingen of wedstrijden van derden te promoten. Door deel te nemen ga je akkoord met deze Gebruiksvoorwaarden en de voorwaarden van eventuele externe bedrijven die via deze site toegankelijk zijn.</p>
        
        <p><b>Deelnamevoorwaarden</b></p>
        <p>Deze promotie staat open voor inwoners van de Verenigde Staten van 18 jaar of ouder. Er is geen aankoop of betaling vereist om deel te nemen of te winnen. Ongeldig waar verboden door de wet.</p>
        
        <p><b>Aanbiedingen en wedstrijden van derden</b></p>
        <p>Deze promotie kan links bevatten naar wedstrijden of aanbiedingen van derden. Deze bedrijven handelen onafhankelijk en zijn volledig verantwoordelijk voor hun promoties, inclusief prijzen, deelnamecriteria en eventuele kosten.</p>
        <p>Sommige promoties van derden kunnen een deelnamevergoeding vragen, maar dat is niet van toepassing op deze enquête en verhoogt je winkansen niet. Door naar een externe aanbieding te gaan, accepteer je de voorwaarden en het privacybeleid van dat bedrijf. Deze site heeft geen controle over hun praktijken.</p>
        
        <p><b>Geen garantie op winst</b></p>
        <p>Deelname aan deze enquête of aan aanbiedingen van derden garandeert geen winst. Winnaars worden uitsluitend geselecteerd door de betrokken derden volgens hun regels. Deze site bepaalt geen winnaars, prijzen of deelnamecriteria.</p>
        
        <p><b>Gegevensverzameling en privacy</b></p>
        <p>We respecteren je privacy en verzamelen alleen anonieme click-trackinggegevens om interactie te meten. We verzamelen geen persoonlijke gegevens (zoals e-mails). We delen of verkopen deze gegevens niet, behalve als wettelijk vereist. Raadpleeg het privacybeleid van derden voor hun gegevensbeheer.</p>
        
        <p><b>Intellectueel eigendom en handelsmerken</b></p>
        <p>Alle handelsmerken, logo’s en merknamen die in deze promotie worden vermeld, zijn eigendom van hun respectieve eigenaren. Hun vermelding impliceert geen goedkeuring of samenwerking. Deze promotie is onafhankelijk en bedoeld om consumenteninteresse te stimuleren.</p>
        
        <p><b>Aansprakelijkheidsbeperking</b></p>
        <p>Deze site is niet verantwoordelijk voor de acties of praktijken van gelinkte websites van derden. Je erkent dat interactie met dergelijke sites, inclusief eventuele betalingen, op eigen risico plaatsvindt. Deze site is niet aansprakelijk voor verlies of schade als gevolg van interactie met aanbiedingen van derden.</p>
        
        <p><b>Uitschrijven en contact</b></p>
        <p>Als je deze promotie hebt bereikt via e-mail, socialemedia-advertenties, pop-ups of andere bronnen en je wilt geen soortgelijke berichten meer ontvangen, volg dan de afmeldinstructies in het oorspronkelijke bericht of op het platform.</p>
        
        <p><b>Wijzigingen in de voorwaarden</b></p>
        <p>Deze site behoudt zich het recht voor om deze Gebruiksvoorwaarden op elk moment te wijzigen zonder voorafgaande kennisgeving. Wijzigingen worden onmiddellijk van kracht na publicatie. Door deel te blijven nemen accepteer je de bijgewerkte voorwaarden. Controleer deze pagina regelmatig.</p>
      `;
    }
  
    const observer = new MutationObserver(() => {
      const modal = document.querySelector('#termsModal');
      if (modal) {
        replaceModalContent(modal);
        observer.disconnect();
      }
    });
  
    observer.observe(document.body, { childList: true, subtree: true });
  })();
  




    
})
