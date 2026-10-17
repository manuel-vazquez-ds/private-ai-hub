// const textDeProva = "Text de prova<br>".repeat(100);
// ja hem fet les proves del scroll
// he canviat bloqueCentral.innerHTML per
// bloqueCentral.textContent segons chatgpt
import { crearOpcionsDescarrega } from "./descarregues.js";

const textDeProva = "...waiting a message / esperando un mensaje / esperant un missatge";
const mensajeEnvido = "<div style='padding: 5px 0px;'><b>Missatge enviat:</b><br></div>";
const bloqueCentral = document.getElementById("bloque-central");
// canviem aquestes 2 linies ja que el construim directament
// let bloqueCentral = document.getElementById("bloque-central");
//bloqueCentral.textContent = textDeProva;
const mensaje = document.getElementById("el-mensaje");
const bloqueFormulario = document.getElementById("bloque-formulario");
const botonEnviar = document.getElementById("enviar");
const idiomaSelect = document.getElementById("idioma");
const perfilSelect = document.getElementById("perfil");
const botons = document.getElementById("botons");
const btnNouXat = document.getElementById("btnNouXat");
let currentConversationId = null;
let enviant = false;
let traduccions = {};

const desplegable = document.getElementById("descarregar");
// const toggle = desplegable.querySelector(".desplegable-toggle");
// const toggle = desplegable.querySelector(".desplegable-header");


// toggle.addEventListener("click", () => {
//     desplegable.classList.toggle("open");
// });

function actualitzaEstatDescarrega() {
  const dropdown = document.getElementById("descarregar");

  dropdown.classList.toggle("disabled", !Number.isInteger(currentConversationId));
  const nouXat = document.getElementById("nouXat")
  nouXat.classList.toggle("disabled", !Number.isInteger(currentConversationId));
}

desplegable.querySelectorAll("[data-format]").forEach(opcion => {
  opcion.addEventListener("click", () => {
    const format = opcion.dataset.format;

    // descargar conversación
    window.location.href = `/conversacio/${currentConversationId}/descarregar?format=${format}`;
    // console.log(format);

    // desplegable.classList.remove("open");
  });
});

btnNouXat.addEventListener('click', () => {
  if (btnNouXat.parentElement.classList.contains('disabled')) {
    // console.log('Nou xat: botó deshabilitat');
    return;
  }

  // console.log('Nou xat: botó habilitat, executar acció');
  reiniciaXat();
});
// desplegable.hidden = !currentConversationId;

// ca: a l'haver passat a mòdul app.js, ara, les variables no es veuen fora.
window.enviant = enviant

mensaje.addEventListener('input', () => {
  // Si el texto limpio es igual a "", 'disabled' será true.
  botonEnviar.disabled = mensaje.value.trim() === '';
});
// function afegirMissatge(text, tipus) {
function afegirMissatge(text, tipus, id_missatge = null) {
  // console.log("Afegir missatge");
  // console.log("afegirMissatge", id_missatge);
  const node = document.createElement("div");
  node.classList.add(tipus);
  if (tipus !== "msgresponse") {
    // ca: TODO ESTIC AQUÍ HEM D'ESBORRAR EL textcontent i fer append()
    //node.textContent = text;
    node.append(text.text);
    if (text.arxius.length > 0) {
      const arxiusE = document.createElement("div");
      arxiusE.classList.add("arxiusE");
      node.append(arxiusE);
      text.arxius.forEach(arxiu => {
        const el_arxiu = arch_atribs(arxiu, false);
        const nodo = document.createElement("div");
        nodo.classList.add("cada_arx");
        nodo.style.borderColor = "black";
        nodo.innerHTML = el_arxiu;
        arxiusE.append(nodo);
      });

    }
  } else {
    const html = DOMPurify.sanitize(
      marked.parse(text));
    node.innerHTML = html;
    renderMathInElement(node, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false },
        { left: "\\(", right: "\\)", display: false },
        { left: "\\[", right: "\\]", display: true }
      ], throwOnError: false
    });
    // const opcionsDescarrega = crearOpcionsDescarrega(id_missatge);
    // console.log("Traduccions_1:", traduccions);
    const opcionsDescarrega = crearOpcionsDescarrega(id_missatge, traduccions);
    node.append(opcionsDescarrega);
  }
  bloqueCentral.appendChild(node);
  return node;
}
function afegirMsgPrompt(text) {
  return afegirMissatge(text, "msgprompt");
}
// function afegirMsgResponse(text) {
function afegirMsgResponse({ text, id_missatge = null }) {
  // console.log("afegirMsgResponse", id_missatge);
  return afegirMissatge(text, "msgresponse", id_missatge);
}
// function crearMsgStatus() {
//   const node = document.createElement("div");
//   node.classList.add("msgstatus");
//   node.textContent = "Thinking... / Pensando... / Pensant...";
//   bloqueCentral.appendChild(node);
//   return {
//     node: node,
//     inici: performance.now()
//   };
// }
// function finalitzarMsgStatus(status) {
//   const temps = ((performance.now() - status.inici) / 1000).toFixed(2);
//   status.node.classList.add("msgstatusfinal");
//   status.node.classList.remove("msgstatus");
//   status.node.textContent = `Thought... / Pensado... / Pensat... (${temps}s.)`;
// }

