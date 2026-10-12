// const formats = {txt: "Text", md: "Markdown"};
const formats = {txt: {nom:"Text", fitxer: "des_TXT02_MVM.svg"}, md: {nom:"Markdown", fitxer: "des_MD02_MVM.svg"}};

// function downloadFile(filename, content) {
//     const blob = new Blob([content], { type: 'text/plain' });
//     const url = URL.createObjectURL(blob);
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = filename;
//     document.body.appendChild(a);
//     a.click();
//     document.body.removeChild(a);
//     URL.revokeObjectURL(url);
// }

// export function crearOpcionsDescarrega(id_missatge) {
export function crearOpcionsDescarrega(id_missatge, traduccions) {

    const opcionsDescarrega = document.createElement("div");
    opcionsDescarrega.classList.add("descE");
    for (const [format, dades] of Object.entries(formats)) {
        // const nodeTipusFormat = document.createElement("div");
        // nodeTipusFormat.textContent = nom;
        const nodeTipusFormat = document.createElement("button");
        nodeTipusFormat.type = "button";
        nodeTipusFormat.classList.add("arx_desc");
                
        const icona = document.createElement("img");
        icona.classList.add("descarregables");
        icona.src = `/static/${dades.fitxer}`;
        // icona.alt = dades.nom;
        icona.alt = traduccions[format];
        nodeTipusFormat.appendChild(icona);

        nodeTipusFormat.dataset.format = format;
        nodeTipusFormat.dataset.id_missatge = id_missatge;
        nodeTipusFormat.dataset.tooltip = traduccions[format];
        // console.log("Tooltip:", nodeTipusFormat.dataset.tooltip);
        // console.log("Format:", nodeTipusFormat.dataset.format);
        // console.log("Traduccions:", traduccions);
        nodeTipusFormat.addEventListener("click", descarrega);
        opcionsDescarrega.appendChild(nodeTipusFormat);
    }
    return opcionsDescarrega;
}
// async function descarrega(event) {
//     const format = event.target.dataset.format;
//     const id_missatge = event.target.dataset.id_missatge;
//     const response = await fetch(`/descarregar/${id_missatge}?format=${format}`);
//     const data = await response.json();
//     const blob = new Blob([data.content], { type: 'text/plain' });
//     const url = URL.createObjectURL(blob);
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = data.filename;
//     document.body.appendChild(a);
//     a.click();
//     document.body.removeChild(a);
//     URL.revokeObjectURL(url);
// }

function descarrega(event) {
    const elemento = event.currentTarget;
    // no fa falta contenidor el parametre vindra amb event
    //const contenedor = elemento.closest(".message-downloads");

    const id_missatge = elemento.dataset.id_missatge;
    const format = elemento.dataset.format;

    // ES TOT AIXÒ, PERÒ DE MOMENT HO BLOQUEJO I FAIG UN CONSOLE.LOG()
    window.location.href =
        `/missatge/${id_missatge}/descarregar?format=${format}`;
    console.log("Descarregant missatge", id_missatge, "en format", format);
}