const pulsa = document.getElementById("afegir_arch");
const arxius = document.getElementById("arxius");

const selec_arxiu = document.createElement("input");
selec_arxiu.type = "file";
selec_arxiu.accept = ".txt,.md";


selec_arxiu.addEventListener('change', (event) => {
    const file = event.target.files[0];
    const elFitxer = file;
    // console.log(elFitxer);
    event.target.value = '';
    if (elFitxer) {
        fitxerHashat = { file: elFitxer, hash: crea_hash(elFitxer) };
        const el_arxiu = afegeix_arxiu(fitxerHashat, true);
        if (el_arxiu) {
            arxius.append(el_arxiu);
            // console.log(llista_arxius);
        }
    }
});

const col_ext = { txt: "#A9A9A9", md: "#1E90FF", pdf: "#FF0000", csv: "#228b22a9", xls: "#228B22" }
// const alertes = { mida: "Mida d'arxius sobrepassa el permés", inclos: "Document ja inclòs" }
const mida_max = 1024 * 1024; // 1 MB
// const mida_max = 4096; // 4 KB

const llista_arxius = [];

pulsa.addEventListener('click', () => {
    if (enviant) return;
    selec_arxiu.click();
})

arxius.addEventListener('click', (e) => {
    if (enviant) return;
    if (e.target.matches('.esborra')) {
        for (let i = 0; i < llista_arxius.length; i++) {
            if (llista_arxius[i].hash === e.target.parentElement.getAttribute("data-hash")) {
                llista_arxius.splice(i, 1);
                break;
            }
        }
        e.target.parentElement.remove();
    }
})

function afegeix_arxiu(fitxer, provisional) {
    if (hash_existent(fitxer.hash)) {
        alert(alertes.inclos);
        return;
    }
    if (mida_maxima(fitxer)) {
        alert(alertes.mida);
        return;
    }
    let ext3 = fitxer.file.name.split('.').pop().toLowerCase();
    // console.log(ext3);
    const bgcolor = col_ext[ext3] ? col_ext[ext3] : col_ext.txt;
    const el_arxiu = `<div class="arx_tipus" style="background-color:${bgcolor}">${ext3}</div>
                <div class="arx_nom">${fitxer.file.name}</div>
                ${provisional ? `<div class="esborra">&#9587</div>` : ``}`;
    const nodo = document.createElement("div");
    nodo.classList.add("cada_arx")
    nodo.setAttribute("data-hash", fitxer.hash);
    nodo.innerHTML = el_arxiu;
    llista_arxius.push(fitxer);
    return nodo;

}
function crea_hash(fitxer) {
    const metadata = `${fitxer.name}-${fitxer.size}-${fitxer.lastModified}-${fitxer.type}`;
    // ca: Creem un hash ràpid (djb2)
    let hash = 5381;
    for (let i = 0; i < metadata.length; i++) {
        hash = (hash * 33) ^ metadata.charCodeAt(i);
    }
    return (hash >>> 0).toString(16);
}
function hash_existent(hash) {
    for (let i = 0; i < llista_arxius.length; i++) {
        if (llista_arxius[i].hash === hash) {
            return true;
        }
    }
    return false;
}
function mida_maxima(nou_fitxer) {
    const mida_amb_nou = nou_fitxer.file.size + llista_arxius.reduce((total, arxiu) => total + arxiu.file.size, 0);
    // console.log(mida_amb_nou);
    return mida_amb_nou > mida_max;
}
function arch_atribs(fitxer,provisional) {
    // let ext3 = fitxer.file.name.split('.').pop().toLowerCase();
    let ext3 = fitxer.split('.').pop().toLowerCase();
    const bgcolor = col_ext[ext3] ? col_ext[ext3] : col_ext.txt;
//    const fgcolor = prmpt ? "; color: black" : "";
    const el_arxiu = `<div class="arx_tipus" style="background-color:${bgcolor}">${ext3}</div>
                <div class="arx_nom">${fitxer}</div>
                ${provisional ? `<div class="esborra">&#9587</div>` : ``}`;
    return el_arxiu;
}
function neteja_arxius() {
    llista_arxius.length = 0;
    arxius.textContent = "";
}