function crearMsgStatus() {
  const node = document.createElement("div");
  node.classList.add("msgstatus");
  bloqueCentral.appendChild(node);

  const inici = performance.now();

  const actualizar = () => {
    const temps = Math.floor((performance.now() - inici) / 1000);
    node.textContent = `Thinking... / Pensando... / Pensant... (${temps}s.)`;
  };

  actualizar();

  const interval = setInterval(actualizar, 1000);

  return {
    node: node,
    inici: inici,
    interval: interval
  };
}


// function finalitzarMsgStatus(status) {
//   clearInterval(status.interval);

//   const temps = ((performance.now() - status.inici) / 1000).toFixed(2);

//   status.node.classList.add("msgstatusfinal");
//   status.node.classList.remove("msgstatus");
//   status.node.textContent = `Thought... / Pensado... / Pensat... (${temps}s.)`;
// }

function finalitzarMsgStatus(status, error = null) {
  clearInterval(status.interval);

  const temps = ((performance.now() - status.inici) / 1000).toFixed(2);

  status.node.classList.add("msgstatusfinal");
  status.node.classList.remove("msgstatus");

  if (error) {
    // status.node.textContent = `Error: ${error.message}`;
    status.node.textContent = `Error: ${error.message} (${temps}s.)`;
  } else {
    status.node.textContent =
      `Thought... / Pensado... / Pensat... (${temps}s.)`;
  }
}


bloqueFormulario.addEventListener('submit', async (e) => {
  // console.log("Submit handler called"); // Add this
  e.preventDefault();
  if (enviant) return;
  enviant = true;
  window.enviant = true;
  // ca: per treure el focus del textarea quan s'envia el formulari
  document.activeElement.blur();
  canvia_form_estat();
  // console.log(mensaje.value);
  document.querySelector("#mensaje-inicial")?.remove();

  // ca: canviem aquesta dinàmica per afegir arxius
  // afegirMsgPrompt(mensaje.value.trim());

  const arxiusE = [];
  llista_arxius.forEach(arxiu => {
    arxiusE.push(arxiu.file.name);
  });
  afegirMsgPrompt({ text: mensaje.value.trim(), arxius: arxiusE });


  const estat = crearMsgStatus();
  // el replicarem cada cop que afegim un o més missatges seguits
  bloqueCentral.scrollTop = bloqueCentral.scrollHeight;

  botons.disabled = true;

  try {
    const formData = new FormData();
    llista_arxius.forEach(arxiu => {
      formData.append("arxius", arxiu.file);
    });
    // ca: provem això sinò farem un JSON stringify
    formData.append("message", mensaje.value.trim());
    if (currentConversationId)
      formData.append("conversacio_id", currentConversationId);

    formData.append("perfil_id", perfilSelect.value);
    const resposta = await fetch("/chat", {
      method: "POST",
      // ca: no necessitem headers, ja es genera automàticament
      // headers: {
      //   "Content-Type": "application/json",
      // },
      body: formData
    });
    const data = await resposta.json();
    if (!resposta.ok) {
      throw new Error(data.detail);
    }
    currentConversationId = data.conversacio_id;
    const currentMissatge_id = data.missatge_id;
    //afegirMsgResponse( data.response);
    afegirMsgResponse({ text: data.response, id_missatge: currentMissatge_id });
    // afegirMsgResponse(text= data.response, id_missatge = currentMissatge_id);
    finalitzarMsgStatus(estat);
    perfilSelect.disabled = true;
    // ca: fem visible descarregar
    // const dsc = document.getElementById("descarregar");
    // dsc.style.visibility = "visible";

    // ca: trec el desplegable perque ara estarà visible i dehabilitada la capcelerea
    // desplegable.style.display = "inline-block";


  } catch (error) {
    console.error(error);
    // estat.node.classList.add("msgstatusfinal");
    // estat.node.classList.remove("msgstatus");
    // estat.node.textContent = `Error: ${error.message}`;
    finalitzarMsgStatus(estat, error);
  } finally {
    bloqueCentral.scrollTop = bloqueCentral.scrollHeight;
    mensaje.value = "";
    mensaje.style.height = "auto";
    // llista_arxius.length = 0;
    neteja_arxius();
    botonEnviar.disabled = true;
    botons.disabled = false;
    enviant = false;
    window.enviant = false;
    canvia_form_estat();

    actualitzaEstatDescarrega();

    mensaje.focus();
  }
});
function canvia_form_estat() {
  // TODO: implement this function
  if (enviant) {
    bloqueFormulario.classList.add("bloc_espera");
    // console.log("Enviant:")
  } else {
    bloqueFormulario.classList.remove("bloc_espera");
  }
}


