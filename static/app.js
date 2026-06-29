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
mensaje.addEventListener('input', () => {
  // Si el texto limpio es igual a "", 'disabled' será true.
  botonEnviar.disabled = mensaje.value.trim() === '';
});
function afegirMissatge(text, tipus) {
  // console.log("Afegir missatge");
  const node = document.createElement("div");
  node.classList.add(tipus)
  node.textContent = text;
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
  return {node: node,
    inici: performance.now()
  };
}
function finalitzarMsgStatus(status) {
  const temps = ((performance.now() - status.inici)/1000).toFixed(2);
  status.node.classList.add("msgstatusfinal");
  status.node.classList.remove("msgstatus");
  status.node.textContent = `Thought... / Pensado... / Pensat... (${temps}s.)`;
}

bloqueFormulario.addEventListener('submit', async(e) => {
  // console.log("Submit handler called"); // Add this
  e.preventDefault();
  // // console.log(mensaje.value);
  document.querySelector("#mensaje-inicial")?.remove();

  afegirMsgPrompt(mensaje.value.trim());
  const estat = crearMsgStatus();
  // el replicarem cada cop que afegim un o més missatges seguits
  bloqueCentral.scrollTop = bloqueCentral.scrollHeight;
  try {
   const resposta = await fetch("/chat", {
     method: "POST",
     headers: {
       "Content-Type": "application/json",
     },
     body: JSON.stringify({
       message: mensaje.value.trim(),
     }),
   });
   const data = await resposta.json();
   afegirMsgResponse(data.response);
   finalitzarMsgStatus(estat);
  } catch (error) {
    console.error(error);
    estat.node.classList.add("msgstatusfinal");
    estat.node.classList.remove("msgstatus");
    estat.node.textContent = `Error: ${error.message}`;
  }

  bloqueCentral.scrollTop = bloqueCentral.scrollHeight;
  mensaje.value = "";
  mensaje.style.height = "auto";
  botonEnviar.disabled = true;

  mensaje.focus();
});


// bloqueFormulario.addEventListener('submit', (e) => {
//   console.log("Submit handler called"); // Add this
//   e.preventDefault();
//   // console.log(mensaje.value);
//   if (bloqueCentral.textContent === textDeProva) {
//     bloqueCentral.textContent = mensajeEnvido + mensaje.value;
//   // } else {
//   //   bloqueCentral.textContent += "<br><br>" + mensajeEnvido + mensaje.value;
//   // }
//   } else {
//     bloqueCentral.innerHTML += "<br><br>" + mensajeEnvido + mensaje.value;
//   }
//   bloqueCentral.scrollTop = bloqueCentral.scrollHeight;
//   mensaje.value = "";
//   mensaje.style.height = "auto";
//   botonEnviar.disabled = true;
//   mensaje.focus();
// });

//ca: per capturar l'idioma
async function reclamaIdioma(quinIdioma) {
  // console.log("Idioma seleccionat: " + quinIdioma);
  // ca: fem una petició POST per actualitzar l'idioma
  const response = await fetch("/posa_idioma", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({language: quinIdioma}),
  });
 const nou_idioma = await response.json();
 // console.log(nou_idioma);
 canvia_idioma(quinIdioma, nou_idioma);
}

// idiomaSelect.addEventListener('change', async () => {
//   console.log("Idioma seleccionat: " + idiomaSelect.value);
//   // ca: fem una petició POST per actualitzar l'idioma
//   const response = await fetch("/posa_idioma", {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/json",
//     },
//     body: JSON.stringify({language: idiomaSelect.value}),
//   });
//  const nou_idioma = await response.json();
//  console.log(nou_idioma);
//  canvia_idioma(idiomaSelect.value, nou_idioma);
// });
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
            elemento.setAttribute("placeholder",textos[cada]);
        });
        document.documentElement.lang = amb_idioma;
};

mensaje.addEventListener("input", () => {
    mensaje.style.height = "auto";
    mensaje.style.height = mensaje.scrollHeight + "px";
    botonEnviar.disabled = mensaje.value.trim() === '';

});
mensaje.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.ctrlKey) {
        e.preventDefault();
        //botonEnviar.click();
        bloqueFormulario.requestSubmit();
    }
});