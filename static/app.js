// const textDeProva = "Text de prova<br>".repeat(100);
// ja hem fet les proves del scroll
// he canviat bloqueCentral.innerHTML per
// bloqueCentral.textContent segons chatgpt
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
let currentConversationId = null;
let enviant = false;

mensaje.addEventListener('input', () => {
  // Si el texto limpio es igual a "", 'disabled' será true.
  botonEnviar.disabled = mensaje.value.trim() === '';
});
function afegirMissatge(text, tipus) {
  // console.log("Afegir missatge");
  const node = document.createElement("div");
  node.classList.add(tipus);
  if (tipus !== "msgresponse") {
    // ca: TODO ESTIC AQUÍ HEM D'ESBORRAR EL textcontent i fer append()
    //node.textContent = text;
    node.append(text.text);
    if (text.arxius.length >0) {
      const arxiusE = document.createElement("div");
      arxiusE.classList.add("arxiusE");
      node.append(arxiusE);
      text.arxius.forEach(arxiu => {
        const el_arxiu = arch_atribs(arxiu, false);
        const nodo = document.createElement("div");
        nodo.classList.add("cada_arx");
        nodo.style.borderColor = "black";
        nodo.innerHTML=el_arxiu;
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
  }
  bloqueCentral.appendChild(node);
  return node;
}
function afegirMsgPrompt(text) {
  return afegirMissatge(text, "msgprompt");
}
function afegirMsgResponse(text) {
  return afegirMissatge(text, "msgresponse");
}
function crearMsgStatus() {
  const node = document.createElement("div");
  node.classList.add("msgstatus");
  node.textContent = "Thinking... / Pensando... / Pensant...";
  bloqueCentral.appendChild(node);
  return {
    node: node,
    inici: performance.now()
  };
}
function finalitzarMsgStatus(status) {
  const temps = ((performance.now() - status.inici) / 1000).toFixed(2);
  status.node.classList.add("msgstatusfinal");
  status.node.classList.remove("msgstatus");
  status.node.textContent = `Thought... / Pensado... / Pensat... (${temps}s.)`;
}

bloqueFormulario.addEventListener('submit', async (e) => {
  // console.log("Submit handler called"); // Add this
  e.preventDefault();
  if (enviant) return;
  enviant = true;
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
  afegirMsgPrompt({text: mensaje.value.trim(), arxius: arxiusE});


  const estat = crearMsgStatus();
  // el replicarem cada cop que afegim un o més missatges seguits
  bloqueCentral.scrollTop = bloqueCentral.scrollHeight;

  botons.disabled = true;

  // try {
  //   const resposta = await fetch("/chat", {
  //     method: "POST",
  //     headers: {
  //       "Content-Type": "application/json",
  //     },
  //     body: JSON.stringify({
  //       message: mensaje.value.trim(),
  //       conversacio_id: currentConversationId,
  //       perfil_id: perfilSelect.value
  //     }),
  //   });
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
    afegirMsgResponse(data.response);
    finalitzarMsgStatus(estat);
    perfilSelect.disabled = true;
  } catch (error) {
    console.error(error);
    estat.node.classList.add("msgstatusfinal");
    estat.node.classList.remove("msgstatus");
    estat.node.textContent = `Error: ${error.message}`;
  } finally {
    bloqueCentral.scrollTop = bloqueCentral.scrollHeight;
    mensaje.value = "";
    mensaje.style.height = "auto";
    // llista_arxius.length = 0;
    neteja_arxius();
    botonEnviar.disabled = true;
    botons.disabled = false;
    enviant = false;
    canvia_form_estat();

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