//ca: per capturar l'idioma
async function reclamaIdioma(quinIdioma) {
  // console.log("Idioma seleccionat: " + quinIdioma);
  // ca: fem una petició POST per actualitzar l'idioma
  const response = await fetch("/posa_idioma", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ language: quinIdioma }),
  });
  const nou_idioma = await response.json();
  // console.log(nou_idioma);
  traduccions = nou_idioma;
  // console.log("Traduccions_0:", traduccions);
  canvia_idioma(quinIdioma, nou_idioma);
}

idiomaSelect.addEventListener('change', async (elEvent) => {
  // console.log("Idioma seleccionat: " + elEvent.target.value);
  await reclamaIdioma(elEvent.target.value);
});

function canvia_idioma(amb_idioma, textos) {
  // ca: canviar els textos segons l'idioma
  // console.log("Canviant idioma a: " + amb_idioma);
  // console.log("textos: " + JSON.stringify(textos));
  document.querySelectorAll('[idio]').forEach(elemento => {
    // console.log(elemento.getAttribute('idio'));
    const cada = elemento.getAttribute('idio');
    elemento.textContent = textos[cada];
  });

  document.querySelectorAll('[idio-place]').forEach(elemento => {
    // console.log(elemento.getAttribute('idio-place'));
    const cada = elemento.getAttribute('idio-place');
    elemento.setAttribute("placeholder", textos[cada]);
  });
  document.querySelectorAll('[idio-tool]').forEach(elemento => {
    // console.log(elemento.getAttribute('idio-tool'));
    const cada = elemento.getAttribute('idio-tool');
    elemento.setAttribute("data-tooltip", textos[cada]);
    const imatge = elemento.querySelector('img');
    imatge.setAttribute('alt', textos[cada]);
    // imatge.alt = textos[cada];
  });
  document.querySelectorAll('[data-format]').forEach(elemento => {
    // console.log(elemento.getAttribute('idio-tool'));
    const cada = elemento.getAttribute('data-format');
    elemento.setAttribute("data-tooltip", textos[cada]);
    const imatge = elemento.querySelector('img');
    imatge.setAttribute('alt', textos[cada]);
  });

  document.documentElement.lang = amb_idioma;
  // ca: canviar els textos de les alertes
  alertes.mida = textos.mida;
  alertes.inclos = textos.inclos;
};

mensaje.addEventListener("input", () => {
  mensaje.style.height = "auto";
  mensaje.style.height = mensaje.scrollHeight + "px";
  botonEnviar.disabled = mensaje.value.trim() === '';

});
mensaje.addEventListener("keydown", (e) => {
  if (enviant) return;
  if (e.key === "Enter" && e.ctrlKey) {
    e.preventDefault();
    //botonEnviar.click();
    bloqueFormulario.requestSubmit();
  }
});
function reiniciaXat() {

  const bloqueCentral = document.getElementById("bloque-central");

  // ca: Esborra de golpe tot el contingut (missatges afegits)
  bloqueCentral.innerHTML = "";

  // ca: Torna a crear el missatge inicial
  const mensajeInicial = document.createElement("div");
  mensajeInicial.id = "mensaje-inicial";
  mensajeInicial.style.fontStyle = "italic";
  mensajeInicial.textContent = "...waiting a message / esperando un mensaje / esperant un missatge";

  bloqueCentral.appendChild(mensajeInicial);

  // ca: reiniciar el perfil select
  // perfilSelect.value = "";
  // ca: canviar el perfil a la primera opció del select
  perfilSelect.selectedIndex = 0;
  perfilSelect.disabled = false;
  
  // ca: reiniciar el botó d'enviar
  botonEnviar.disabled = true;
  
  // ca: reiniciar el textarea
  mensaje.value = "";
  mensaje.style.height = "auto";
  
  // ca: reiniciar la variable de control
  neteja_arxius();
  botonEnviar.disabled = true;
  botons.disabled = false;

  enviant = false;
  window.enviant = false;

  // ca: reiniciar l'ID de la conversa
  currentConversationId = null;
  
  // ca: actualitzar l'estat del formulari
  canvia_form_estat();
  
  // ca: actualitzar l'estat de la descàrrega
  actualitzaEstatDescarrega();
  
  // ca: enfocar el textarea
  mensaje.focus();
}