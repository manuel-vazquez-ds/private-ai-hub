// const textDeProva = "Text de prova<br>".repeat(100);
// ja hem fet les proves del scroll
const textDeProva = "...esperant un missatge";
const mensajeEnvido = "<div style='padding: 5px 0px;'><b>Missatge enviat:</b><br></div>";
let bloqueCentral = document.getElementById("bloque-central");
bloqueCentral.innerHTML = textDeProva;
const mensaje = document.getElementById("el-mensaje");
const bloqueFormulario = document.getElementById("bloque-formulario");
const botonEnviar = document.getElementById("enviar");
mensaje.addEventListener('input', () => {
  // Si el texto limpio es igual a "", 'disabled' será true.
  botonEnviar.disabled = mensaje.value.trim() === '';
});

bloqueFormulario.addEventListener('submit', (e) => {
  e.preventDefault();
  // console.log(mensaje.value);
  if (bloqueCentral.innerHTML === textDeProva) {
    bloqueCentral.innerHTML = mensajeEnvido + mensaje.value;
  } else {
    bloqueCentral.innerHTML += "<br><br>" + mensajeEnvido + mensaje.value;
  }
  bloqueCentral.scrollTop = bloqueCentral.scrollHeight;
  mensaje.value = "";
  mensaje.focus();
});
